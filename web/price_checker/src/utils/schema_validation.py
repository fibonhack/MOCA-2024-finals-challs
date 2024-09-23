import json
from jsonschema import validate, ValidationError

def validate_json(json_data, schema_file_path):
    try:
        # Load JSON Schema from file
        with open(schema_file_path, 'r') as schema_file:
            schema = json.load(schema_file)
        
        # Validate JSON data against the schema
        validate(instance=json_data, schema=schema)
        return True
    
    except ValidationError as e:
        return False
    except json.JSONDecodeError as e:
        return False
    except FileNotFoundError as e:
        return False
    except Exception as e:
        return False

