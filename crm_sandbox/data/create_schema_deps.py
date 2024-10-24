import json

def parse_dependencies(file):
    text = open(file, "r").read().strip()
    current_object = None
    dependencies = {}
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("Dependencies for"):
            if current_object:
                for k,v in fields_map.items():
                    fields_map[k] = f"References {v[0]} object." if len(v) == 1 else f"References one of [{', '.join(v)}] objects."
                dependencies[current_object] = fields_map
            current_object = line.split("for ")[1].strip(":")
            dependencies[current_object] = []
            fields_map = {}
        elif line.startswith("- Field:"):
            parts = line.split(", ")
            field = parts[0].split(": ")[1].strip()
            field = _replace_id_in_field(field)
            referenced_object = parts[1].split(": ")[1].strip()
            if field in fields_map:
                fields_map[field].append(referenced_object)
            else:
                fields_map[field] = [referenced_object]
    # Add the last object
    for k,v in fields_map.items():
        fields_map[k] = f"References {v[0]} object." if len(v) == 1 else f"References one of [{', '.join(v)}] objects."
    dependencies[current_object] = fields_map
    return dependencies

def _replace_id_in_field(obj):
    if obj[-2:] == "ID":
        return obj[:-2] + "Id"
    return obj

def concat_update(dict_a, dict_b):
    for key, value in dict_b.items():
        if key in dict_a:
            dict_a[key] += '. ' + value
        else:
            dict_a[key] = value

if __name__ == "__main__":
    dependencies = parse_dependencies("dependencies.txt")
    with open("schema.json", "r") as f:
        schema = json.load(f)

    for item in schema:
        obj = item["object"]
        item["fields"] = {_replace_id_in_field(k): v for k,v in item["fields"].items()}
        if obj in dependencies:
            concat_update(item["fields"], dependencies[obj])
        
    
    with open("schema_with_dependencies.json", "w") as f:
        f.write(json.dumps(schema, indent=2))

    
