import os
import re
from collections import defaultdict
import json
import sys
sys.path.append(r"D:\PythonProjects\TestSuites-Extension\src")
from antlr4 import *
from dialect_matching_calculate.SqlLexer import SqlLexer

# dataset_path = r"../outputs/manually_extractor_for_mysql_test_suites/tasks_chq/dataset/"
#
# dialect_matching_keyword_filepath = r"../outputs/sql_extractor_for_mysql_test_suites/dialect_info/mysql_test_suites_extension_dialect_matching_keywords.json"

class DMCaculator:
    def __init__(self, dataset_path, dialect_matching_keywords_filepath):
        self.dataset_path = dataset_path
        self.dialect_matching_keywords_filepath = dialect_matching_keywords_filepath
        # 读取所有的任务（dataset）
        self.dataset = defaultdict(dict)
        print(dataset_path)
        for detailed_dataset_name in os.listdir(dataset_path):
            if ".json" not in detailed_dataset_name:
                continue
            target_dbms = detailed_dataset_name.replace(".json", "").replace("bird-", "")
            with open(os.path.join(self.dataset_path, detailed_dataset_name), mode="r", encoding="utf-8") as f:
                detailed_dataset = json.load(f)
            for item in detailed_dataset:
                self.dataset[target_dbms][item["sql_id"]] = item
        # 读取映射后的方言的匹配关键字
        with open(self.dialect_matching_keywords_filepath, mode="r", encoding="utf-8") as f:
            self.dialect_matching_keywords = json.load(f)

    def get_tokens(self, sql_text):
        input_stream = InputStream(sql_text)
        lexer = SqlLexer(input_stream)
        token_stream = CommonTokenStream(lexer)
        token_stream.fill()
        return token_stream.tokens

    def compute_tp_fn_fp_per_task(self, task_id, pd_sql, target_dbms):
        task = self.dataset[target_dbms][task_id]
        gt_sql = task["target_query"]
        if "dialect_tokens" in task:
            dialect_tokens = task["dialect_tokens"]
        else:
            dialect_tokens = []
            for item in task["source_dialect_locations"]:
                token = task["source_query"][item["start_index"]:item["end_index"]]
                match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*\(', token)
                if match:
                    func_name = match.group(1)
                    dialect_tokens.append(func_name)
            print("dialect_tokens:"+str(dialect_tokens))


        # 计算TP_n
        TP_n = 0
        for dialect_token in dialect_tokens:
            matching_keywords = self.dialect_matching_keywords[dialect_token][target_dbms]["matching_keyword"] if dialect_token in self.dialect_matching_keywords else []
            for matching_keyword in matching_keywords:
                if matching_keyword in pd_sql:
                    TP_n += 1
                    break

        # 计算FN_n
        FN_n = len(dialect_tokens) - TP_n

        # 计算FP_n
        gt_sql_tokens = self.get_tokens(gt_sql)
        gt_identifiers = {token.text.replace("`", "").replace("\"", "") for token in gt_sql_tokens if token.type == SqlLexer.IDENTIFIER}
        pd_sql_tokens = self.get_tokens(pd_sql)
        pd_identifiers = {token.text.replace("`", "").replace("\"", "") for token in pd_sql_tokens if token.type == SqlLexer.IDENTIFIER}
        FP_n = len(pd_identifiers - gt_identifiers)

        print(pd_identifiers)
        print(gt_identifiers)
        print(pd_identifiers - gt_identifiers)

        return TP_n, FP_n, FN_n

def test():
    dataset_path = os.path.join("..", "test-suites-extension", "dataset")
    dialect_matching_keyword_filepath = r"mysql_test_suites_extension_dialect_matching_keywords.json"
    dm_caculator = DMCaculator(dataset_path, dialect_matching_keyword_filepath)
    # TP_n, FP_n, FN_n
    print(dm_caculator.compute_tp_fn_fp_per_task("clickhouse_1_6", "SELECT * FROM t0 WHERE (a, b) IN (ROW(1, 10));", "clickhouse"))

    # dataset_path = os.path.join("..", "bird-dlbench")
    # dialect_matching_keyword_filepath = r"bird_extension_dialect_matching_keywords.json"
    # dm_caculator = DMCaculator(dataset_path, dialect_matching_keyword_filepath)
    # # TP_n, FP_n, FN_n
    # print(dm_caculator.compute_tp_fn_fp_per_task(216, "SELECT (CAST(SUM(CASE WHEN substring('Last Updated', -4) > '2018' THEN 1 ELSE 0 END) AS Float64) * 100) / COUNT(App) AS PER FROM playstore WHERE _Type = 'Free' AND Rating >= 4.5","clickhouse"))


