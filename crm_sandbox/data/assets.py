from datasets import load_dataset

crmarena = load_dataset("Salesforce/CRMArena", "CRMArena")
    
TASKS_NATURAL = [data for data in crmarena["test"]]
    
schema = load_dataset("Salesforce/CRMArena", "schema")

SCHEMA = [data for data in schema["test"]]    
    
TOOLS = None