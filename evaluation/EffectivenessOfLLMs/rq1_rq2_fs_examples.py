import json
import os
import random
from query_llm_chat import query_llm, Item

def rq1_rq2_exp(input_file, output_file, model_, stream_, temperature_, fs, ka):
    prompt_template_others = {
        "System messages": "You are an expert SQL translation assistant.Let's think step by step.",
        "Task Descriptions": "Please translate the following SQL statement from {source_dialect} to {target_dialect} , ensuring that the resulting query is functionally equivalent to the original. [SQL statement]:{source_query}",
        "Schema Information": "{source_dialect} schema: {source_related_schemas}.\n {target_dialect} schema: {target_related_schemas}.",
        "External Dialect Knowledge": "You may refer to these dialect rules and tips to guide your translation.{source_dialect} dialect knowledge:{source_dialect_knowledge}.\n {target_dialect} dialect knowledge: {target_dialect_knowledge}",
        "Few-shot Demonstrations": "[SQL] ... [Answer]",
        "Output Constrains": "Output only the translated SQL. Do not add any extra commentary."
    }

    prompt_template_deepseek_r1 = {
        "System messages": "You are an expert SQL translation assistant.Let's think step by step.",
        "Task Descriptions": "Please translate the following SQL statement from {source_dialect} to {target_dialect} , ensuring that the resulting query is functionally equivalent to the original. [SQL statement]:{source_query}",
        "Schema Information": "{source_dialect} schema: {source_related_schemas}.\n {target_dialect} schema: {target_related_schemas}.",
        "External Dialect Knowledge": "You may refer to these dialect rules and tips to guide your translation.{source_dialect} dialect knowledge:{source_dialect_knowledge}.\n {target_dialect} dialect knowledge: {target_dialect_knowledge}",
        "Few-shot Demonstrations": "[SQL] ... [Answer]",
        "Output Constrains": "Output only the translated SQL in the following JSON format:{{'answer': 'your answer SQL'}}.Do not add any extra commentary."
    }
    if model_ == "deepseek-r1:8b-llama-distill-q8_0":
        prompt_template = prompt_template_deepseek_r1
    else:
        prompt_template = prompt_template_others
    user_content = "[Task Descriptions]:" + prompt_template["Task Descriptions"] + prompt_template[
        "Output Constrains"] + "\n[Schema Information]:" + prompt_template["Schema Information"]
    if fs:
        user_content = user_content + "1"
    if ka:
        user_content = user_content + "\n[External Dialect Knowledge]:" + prompt_template["External Dialect Knowledge"]

    with open(input_file, "r", encoding="utf-8") as r:
        data_load = json.load(r)
    length = 0
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as r:
            result_load = r.readlines()
        # length = json.loads(result_load[-1])["sql_id"]
        length = len(result_load)

    for index in range(len(data_load)):
        item = data_load[index]
        # 判断是否已经处理过
        if index < length:
            continue
        print(item["sql_id"])
        params = {
            "source_dialect": item["source_dialect"],
            "target_dialect": item["target_dialect"],
            "source_query": item["source_query"],
            "source_related_schemas": item["source_related_schemas"],
            "target_related_schemas": item["target_related_schemas"],
            "source_dialect_knowledge": item["source_dialect_knowledge"],
            "target_dialect_knowledge": item["target_dialect_knowledge"],
        }
        user_format = user_content.format(**params)
        formated_messages = [
            {"role": "system", "content": prompt_template["System messages"]},
            {"role": "user", "content": user_format}
        ]

        print(formated_messages)
        # formated_item = Item(
        #     model=model_,
        #     messages=formated_messages,
        #     stream=stream_,
        #     temperature=temperature_
        # )
        # # print(formated_item.messages)
        # response = query_llm(formated_item)
        # response["sql_id"] = item["sql_id"]

        # 保存结果
        with open(output_file, "a", encoding="utf-8") as a:
            a.write(json.dumps(formated_messages, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    dbs = [
        "clickhouse",
        "duckdb",
        "mariadb",
        "monetdb",
        "mysql"
    ]

    models = [
        "gpt-3.5-turbo"
    ]

    # for db in dbs:
    #     input_file = "../bird-dlbench/bird-{db_name}.json".format(db_name=db)
    #     for model in models:
    #         output_file = "../bird-dlbench/bird-{db_name}-result-{model_name}-fs.jsonl".format(db_name=db, model_name=model)
    #         print(output_file)
    #         # rq1_rq2_exp(input_file, output_file, model, False, 0.0, fs=False, ka=False)
    #         # rq1_rq2_exp(input_file, output_file, model, False, 0.0, fs=True, ka=False)
    #         rq1_rq2_exp(input_file, output_file, model, False, 0.0, fs=False, ka=False)

    dataset_name = "test-suites-extension-postgresql"
    for db in dbs:
        input_file = os.path.join("..", dataset_name, "dataset-processed","{db_name}.json".format(db_name=db))
        output_dic = os.path.join("..", f"{dataset_name}-Output-fs", db)
        if not os.path.exists(output_dic):
            os.makedirs(output_dic)
        for model in models:
            output_file = os.path.join(output_dic,"test-suites-{db_name}-result-{model_name}.jsonl".replace(":", "-").format(db_name=db, model_name=model))
            print(output_file)
            rq1_rq2_exp(input_file, output_file, model, False, 0.0, False, False)
