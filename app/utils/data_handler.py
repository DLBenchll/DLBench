import json
import os.path


def load_input_data(input_data_path):
    with open(input_data_path, "r", encoding="utf-8") as file:
        input_data = json.load(file)

    keys_to_check = {"sql_id", "database_name", "source_dbms", "target_dbms", "source_query", "source_dialect_knowledge", "target_dialect_knowledge", "source_related_schemas", "target_related_schemas"}

    def item_check(item_):
        missing_keys = keys_to_check - set(item_.keys())
        if missing_keys:
            raise ValueError(f"Missing keys: {', '.join(missing_keys)} in {item_}")

    if isinstance(input_data, list):
        for item in input_data:
            item_check(item)
    else:
        item_check(input_data)

    return input_data

def load_few_shot_examples(few_shots_dir, source_dbms, target_dbms):
    with open(file=os.path.join(few_shots_dir, f"{source_dbms}_{target_dbms}.json"), mode="r", encoding="utf-8") as file:
        return json.load(file)

def load_dataset(dataset_path):
    return load_input_data(dataset_path)