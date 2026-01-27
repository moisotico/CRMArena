import os
from litellm import completion
import litellm
litellm.set_verbose = False
from typing import Dict, List
import time, traceback
from crm_sandbox.agents.prompts import SCHEMA_STRING, REACT_RULE_STRING, ACT_RULE_STRING, SYSTEM_METADATA, REACT_EXTERNAL_INTERACTIVE_PROMPT, REACT_INTERNAL_INTERACTIVE_PROMPT, REACT_INTERNAL_PROMPT, REACT_EXTERNAL_PROMPT, REACT_PRIVACY_AWARE_EXTERNAL_PROMPT, REACT_PRIVACY_AWARE_EXTERNAL_INTERACTIVE_PROMPT, ACT_PROMPT
from crm_sandbox.agents.utils import (
    parse_wrapped_response,
    BEDROCK_MODELS_MAP,
    TOGETHER_MODELS_MAP,
    VERTEX_MODELS_MAP,
    ANTHROPIC_MODELS_MAP,
    CUSTOM_SERVER_MODELS_MAP,
    get_dynamic_max_tokens,
    estimate_input_tokens,
    get_openrouter_extra_body,
    openrouter_completion,
)
import together
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




class ChatAgent:
    def __init__(
        self, schema_obj, model: str = "gpt-4o", max_turns: int = 20, eval_mode="default", strategy="react", provider="bedrock", interactive=False, agent_type="internal", privacy_aware_prompt=False, openrouter_providers=None
    ):
        schema = self._build_schema(schema_obj)
        assert strategy in ["react", "act"], "Only react and act strategies supported for now"
        assert agent_type in ["internal", "external"], "Invalid agent type"
        
        
        if strategy == "react":
            # react strategy
            if not interactive:
                if agent_type == "internal":
                    self.sys_prompt = REACT_INTERNAL_PROMPT.format(system_description=schema, system="Salesforce instance") # add strategy template and schema description
                else:
                    if privacy_aware_prompt:
                        self.sys_prompt = REACT_PRIVACY_AWARE_EXTERNAL_PROMPT.format(system_description=schema, system="Salesforce instance") # add strategy template and schema description
                    else:
                        self.sys_prompt = REACT_EXTERNAL_PROMPT.format(system_description=schema, system="Salesforce instance") # add strategy template and schema description
            else:
                if agent_type == "internal":
                    self.sys_prompt = REACT_INTERNAL_INTERACTIVE_PROMPT.format(system_description=schema, system="Salesforce instance") # add strategy template and schema description
                else:
                    if privacy_aware_prompt:
                        self.sys_prompt = REACT_PRIVACY_AWARE_EXTERNAL_INTERACTIVE_PROMPT.format(system_description=schema, system="Salesforce instance") # add strategy template and schema description
                    else:
                        self.sys_prompt = REACT_EXTERNAL_INTERACTIVE_PROMPT.format(system_description=schema, system="Salesforce instance") # add strategy template and schema description
        else:
            # act strategy
            self.sys_prompt = ACT_PROMPT.format(system_description=schema, system="Salesforce instance")
        
        self.agent_type = agent_type
        self.original_model_name = model
        self.model = model
        self.eval_mode = eval_mode
        self.max_turns = max_turns
        self.strategy = strategy
        self.info = {}
        self.usage = {"cost": [], "completion_tokens": [], "prompt_tokens": [], "total_tokens": []}
        self.provider = provider
        self.openrouter_providers = openrouter_providers or []

        if provider == "bedrock" and self.model in BEDROCK_MODELS_MAP:
            os.environ["AWS_REGION_NAME"] = BEDROCK_MODELS_MAP[self.model]["region"]
            self.model = BEDROCK_MODELS_MAP[self.model]["name"]
        elif provider == "together_ai" and self.model in TOGETHER_MODELS_MAP:
            self.model = TOGETHER_MODELS_MAP[self.model]["name"]
        elif "vertex" in provider and self.model in VERTEX_MODELS_MAP:
            self.model = VERTEX_MODELS_MAP[self.model]["name"]
        elif provider == "anthropic" and self.model in ANTHROPIC_MODELS_MAP:
            self.model = ANTHROPIC_MODELS_MAP[self.model]["name"]
        elif provider == "custom_server" and self.model in CUSTOM_SERVER_MODELS_MAP:
            # Handle custom LiteLLM server models
            self.custom_server_config = CUSTOM_SERVER_MODELS_MAP[self.model]
            self.model = self.custom_server_config["name"]
        elif provider == "litellm_server":
            # Handle LiteLLM server - need openai/ prefix for provider detection
            if not self.model.startswith("openai/"):
                self.model = f"openai/{self.model}"
        else:
            pass
        if self.model in ["o1-mini", "o1-preview", "o1-2024-12-17", "o3-mini-2025-01-31"]:
            import litellm
            
            litellm.drop_params=True
            print("dropping parameters")
            
            # assert self.model in ["o1-mini", "o1-preview", "gpt-4o-2024-08-06", "gpt-3.5-turbo-0125"], "Invalid model name"
    
    def _build_schema(self, schema_obj):
        object_description = dict()
        for item in schema_obj:
            object_description[item["object"]] = "\n".join([f"  - {k}: {v}" for k,v in item["fields"].items()])
            
        template = SCHEMA_STRING.format(
            object_names=", ".join(object_description.keys()),
            object_fields="\n".join(
                [f"{obj}\n{fields}" for obj, fields in object_description.items()]
            )
        )
        return template
    
    def _safe_add_message(self, role, content, fallback_content="(empty message)"):
        """Safely add a message, ensuring content is never blank to prevent Bedrock errors."""
        if not content or (isinstance(content, str) and not content.strip()):
            logger.warning(f"Prevented blank content for role '{role}', using fallback: {fallback_content}")
            content = fallback_content
        self.messages.append({"role": role, "content": content})

    def reset(self, args):
        if args["metadata"]["required"]:
            self.sys_prompt += SYSTEM_METADATA.format(system_metadata=args["metadata"]["required"], system="Salesforce instance") # add task/query-specific metadata here
        if self.eval_mode == "aided" and "optional" in args["metadata"]:
            self.sys_prompt += "\n" + args["metadata"]["optional"]
        if self.original_model_name not in ["o1-mini", "o1-preview", "o1-2024-12-17", "deepseek-r1", "o3-mini-2025-01-31", "gemini-2.5-flash-preview-04-17", "gpt-oss-20b"]:
            self.messages = [{"role": "system", "content": self.sys_prompt.strip()}]
            self._safe_add_message("user", args["query"].strip())
        
        else:
            # No system role for o1-mini and o1-preview
            self.messages = [{"role": "user", "content": self.sys_prompt + "\n\n" + args["query"]}]
        self.usage = {"cost": [], "completion_tokens": [], "prompt_tokens": [], "total_tokens": []}
        
    def act(self, env, index=None, temperature=0.0):
        query, metadata = env.reset(task_index=index)
        self.reset({"query": query, "metadata": metadata})
        # print("----")
        # print(self.sys_prompt)
        # print("----")
        # total_cost = 0.0
        self.info["observation_sizes"] = []
        done = False
        reward = 0
        
        current_agent_turn = 0
        # for turn_id in range(self.max_turns):
        while current_agent_turn < self.max_turns:
            info = {}
            current_agent_turn += 1
            logger.info(f"Agent turn {current_agent_turn} started")
            # turn off thinking for gemini 2.5 flash
            if self.original_model_name == "gemini-2.5-flash-preview-04-17":
                thinking = {"type": "disabled", "budget_tokens": 0}
            elif self.original_model_name == "gemini-2.5-flash-preview-04-17-thinking-4096":
                thinking = {"type": "enabled", "budget_tokens": 4096}
            else:
                thinking = None
            
            # Calculate max_tokens with context window safety
            input_tokens = estimate_input_tokens(self.messages)
            max_tokens = get_dynamic_max_tokens(self.original_model_name, input_tokens)
            
            # Debug logging for max_tokens calculation
            logger.info(f"DEBUG: max_tokens calculation: original_model_name={self.original_model_name}, input_tokens={input_tokens}, calculated_max_tokens={max_tokens}")
            
            # Safety check for negative max_tokens
            if max_tokens <= 0:
                logger.error(f"ERROR: Calculated negative max_tokens={max_tokens}, using fallback=1")
                max_tokens = 1


            # Base completion arguments (keep existing logic intact)
            # Models that don't allow both temperature and top_p
            models_without_top_p = ["o3-mini-2025-01-31"]
            # Anthropic models don't allow both temperature and top_p
            if self.provider == "anthropic" or "anthropic/" in self.model:
                models_without_top_p.append(self.model)
            
            completion_kwargs = {
                "messages": self.messages,
                "model": self.model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": 1.0 if self.model not in models_without_top_p else None,
                "thinking": thinking,
                "additional_drop_params": ["temperature"] if self.original_model_name in ["o1-mini", "o1-preview", "o1-2024-12-17", "deepseek-r1", "o3-mini-2025-01-31"] else []
            }
            extra_body = get_openrouter_extra_body(model=self.model, provider=self.provider, openrouter_providers=self.openrouter_providers)
            if extra_body:
                completion_kwargs["extra_body"] = extra_body
            
            # Add custom server parameters only if needed
            if self.provider in ["custom_server", "litellm_server"] and hasattr(self, 'custom_server_config'):
                completion_kwargs["base_url"] = self.custom_server_config["base_url"]
                completion_kwargs["api_key"] = self.custom_server_config["api_key"]
            
            # Retry with exponential backoff for custom server
            max_retries = 3 if self.provider in ["custom_server", "litellm_server"] else 1
            logger.info(f"DEBUG: About to call LiteLLM with {max_retries} max retries, provider: {self.provider}")
            logger.info(f"DEBUG: LiteLLM call kwargs: model={completion_kwargs['model']}, max_tokens={completion_kwargs['max_tokens']}, temperature={completion_kwargs.get('temperature', 'None')}")
            
            for retry in range(max_retries):
                try:
                    logger.info(f"DEBUG: LiteLLM attempt {retry + 1}/{max_retries}")
                    logger.info(f"DEBUG: extra_body={extra_body}, self.provider={self.provider}")
                    logger.info(f"DEBUG: condition (extra_body and self.provider == 'openrouter') = {bool(extra_body and self.provider == 'openrouter')}")
                    if extra_body and self.provider == "openrouter":
                        logger.info(f"DEBUG: USING openrouter_completion() with extra_body={extra_body}")
                        res = openrouter_completion(
                            model=self.model,
                            messages=self.messages,
                            temperature=temperature,
                            top_p=completion_kwargs.get("top_p"),
                            max_tokens=max_tokens,
                            tools=None,
                            timeout=completion_kwargs.get("timeout"),
                            extra_body=extra_body,
                        )
                    else:
                        res = completion(**completion_kwargs)
                    logger.info(f"DEBUG: LiteLLM call succeeded on attempt {retry + 1}")
                    break
                except Exception as e:
                    if retry < max_retries - 1:
                        wait_time = 2 ** retry
                        logger.info(f"LiteLLM call failed (attempt {retry + 1}/{max_retries}), retrying in {wait_time}s: {e}")
                        time.sleep(wait_time)
                    else:
                        logger.info(f"DEBUG: All retry attempts failed, raising exception: {e}")
                        raise e
            
            
            message = res.choices[0].message.model_dump()
            
            
            usage = res.usage

            for key in self.usage.keys():
                if key != "cost":
                    self.usage[key].append(usage.get(key, 0))

            self.usage["cost"].append(res._hidden_params["response_cost"])
            action = self.message_action_parser(message, self.model)
            print("User Turn:", env.current_user_turn, "Agent Turn:", current_agent_turn, "Agent:", message["content"].strip())
            self._safe_add_message("assistant", message["content"].strip())
            if action is None:
                self.info["end_reason"] = {
                    "source": "agent",
                    "message": "Invalid action",
                    "content":  message["content"].strip()
                }
                info["end_reason"] = self.info["end_reason"]
                if self.strategy == "react":
                    self._safe_add_message("user", REACT_RULE_STRING)
                elif self.strategy == "act":
                    self._safe_add_message("user", ACT_RULE_STRING)
                continue
            obs, reward, done, info = env.step(action)
            
            if "observation_size" in info:
                self.info["observation_sizes"].append(info["observation_size"])
            if "end_reason" in info: # implies error in query
                self.info["end_reason"] = info["end_reason"]
            # reset counter if previous action is respond
            if action["name"] == "respond":
                current_agent_turn = 0
            if done:
                break
            elif action["name"] == "execute": # execution results from
                safe_obs = obs if obs else "(empty)"
                obs_content = f"Salesforce instance output: {safe_obs}"
                self._safe_add_message("user", obs_content)
            elif action["name"] == "respond": # respond to simulated user
                safe_obs = obs if obs and obs.strip() else "(empty response)"
                self._safe_add_message("user", safe_obs)
        
        # Here when either max_turns is reached or submitted
        if not done: 
            if "end_reason" not in info: # no error in last query
                self.info["end_reason"] = {
                    "source": "agent",
                    "message": "Max turns reached",
                    "content":  message["content"].strip()
                }
        self.info["usage"] = self.usage
        self.info["total_cost"] = sum(cost for cost in self.usage["cost"] if cost is not None)
        self.info["num_turns"] = (env.current_user_turn, current_agent_turn + 1)
        return reward

    def get_messages(self) -> List[Dict[str, str]]:
        return self.messages

    @staticmethod
    def message_action_parser(message: Dict[str, str], model_name: str) -> Dict[str, str]:
        action = None
        if not message or not message.get("content"):
            return None
        content = message["content"].strip()
        # if model_name "deepseek-r1":
        #     content = content.split("</think>")[1]
        resp = parse_wrapped_response(r'<execute>(.*?)</execute>', content).strip()
        if resp:
            action = {"name": "execute", "content": resp}
            return action
        
        resp = parse_wrapped_response(r'<respond>(.*?)</respond>', content).strip()
        if resp:
            action = {"name": "respond", "content": resp}
            return action
        return action
