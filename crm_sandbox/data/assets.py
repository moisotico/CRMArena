from datasets import load_dataset

crmarena = load_dataset("Salesforce/CRMArena", "CRMArena")
    
TASKS_NATURAL = [data for data in crmarena["test"]]
    
schema = load_dataset("Salesforce/CRMArena", "schema")

SCHEMA = [data for data in schema["test"]]    

# work around for huggingface's data representations
for schema in SCHEMA:
    schema["fields"] = {k: v for k, v in schema["fields"].items() if v is not None}
    
TOOLS = None