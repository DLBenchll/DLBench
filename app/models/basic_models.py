import json
import os
import re
from abc import abstractmethod

from openai import OpenAI
import requests
from pydantic import BaseModel


class Item(BaseModel):
    model: str
    messages: list
    stream: bool
    temperature: float

class BasicModel:
    def __init__(self, model_name, temperature, model_config):
        self.model_name = model_name
        self.system_prompt = "You are an expert SQL translation assistant.Let's think step by step."
        self.temperature = temperature
        self.model_config = model_config
        self.user_prompt = {
            "task_description": "Please translate the following SQL statement from {source_dbms} to {target_dbms} , ensuring that the resulting query is functionally equivalent to the original. [SQL statement]:{source_query}\n",
            "schema_information": "{source_dbms} schema: {source_related_schemas}.\n {target_dbms} schema: {target_related_schemas}.",
            "external_dialect_knowledge": "may refer to these dialect rules and tips to guide your translation.{source_dbms} dialect knowledge:{source_dialect_knowledge}.",
            "output_constrains": "Output only the translated SQL in format of: ```sql<translated SQL>```. Do not add any extra commentary."
        }

    @abstractmethod
    def generate(self, messages: list):
        pass

    def generate_messages(self, item, use_fs, use_ka, few_shots=None):
        user_content = "[Task Descriptions]:" + self.user_prompt["task_description"].format(source_dbms=item["source_dbms"], target_dbms=item["target_dbms"], source_query=item["source_query"])
        user_content += "\n[Schema Information]:" + self.user_prompt["schema_information"].format(source_dbms=item["source_dbms"], source_related_schemas=item["source_related_schemas"], target_dbms=item["target_dbms"], target_related_schemas=item["target_related_schemas"])
        if use_ka:
            user_content += "\n[External Dialect Knowledge]:" + self.user_prompt["external_dialect_knowledge"].format(source_dbms=item["source_dbms"], source_dialect_knowledge=item["source_dialect_knowledge"], target_dbms=item["target_dbms"], target_dialect_knowledge=item["target_dialect_knowledge"])
        if use_fs and few_shots is not None:
            user_content += "\n[Few-shot Demonstrations]:"
            for idx, shot in enumerate(few_shots):
                user_content += f"\n[Example {idx + 1}]:"
                user_content += str(shot)
        user_content += "\n[Output Constrains]:" + self.user_prompt["output_constrains"]
        messages = [{"role": "system", "content": self.system_prompt}, {"role": "user", "content": user_content}]
        return messages

    def parse_response_content(self, response_content):
        def remove_extra_whitespace(s):
            # \s+ 表示连续一个或多个空白符，替换成一个空格
            return re.sub(r'\s+', ' ', s).strip()

        matches = re.findall(r"```sql\s*(.*?)\s*```", response_content, re.DOTALL)
        if len(matches) == 0:
            return response_content
        else:
            return remove_extra_whitespace(matches[0])

    def translateSQL(self, item, use_fs, use_ka, few_shots=None):
        messages = self.generate_messages(item, use_fs, use_ka, few_shots)
        response_content, raw_response = self.generate(messages)
        parsed_result = self.parse_response_content(response_content)
        return parsed_result, raw_response

class OllamaModel(BasicModel):

    def __init__(self, model_name, temperature, model_config):
        super().__init__(model_name, temperature, model_config)
        self.url = self.model_config["url"]
        self.stream = self.model_config["stream"]
        self.header = {"Content-Type": "application/json"}
        os.environ["NO_PROXY"] = "localhost"

    def generate(self, messages: list):
        response = requests.post(url=self.url, headers=self.header, data=json.dumps(Item(model=self.model_name, messages=messages, stream=self.stream, temperature=self.temperature).model_dump()))
        if response.status_code == 200:
            raw_response = response.json()
            response_content = raw_response["message"]["content"]
            return response_content, raw_response
        else:
            raise Exception(f"Error: {response.status_code} {response.text}")

class SQLCoder(OllamaModel):
    def __init__(self, model_name, temperature, model_config):
        super().__init__(model_name, temperature, model_config)
        self.user_prompt["output_constrains"] = "Output only the translated SQL. Do not add any extra commentary."

    def generate_messages(self, item, use_fs, use_ka, few_shots=None):
        user_content = "### Task:\n" + self.user_prompt["task_description"].format(source_dbms=item["source_dbms"], target_dbms=item["target_dbms"], source_query=item["source_query"])
        user_content += "\n[Schema Information]:" + self.user_prompt["schema_information"].format(source_dbms=item["source_dbms"], source_related_schemas=item["source_related_schemas"], target_dbms=item["target_dbms"], target_related_schemas=item["target_related_schemas"])
        if use_ka:
            user_content += "\n### External Dialect Knowledge:\n" + self.user_prompt["external_dialect_knowledge"].format(source_dbms=item["source_dbms"], source_dialect_knowledge=item["source_dialect_knowledge"], target_dbms=item["target_dbms"], target_dialect_knowledge=item["target_dialect_knowledge"])
        if use_fs and few_shots is not None:
            user_content += "\n### Few-shot Demonstrations:\n"
            for idx, shot in enumerate(few_shots):
                user_content += f"\n[Example {idx + 1}]:"
                user_content += str(shot)
        user_content += "\n### Output Constrains:\n" + self.user_prompt["output_constrains"]
        messages = [{"role": "system", "content": self.system_prompt}, {"role": "user", "content": user_content}]
        return messages

    def parse_response_content(self, response_content):
        idx = response_content.find(':')
        if idx != -1:
            sql = response_content[idx + 1:].strip()
        else:
            sql = response_content.strip()
        sql = re.sub(r'^<s>\s*', '', sql)
        sql = re.sub(r'\s*</s>$', '', sql)
        output_string_processed = sql.strip()
        return output_string_processed


class OpenAIModel(BasicModel):
    def __init__(self, model_name, temperature, model_config):
        super().__init__(model_name, temperature, model_config)
        if self.model_config["http_proxy"] != "" and self.model_config["https_proxy"] != "":
            os.environ["HTTP_PROXY"] = self.model_config["http_proxy"]
            os.environ["HTTPS_PROXY"] = self.model_config["https_proxy"]
        self.api_key = self.model_config["openai_api_key"]
        self.base_url = self.model_config["openai_api_base"]
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def generate(self, messages: list):
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature
        )
        return response.choices[0].message.content, {
            "role": "assistant",
            "content": response.choices[0].message.content
        }
