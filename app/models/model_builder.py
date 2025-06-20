import yaml

from app.models.basic_models import SQLCoder, OllamaModel, OpenAIModel


def build(model_config_path):
    with open(model_config_path, "r", encoding="utf-8") as file:
        model_config = yaml.safe_load(file)

    if "model_name" not in model_config:
        raise Exception(f"Error loading model config from {model_config_path}: missing model_name")
    if "temperature" not in model_config:
        raise Exception(f"Error loading model config from {model_config_path}: missing temperature")
    model_name = model_config["model_name"]
    temperature = model_config["temperature"]
    if model_name not in ["sqlcoder:7b", "codellama:7b-instruct", "deepseek-coder:6.7b-instruct", "deepseek-r1:8b-llama-distill-q8_0", "gpt-3.5-turbo"]:
        raise Exception(f"Error loading model config from {model_config_path}: {model_name} not supported")

    if model_name == "sqlcoder:7b":
        return SQLCoder(model_name, temperature, model_config)
    elif model_name == "gpt-3.5-turbo":
        return OpenAIModel(model_name, temperature, model_config)
    else:
        return OllamaModel(model_name, temperature, model_config)