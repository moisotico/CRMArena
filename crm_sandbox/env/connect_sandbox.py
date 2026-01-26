from simple_salesforce import Salesforce
from simple_salesforce.exceptions import SalesforceAuthenticationFailed
import ast
import os, re, pandas as pd
import time
import logging
import threading
from tqdm import tqdm
from typing import Dict, List, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

DATA_DIR = "../data"
CURRENT_SCHEMA_FILE = f"{DATA_DIR}/current_schema.json"
FULL_SCHEMA_FILE = f"{DATA_DIR}/training_org_non_null_full_schema.json"
METADATA_FILE = f"{DATA_DIR}/training_org_full_object_metadata_superset.jsonl"

# Retry configuration
MAX_AUTH_RETRIES = 3
INITIAL_RETRY_DELAY = 2  # seconds
MAX_RETRY_DELAY = 10  # seconds

# Connection pool for reusing authenticated sessions
_connection_pool: Dict[str, Salesforce] = {}
_pool_lock = threading.Lock()


def get_cached_connection(org_type: str, auth: Dict) -> Optional[Salesforce]:
    """Get a cached Salesforce connection if available and valid."""
    with _pool_lock:
        if org_type in _connection_pool:
            sf = _connection_pool[org_type]
            # Test if connection is still valid with a lightweight call
            try:
                sf.limits()  # Quick API call to verify session
                logger.debug(f"Reusing cached Salesforce connection for {org_type}")
                return sf
            except Exception as e:
                logger.info(f"Cached connection for {org_type} expired: {e}. Will re-auth.")
                del _connection_pool[org_type]
        return None


def cache_connection(org_type: str, sf: Salesforce) -> None:
    """Cache a Salesforce connection for reuse."""
    with _pool_lock:
        _connection_pool[org_type] = sf
        logger.info(f"Cached Salesforce connection for {org_type} (session_id: {sf.session_id[:20]}...)")


def invalidate_connection(org_type: str) -> None:
    """Remove a cached connection (e.g., after auth failure)."""
    with _pool_lock:
        if org_type in _connection_pool:
            del _connection_pool[org_type]
            logger.info(f"Invalidated cached connection for {org_type}")


