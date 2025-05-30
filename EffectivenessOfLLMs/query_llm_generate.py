from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel
import json
import requests
import os

app = FastAPI(debug=True)

class Item(BaseModel):
    model: str
    prompt: str
    stream:	bool
    temperature: float


urls = ["http://localhost:11435/api/generate"]

headers = {
    "Content-Type": "application/json"
}

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/chat/{llms_name}")
def query_llm(item: Item):
    # 确保 localhost 不走代理
    os.environ["NO_PROXY"] = "localhost"

    url = urls[0]
    response = requests.post(url, headers=headers, data=json.dumps(item.model_dump()))
    if response.status_code == 200:
        return response.json()
        # return {
        #     "model": item.model,
        #     "response": response.json()
        # }
        # return {"data": response.text, "llms_name": llms_name}
    else:
        print("错误:", response.status_code, response.text)
        return {
            "model": item.model,
            "error": response.status_code,
            "message": response.text
        }
        # return {"item_name": item.model, "error": response.status_code, "data": response.text}

    # return {"item_name": item.model, "llms_name": llms_name}


# main 函数调用 update_item，模拟 curl 请求
if __name__ == "__main__":
    # test_item = Item(
    #     model="sqlcoder:7b",
    #     prompt=(
    #         "Please translate the following SQL statement from MySQL to PostgreSQL , "
    #         "ensuring that the resulting query is functionally equivalent to the original."
    #         "SQL statement:CREATE TABLE users ( id INT PRIMARY KEY, username VARCHAR(50), "
    #         "email VARCHAR(100), created_at TIMESTAMP );"
    #     ),
    #     stream=False,
    #     temperature=0.0
    # )

    # test_item = Item(
    #     model="codellama:7b-instruct",
    #     prompt=(
    #         "Please translate the following SQL statement from MySQL to PostgreSQL , "
    #         "ensuring that the resulting query is functionally equivalent to the original."
    #         "SQL statement:CREATE TABLE users ( id INT PRIMARY KEY, username VARCHAR(50), "
    #         "email VARCHAR(100), created_at TIMESTAMP );"
    #     ),
    #     stream=False,
    #     temperature=0.0
    # )

    # test_item = Item(
    #     model="deepseek-coder:6.7b-instruct",
    #     prompt=(
    #         "Please translate the following SQL statement from MySQL to PostgreSQL , "
    #         "ensuring that the resulting query is functionally equivalent to the original."
    #         "SQL statement:CREATE TABLE users ( id INT PRIMARY KEY, username VARCHAR(50), "
    #         "email VARCHAR(100), created_at TIMESTAMP );"
    #     ),
    #     stream=False,
    #     temperature=0.0
    # )


    test_item = Item(
        model="sqlcoder:7b",
        prompt=(
            "Please translate the following SQL statement from MySQL to PostgreSQL , ensuring that the resulting query is functionally equivalent to the original."
            "Output only the translated SQL. Do not add any extra commentary."
            "SQL statement: select unix_timestamp('1970-01-01 01:00:00'),unix_timestamp('1970-01-01 01:00:01'),unix_timestamp('2038-01-19 04:14:07'),unix_timestamp('2038-01-19 04:14:08'); -- UNIX_TIMESTAMP, "
        ),
        stream=False,
        temperature=0.0
    )
        #     prompt=(
        #     "Please translate the following SQL statement from MySQL to PostgreSQL , "
        #     "ensuring that the resulting query is functionally equivalent to the original."
        #     "Output only the translated SQL. Do not add any extra commentary."
        #     "SQL statement:CREATE TABLE users ( id INT PRIMARY KEY, username VARCHAR(50), "
        #     "email VARCHAR(100), created_at TIMESTAMP );"
        # ),

    result = query_llm(test_item)
    print(json.dumps(result, indent=2, ensure_ascii=False))