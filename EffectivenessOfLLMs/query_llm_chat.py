from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel
import json
import requests
import os
import json
import os
import openai

api_key = "sk-Y5ajiDX9mVPXjgwG3303FdA9441c46E082Ff5aFfC6A12040"
api_base = "https://api.ai-yyds.com/v1"

app = FastAPI(debug=True)


class Item(BaseModel):
    model: str
    messages: list
    stream: bool
    temperature: float


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/chat/{llms_name}")
def query_llm(item: Item):
    if item.model in ["gpt-3.5-turbo"]:
        # 初始化 OpenAI 客户端
        client = openai.OpenAI(api_key=api_key, base_url=api_base)
        response = client.chat.completions.create(
            model=item.model,
            messages=item.messages,
            temperature=item.temperature
        ).choices[0].message.content
        return {
            "model": item.model,
            "message": response
        }
    elif item.model in ["sqlcoder:7b", "codellama:7b-instruct", "deepseek-coder:6.7b-instruct",
                        "deepseek-r1:8b-llama-distill-q8_0", "deepseek-r1:8b-llama-distill-q4_K_M"]:
        urls = ["http://localhost:11435/api/chat"]
        headers = {
            "Content-Type": "application/json"
        }
        # 确保 localhost 不走代理
        os.environ["NO_PROXY"] = "localhost"

        url = urls[0]
        response = requests.post(url, headers=headers, data=json.dumps(item.model_dump()))
        if response.status_code == 200:
            return response.json()
        else:
            print("错误:", response.status_code, response.text)
            return {
                "model": item.model,
                "error": response.status_code,
                "message": response.text
            }
    else:
        print("错误:", "不支持的模型")

# # main 函数调用 update_item，模拟 curl 请求
# if __name__ == "__main__":
#     # test_item = Item(
#     #     model="sqlcoder:7b",
#     #     messages=[
#     #         {"role": "system", "content": "You are an expert in SQL translation."},
#     #         {"role": "user", "content": "Please translate the following SQL statement from MySQL to PostgreSQL , ensuring that the resulting query is functionally equivalent to the original.SQL statement:CREATE TABLE users ( id INT PRIMARY KEY, username VARCHAR(50), email VARCHAR(100), created_at TIMESTAMP );"}
#     #     ],
#     #     stream=False,
#     #     temperature=0.0
#     # )

#     # test_item = Item(
#     #     model="codellama:7b-instruct",
#     #     messages=[
#     #         {"role": "system", "content": "You are an expert in SQL translation."},
#     #         {"role": "user", "content": "Please translate the following SQL statement from MySQL to PostgreSQL , ensuring that the resulting query is functionally equivalent to the original.SQL statement:CREATE TABLE users ( id INT PRIMARY KEY, username VARCHAR(50), email VARCHAR(100), created_at TIMESTAMP );"}
#     #     ],
#     #     stream=False,
#     #     temperature=0.0
#     # )

#     # test_item = Item(
#     #     model="deepseek-coder:6.7b-instruct",
#     #     messages=[
#     #         {"role": "system", "content": "You are an expert in SQL translation."},
#     #         {"role": "user", "content": "Please translate the following SQL statement from MySQL to PostgreSQL , ensuring that the resulting query is functionally equivalent to the original.SQL statement:CREATE TABLE users ( id INT PRIMARY KEY, username VARCHAR(50), email VARCHAR(100), created_at TIMESTAMP );"}
#     #     ],
#     #     stream=False,
#     #     temperature=0.0
#     # )


#     test_item = Item(
#         model="deepseek-r1:8b-llama-distill-q8_0",
#         messages=[
#             {"role": "system", "content": "You are an expert in SQL translation."},
#             {"role": "user", "content": "Please translate the following SQL statement from MySQL to PostgreSQL , ensuring that the resulting query is functionally equivalent to the original.SQL statement:CREATE TABLE users ( id INT PRIMARY KEY, username VARCHAR(50), email VARCHAR(100), created_at TIMESTAMP );"}
#         ],
#         stream=False,
#         temperature=0.0
#     )

#     result = query_llm(test_item)
#     print(json.dumps(result, indent=2, ensure_ascii=False))