class SalesforceConnector:
    def __init__(self, auth=None, schema_file=FULL_SCHEMA_FILE, org_type="b2b"):

        assert org_type in ["b2b", "b2c", "original"], "Invalid organization type"
        if not auth:
            auth = self.sf_auth(org_type)

        self.auth = auth
        self.org_type = org_type

        # Try to reuse cached connection first
        cached = get_cached_connection(org_type, auth)
        if cached:
            self.sf = cached
        else:
            self.sf = self._connect_with_retry(auth)
            cache_connection(org_type, self.sf)

    def _connect_with_retry(self, auth: Dict) -> Salesforce:
        """Attempt to connect to Salesforce with retry logic for transient failures."""
        last_error = None
        delay = INITIAL_RETRY_DELAY

        for attempt in range(1, MAX_AUTH_RETRIES + 1):
            try:
                if auth.get("username"):
                    sf = Salesforce(
                        username=auth["username"],
                        password=auth["password"],
                        security_token=auth["security_token"]
                    )
                else:
                    sf = Salesforce(
                        instance_url=auth["instance_url"],
                        session_id=auth["session_id"]
                    )

                if attempt > 1:
                    logger.info(f"Salesforce connection succeeded on attempt {attempt}")
                return sf

            except SalesforceAuthenticationFailed as e:
                last_error = e
                error_msg = str(e)

                # Check if it's a lockout vs bad credentials
                if "INVALID_LOGIN" in error_msg:
                    if "locked out" in error_msg.lower():
                        logger.warning(f"Salesforce account locked out (attempt {attempt}/{MAX_AUTH_RETRIES}). Waiting {delay}s before retry...")
                    else:
                        logger.warning(f"Salesforce auth failed (attempt {attempt}/{MAX_AUTH_RETRIES}): {error_msg[:100]}. Retrying in {delay}s...")
                else:
                    logger.warning(f"Salesforce connection error (attempt {attempt}/{MAX_AUTH_RETRIES}): {error_msg[:100]}. Retrying in {delay}s...")

                if attempt < MAX_AUTH_RETRIES:
                    time.sleep(delay)
                    delay = min(delay * 2, MAX_RETRY_DELAY)  # Exponential backoff with cap

            except Exception as e:
                last_error = e
                logger.warning(f"Unexpected Salesforce error (attempt {attempt}/{MAX_AUTH_RETRIES}): {e}. Retrying in {delay}s...")

                if attempt < MAX_AUTH_RETRIES:
                    time.sleep(delay)
                    delay = min(delay * 2, MAX_RETRY_DELAY)

        # All retries exhausted
        logger.error(f"Salesforce connection failed after {MAX_AUTH_RETRIES} attempts. Last error: {last_error}")
        raise last_error

    def reconnect(self) -> bool:
        """Attempt to reconnect to Salesforce. Returns True on success."""
        try:
            logger.info("Attempting Salesforce reconnection...")
            # Invalidate cached connection before reconnecting
            invalidate_connection(self.org_type)
            self.sf = self._connect_with_retry(self.auth)
            # Cache the new connection
            cache_connection(self.org_type, self.sf)
            logger.info("Salesforce reconnection successful")
            return True
        except Exception as e:
            logger.error(f"Salesforce reconnection failed: {e}")
            return False
        
    def preprocess_query(self, query: str) -> str:
        # remove tags if present
        pattern1 = r'```(?:sql|SQL|soql|SOQL)?([\S\s]+?)```'
        pattern2 = r'```([\S\s]+?)```'
        matches = re.findall(pattern1, query, re.DOTALL) + re.findall(pattern2, query, re.DOTALL)
        if len(matches) > 0:
            query = " ".join(matches[0].split())
            
        return query

    def _result_to_list(self, result_df: pd.DataFrame, field: str = "Name") -> List[str]:
        return result_df[field].tolist()
        
    def run_query(self, query, return_df: bool = False):
        is_sosl = False
        if query.startswith("FIND"):
            is_sosl = True

        # Retry logic for session expiration
        for attempt in range(1, MAX_AUTH_RETRIES + 1):
            try:
                if not is_sosl:
                    processed_query = self.preprocess_query(query)
                    result = self.sf.query_all(processed_query)
                else:
                    result = self.sf.search(query)
                break  # Success, exit retry loop

            except Exception as e:
                error_str = str(e)

                # Check if this is a session/auth error that warrants reconnection
                is_session_error = any(err in error_str.upper() for err in [
                    "INVALID_SESSION", "SESSION_EXPIRED", "INVALID_LOGIN",
                    "AUTHENTICATION", "UNAUTHORIZED"
                ])

                if is_session_error and attempt < MAX_AUTH_RETRIES:
                    logger.warning(f"Salesforce session error on query (attempt {attempt}/{MAX_AUTH_RETRIES}): {error_str[:100]}")
                    if self.reconnect():
                        logger.info("Reconnected successfully, retrying query...")
                        continue
                    else:
                        logger.error("Reconnection failed, cannot retry query")

                # Parse the error for non-retriable cases or after all retries exhausted
                try:
                    parsed_err = ast.literal_eval(error_str.split("Response content:")[1].strip())[0]
                    err = f"{parsed_err['errorCode']}: {parsed_err['message']}"
                except Exception:
                    err = f"Query error: {error_str[:200]}"
                return err, 0
        
        if not is_sosl:
            result_data = result["records"]
        else:
            result_data = result["searchRecords"]
        if len(result_data) == 0:
            return [], 1
        keys = result_data[0].keys()

        for row in result_data:
            if "attributes" in row:
                del row["attributes"]

        all_none_keys = [key for key in keys if all([record[key] is None for record in result_data])]
        new_data = [{k: v for k, v in record.items() if k not in all_none_keys} for record in result_data]
        if return_df:
            return pd.DataFrame(new_data), 1
        return new_data, 1
    
    
    @staticmethod
    def sf_auth(org_type: str):
        auth = dict()
        print(f"Using {org_type} Salesforce credentials")
        if org_type == "b2b":
            if "SALESFORCE_B2B_SECURITY_TOKEN" in os.environ:
             
                auth = {
                    "username" : os.environ["SALESFORCE_B2B_USERNAME"],
                    "password" : os.environ["SALESFORCE_B2B_PASSWORD"],
                    "security_token" : os.environ["SALESFORCE_B2B_SECURITY_TOKEN"]
                }
                return auth
        elif org_type == "b2c":
            if "SALESFORCE_B2C_SECURITY_TOKEN" in os.environ:
                auth = {
                    "username" : os.environ["SALESFORCE_B2C_USERNAME"],
                    "password" : os.environ["SALESFORCE_B2C_PASSWORD"],
                    "security_token" : os.environ["SALESFORCE_B2C_SECURITY_TOKEN"]
                }
                return auth
        elif org_type == "original":
            print("Using original Salesforce credentials")
            if "SALESFORCE_SECURITY_TOKEN" in os.environ:
                auth = {
                    "username" : os.environ["SALESFORCE_USERNAME"],
                    "password" : os.environ["SALESFORCE_PASSWORD"],
                    "security_token" : os.environ["SALESFORCE_SECURITY_TOKEN"]
                }
                return auth
        raise ValueError("No Salesforce credentials found in environment variables!")
    
if __name__ == "__main__":
    load_dotenv()
    sf = SalesforceConnector()
    q = """
        SELECT Id, Subject, Status, Priority, Description
        FROM Case
        WHERE Account.Name = 'Acme' AND (Owner.FirstName = 'Edward' OR Owner.LastName = 'Edward')
    """
    op, s = sf.run_query(q)
    if s == 0:
        err = ast.literal_eval(op.split("Response content:")[1].strip())[0]
        print(f"Error: {err['errorCode']} - {err['message']}")
    else:
        print("Query results:")
        print(op)
        print(f"Status: {s}")
