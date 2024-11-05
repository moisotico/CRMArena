import json, os
FOLDER_PATH = os.path.dirname(__file__)

    
with open(os.path.join(FOLDER_PATH, "tasks_natural.json"), "r") as f:
    TASKS_NATURAL = json.load(f)
    
with open(os.path.join(FOLDER_PATH, "schema_with_dependencies.json"), "r") as f:
    SCHEMA = json.load(f)
    
    
TOOLS = None