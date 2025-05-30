from __future__ import print_function
import os
import json
import nltk
import os
import shutil
import re

from bson.codec import encode_cstring

from dbms_connectors.connector_factory import get_connector_by_dbms_name
from dialect_matching_calculate.compute_tp_fn_fp import DMCaculator
nltk.download('punkt_tab')

current_file_path = os.path.abspath(__file__)
# 获取当前文件所在目录
current_dir = os.path.dirname(current_file_path)

class Evaluator:
    """A simple evaluator"""
    def tokenize_sql(self, sql):
        """
        将 SQL 语句按单词和符号分词，忽略多余的空格和换行。
        注意：大小写敏感，保留原始字符。
        """
        # 去掉多余空白符（换行、tab、多个空格）
        sql_processed = re.sub(r'\s+', ' ', sql.strip())

        # 用正则分词：按关键词、标识符、符号、数值等分开
        # 匹配规则：单词、数字、符号 (如 =, >, *, ,, (, ) 等)
        tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*|\d+|[^\s\w]", sql_processed)

        return tokens

    def eval_exact_match(self, sql1, sql2):
        """
        对两个 SQL 语句进行分词后比较。
        忽略多余空格和换行，不忽略大小写。
        若所有 token 完全匹配，返回 1，否则返回 0。
        """
        tokens1 = self.tokenize_sql(sql1)
        tokens2 = self.tokenize_sql(sql2)
        return int(tokens1 == tokens2)

    def eval_exec_match(self, dataset_name, database_name, db, p_str, g_str):
        """
        return 1 if the values between prediction and gold are matching
        in the corresponding index. Currently not support multiple col_unit(pairs).
        """

        # # 初始化对应的database，针对bird集合去除（改为了先新建所有数据库）
        # init_database(db, database_name)

        with open("dbms_connectors/dbms_config.json", "r", encoding="utf-8") as r:
            dbms_config = json.load(r)
        # 打开该db时，不清空该数据库（因为已经建表并初始化了）
        dbms_config[db]["drop_database"] = False
        if db == "duckdb":
            dbms_config[db]["db_path"] = os.path.join(current_dir, dataset_name, "schemas-duckdb", f"{database_name}.duckdb")
            print(dbms_config[db]["db_path"])
        else:
            dbms_config[db]["database_name"] = database_name

        # 如果是test suites,都要新建表格，结束再删除表格
        if dataset_name == "test-suites-extension":
            init_database(dataset_name, db, database_name)
        connector = get_connector_by_dbms_name(db, **dbms_config[db])
        g_res, g_rowcount, g_error_message = connector.execute(g_str)
        if not g_res:
            g_res_str = "None"
        else:
            g_res_str = connector.record_to_str(g_res) if not g_error_message else ""
        connector.close()
        # if dataset_name == "test-suites-extension":
        #     connector.drop_database(database_name)

        # 如果是test suites,都要新建表格,结束再删除表格
        if dataset_name == "test-suites-extension":
            init_database(dataset_name, db, database_name)
        connector = get_connector_by_dbms_name(db, **dbms_config[db])
        p_res, p_rowcount, p_error_message = connector.execute(p_str)
        if not p_res:
            p_res_str = "None"
        else:
            p_res_str = connector.record_to_str(p_res) if not p_error_message else ""
        connector.close()
        # if dataset_name == "test-suites-extension":
        #     # connector.drop_database(database_name)

        g_exec_result = {
            "result": g_res_str,
            "rowcount": g_rowcount,
            "error_message": str(g_error_message),
            "exec_able": True if not g_error_message else False
        }

        p_exec_result = {
            "result": p_res_str,
            "rowcount": p_rowcount,
            "error_message": str(p_error_message),
            "exec_able": True if not p_error_message else False
        }

        '''
        - **SELECT 查询**：
            - 比较结果集内容
            - 若语义明确指定，则需比较行顺序与重复项
        - **INSERT / UPDATE / DELETE**：
            - 比较 **影响的行数** 是否一致
        '''
        keywords = ["insert", "update", "delete"]
        if any(k in g_res_str.strip().lower() for k in keywords):
            oracle_check = True if g_rowcount == p_rowcount else False
        else:
            oracle_check = True if g_res_str == p_res_str else False

        if g_exec_result["exec_able"] == False or p_exec_result["exec_able"] == False:
            oracle_check = False
        return oracle_check, g_exec_result, p_exec_result

def query_clear(query):
    return query.replace("`","").replace(";","").lower().strip()

def load_dialect_feature(dialect_locations):
    dialect_list = []
    for item in dialect_locations:
        dialect_list.append(item["feature"])

def intersection_size(list1, list2):
    return len(set(list1) & set(list2))

def difference_size(list1, list2):
    return len(set(list1) - set(list2))

def load_ddl(dataset_name, database_name, db):
    with open(os.path.join(current_dir, dataset_name, "schemas", db, database_name+".txt"), "r", encoding="utf-8") as r:
        ddl = r.readlines()
    return ddl

def init_database(dataset_name, db, database_name):
    if database_name == "log":
        return
    with open(os.path.join(current_dir,"dbms_connectors", "dbms_config.json"), "r", encoding="utf-8") as r:
        dbms_config = json.load(r)
    ddl = load_ddl(dataset_name, database_name, db)
    flag = True

    # 打开该db时，需要清空该数据库！！！再进行初始化
    dbms_config[db]["drop_database"] = True
    if db == "duckdb":
        # dbms_config[db]["database_name"] = database_name
        # dbms_config[db]["db_dir"] = os.path.join(current_dir, "bird-dlbench", "schemas")
        # db_path = os.path.join("../bird-dlbench/schemas", f"app_store.duckdb")
        dbms_config[db]["db_path"] = os.path.join(current_dir, dataset_name, "schemas-duckdb", f"{database_name}.duckdb")
    else:
        dbms_config[db]["database_name"] = database_name

    connector = get_connector_by_dbms_name(db, **dbms_config[db])

    # ddl.append("SHOW TABLES;")
    for line in ddl:
        result, rowcount, err = connector.execute(line)
        # print(result)
        # print(rowcount)
        # print('------------------')
        if err:
            flag = False
    if not flag:
        print(database_name + "建表失败")
    else:
        print(database_name + "建表成功")
    connector.close()
    return flag

def drop_database(dataset_name, db, database_name):
    print("drop "+database_name)
    if database_name == "log":
        return
    with open(os.path.join(current_dir,"dbms_connectors", "dbms_config.json"), "r", encoding="utf-8") as r:
        dbms_config = json.load(r)

    # 打开该db时，需要清空该数据库！！！再进行初始化
    dbms_config[db]["drop_database"] = True
    if db == "duckdb":
        dbms_config[db]["db_path"] = os.path.join(current_dir, dataset_name, "schemas-duckdb", f"{database_name}.duckdb")
    else:
        dbms_config[db]["database_name"] = database_name
    connector = get_connector_by_dbms_name(db, **dbms_config[db])
    connector.drop_database(database_name)


def llm_output_process(output_string, model_name):
    output_string_processed = output_string
    if model_name in ["sqlcoder-7b", "sqlcoder:7b"]:
        # 截断第一个 : 之前的所有内容，只保留之后的部分
        idx = output_string_processed.find(':')
        if idx != -1:
            sql = output_string_processed[idx + 1:].strip()
        else:
            sql = output_string_processed.strip()
        # 去除开头的 <s> 和结尾的 </s>（如果有）
        sql = re.sub(r'^<s>\s*', '', sql)
        sql = re.sub(r'\s*</s>$', '', sql)
        output_string_processed = sql.strip()
    elif model_name in ["deepseek-r1-8b-llama-distill-q8_0", "deepseek-r1:8b-llama-distill"]:
        # 提取单引号之间的内容
        match = re.search(r"""['"]answer['"]\s*:\s*(['"])(.*?)}""", output_string_processed, re.DOTALL)
        if match:
            output_string_processed = match.group(2).strip().strip("'")
            output_string_processed = output_string_processed.replace("\\'", "'")
    return output_string_processed

def evaluate(dataset_name, gold_file, predict_file, eval_res_dic, model):
    with open(gold_file, "r", encoding="utf-8") as r:
        gold_lines = json.load(r)
    with open(predict_file, "r", encoding="utf-8") as r:
        pred_lines = r.readlines()

    if not os.path.exists(eval_res_dic):
        os.makedirs(eval_res_dic)
    single_eval_res_file = os.path.join(eval_res_dic, "single_eval_res.jsonl")
    eval_res_file = os.path.join(eval_res_dic, "eval_res.json")
    # if os.path.exists(eval_res_file):
    #     print(eval_res_file+" has been exist.")
    #     return
    if os.path.exists(single_eval_res_file):
        with open(single_eval_res_file, "r", encoding="utf-8") as r:
            processed_cnt = len(r.readlines())
    else:
        processed_cnt = 0

    # plist = [("select max(Share),min(Share) from performance where Type != 'terminal'")]
    # glist = [("SELECT max(SHARE) ,  min(SHARE) FROM performance WHERE TYPE != 'Live final'", "orchestra")]
    evaluator = Evaluator()

    entries = []
    scores = {}  # 记录测试数据的acc，rec，f1，acc_count,rec_count

    # 初始化scores字典
    scores = {'count': 0, 'partial': {}, 'exact': 0.}
    scores['exec'] = 0

    temp = []

    for index in range(len(gold_lines)):
        if index < processed_cnt:
            continue

        gold_json = gold_lines[index]
        sql_id = gold_json["sql_id"]
        print(predict_file)
        print(sql_id)
        # 获取该gold对应的pred信息
        pred_json = json.loads(pred_lines[index])


        # 判断是否对应
        if sql_id != pred_json["sql_id"]:
            print(str(sql_id))
            print(pred_json["sql_id"])
            print(str(sql_id)+ pred_json["sql_id"] + " not match.")
            continue

        tp = 0
        fp = 0
        fn = 0
        # DM：Dialect Matching 方言匹配
        # g_gt = load_dialect_feature(gold_json["target_dialect_locations"])
        # g_pred = [] # 需要antrl进行分析
        # tp = intersection_size(g_pred, g_gt)
        # fp = difference_size(g_pred, g_gt)
        # fn = difference_size(g_gt, g_pred)

        # EM：Exact Matching 精确匹配
        target_query = gold_json["target_query"]
        if type(pred_json["message"]) == dict and "content" in pred_json["message"]:
            predict_query = pred_json["message"]["content"]
        else:
            predict_query = pred_json["message"]

        # 对predict_query做处理（主要是针对sqlcoder模型的结果）
        predict_query = llm_output_process(predict_query, model)
        print("predict query:"+predict_query)
        em_bool = evaluator.eval_exact_match(query_clear(target_query), query_clear(predict_query))

        # else:
        #     # print(target_query.replace("`","").replace(";","").lower())
        #     # print(predict_query.replace("`","").replace(";","").lower())
        #     # print('\n')

        #  EX：Execution Accuracy 执行准确率

        keywords = ["insert", "update", "delete"]
        if any(k in target_query.lower() for k in keywords):
            temp.append(sql_id)


        target_dialect = gold_json["target_dialect"]
        database_name = gold_json["database_name"]
        oracle_check, gold_exec_result, predict_exec_result = evaluator.eval_exec_match(dataset_name, database_name,target_dialect, predict_query, target_query)
        oracle_check = True if em_bool else oracle_check

        # 将单条评估结果存储
        single_eval_result = {
            "sql_id": sql_id,
            "EM": em_bool,
            "EX":{
                "ex_bool": oracle_check,
                "gold_exec_result": gold_exec_result,
                "predict_exec_result": predict_exec_result
            },
            "TP": tp,
            "FP": fp,
            "FN": fn
        }
        with open(single_eval_res_file, 'a', encoding="utf-8") as file:
            json.dump(single_eval_result, file)
            file.write('\n')

        print('---------------------------------')

    print(temp)
    # 计算总体指标
    exact_match_cnt = 0
    exec_match_cnt = 0
    p_dm = 0
    r_dm = 0
    f1_dm = 0
    tp_n = 0
    fp_n = 0
    fn_n = 0
    total_cnt = len(gold_lines)

    with open(single_eval_res_file, "r", encoding="utf-8") as r:
        lines = r.readlines()
    for line in lines:
        data = json.loads(line)
        tp_n += data["TP"]
        fp_n += data["FP"]
        fn_n += data["FN"]
        if data["EM"]:
            exact_match_cnt += 1
        if data["EX"]["ex_bool"]:
            exec_match_cnt += 1
    p_dm = tp_n / (tp_n + fp_n) if (tp_n + fp_n) != 0 else 0
    r_dm = tp_n / (tp_n + fn_n) if (tp_n + fn_n) != 0 else 0
    f1_dm = (2*p_dm*r_dm)/(p_dm+r_dm) if (p_dm+r_dm) != 0 else 0
    eval_result = {
        "P_DM": f"{str(p_dm)}({tp_n}/({tp_n}+{fp_n}))" if tp_n + fp_n != 0 else 0,
        "R_DM": f"{str(r_dm)}({tp_n}/({tp_n}+{fn_n}))" if tp_n + fn_n != 0 else 0,
        "F1_DM": f"{str(f1_dm)}",
        "EM": f"{str(exact_match_cnt/total_cnt)}({exact_match_cnt}/{total_cnt})",
        "EX": f"{str(exec_match_cnt/total_cnt)}({exec_match_cnt}/{total_cnt})"
    }
    with open(eval_res_file, "w", encoding="utf-8") as w:
        json.dump(eval_result, w, indent=4)

def bird_evaluate():
    dbs = [
        # "clickhouse",
        # "duckdb",
        "mariadb", # 不支持
        # "monetdb", # 不支持
        # "mysql",
        # "postgresql"
    ]

    dataset_name = "bird-dlbench"

    for db in dbs:
        # 先初始化建表
        files = os.listdir(f"bird-dlbench/schemas/{db}")
        for file in files:
            database_name = file.replace(".txt", "")
            print(database_name)
            init_database("bird-dlbench", db, database_name)

    # po
    for db in dbs:
        gold = os.path.join("bird-dlbench", f"bird-{db}.json")
        pred_files = os.listdir(os.path.join("Output", db))
        for pred in pred_files:
            model_name = pred.replace(f"bird-{db}-result-", "").replace(".jsonl", "")
            print(model_name)
            evaluate_res_dic = os.path.join("evaluation_results", db, model_name)
            evaluate(dataset_name, gold, os.path.join(os.path.join("Output", db), pred), evaluate_res_dic, model_name)

    # # fs
    # for db in dbs:
    #     gold = os.path.join("bird-dlbench", f"bird-{db}.json")
    #     pred_files = os.listdir(os.path.join("Output-fs", db))
    #     for pred in pred_files:
    #         model_name = pred.replace(f"bird-{db}-result-", "").replace(".jsonl", "")
    #         print(model_name)
    #         evaluate_res_dic = os.path.join("evaluation_results-fs", db, model_name)
    #         evaluate(dataset_name, gold, os.path.join(os.path.join("Output-fs", db), pred), evaluate_res_dic, model_name)
    #
    # # ka
    # for db in dbs:
    #     gold = os.path.join("bird-dlbench", f"bird-{db}.json")
    #     pred_files = os.listdir(os.path.join("Output-ka", db))
    #     for pred in pred_files:
    #         model_name = pred.replace(f"bird-{db}-result-", "").replace(".jsonl", "")
    #         print(model_name)
    #         evaluate_res_dic = os.path.join("evaluation_results-ka", db, model_name)
    #         evaluate(dataset_name, gold, os.path.join(os.path.join("Output-ka", db), pred), evaluate_res_dic, model_name)

    # drop_database("bird-dlbench", "duckdb", "authors")

    for db in dbs:
        # 最后销毁所有database
        files = os.listdir(f"bird-dlbench/schemas/{db}")
        for file in files:
            database_name = file.replace(".txt", "")
            print(database_name)
            drop_database("bird-dlbench", db, database_name)


def bird_evaluate_dm():
    dbs = [
        'clickhouse',
        'duckdb',
        'postgresql',
        'mysql',
        'mariadb',
        'monetdb',
    ]

    dataset_name = "bird-dlbench"
    dataset_path = os.path.join("bird-dlbench")
    dialect_matching_keyword_filepath = os.path.join("dialect_matching_calculate", "bird_extension_dialect_matching_keywords.json")
    dm_caculator = DMCaculator(dataset_path, dialect_matching_keyword_filepath)

    # po
    for db in dbs:
        gold = os.path.join("bird-dlbench", f"bird-{db}.json")
        output_dic = os.path.join("Output", db)
        for pred in os.listdir(output_dic):
            model_name = pred.replace(f"bird-{db}-result-", "").replace(".jsonl", "")
            evaluate_res_dic = os.path.join("evaluation_results", db, model_name)
            single_eval_res_file = os.path.join(evaluate_res_dic, "single_eval_res.jsonl")
            eval_res_file = os.path.join(evaluate_res_dic, "eval_res.json")

            # 遍历output内的数据
            modified_data = []
            with open(os.path.join(output_dic, pred), "r", encoding="utf-8") as r:
                output_lines = r.readlines()
            with open(single_eval_res_file, "r", encoding="utf-8") as r:
                single_eval_lines = r.readlines()
            for index, output_line in enumerate(output_lines):
                data = json.loads(output_line)
                if index >= len(single_eval_lines):
                    # print(single_eval_res_file)
                    # print(data["sql_id"])
                    # print(data["sql_id"] + " 超出index")
                    continue
                if type(data["message"]) == dict and "content" in data["message"]:
                    predict_query = data["message"]["content"]
                else:
                    predict_query = data["message"]
                predict_query = llm_output_process(predict_query, model_name)
                # TP_n, FP_n, FN_n
                # 将 tp, fp, fn更新到原本的数据上
                print(single_eval_res_file)
                old_data = json.loads(single_eval_lines[index])
                if data["sql_id"] != old_data["sql_id"]:
                    print(data["sql_id"])
                    print(data["sql_id"] + " not match.")
                    continue
                old_data["TP"], old_data["FP"], old_data["FN"] = dm_caculator.compute_tp_fn_fp_per_task(data["sql_id"],predict_query,db)
                if old_data["FP"] >=6:
                    old_data["FP"] = 5
                modified_data.append(old_data)
                print('---------------------')
            with open(single_eval_res_file, "w", encoding="utf-8") as w:
                for item in modified_data:
                    json.dump(item, w)
                    w.write('\n')


    # fs
    for db in dbs:
        gold = os.path.join("bird-dlbench", f"bird-{db}.json")
        output_dic = os.path.join("Output-fs", db)
        for pred in os.listdir(output_dic):
            model_name = pred.replace(f"bird-{db}-result-", "").replace(".jsonl", "")
            evaluate_res_dic = os.path.join("evaluation_results-fs", db, model_name)
            single_eval_res_file = os.path.join(evaluate_res_dic, "single_eval_res.jsonl")
            eval_res_file = os.path.join(evaluate_res_dic, "eval_res.json")

            # 遍历output内的数据
            modified_data = []
            with open(os.path.join(output_dic, pred), "r", encoding="utf-8") as r:
                output_lines = r.readlines()
            with open(single_eval_res_file, "r", encoding="utf-8") as r:
                single_eval_lines = r.readlines()
            for index, output_line in enumerate(output_lines):
                data = json.loads(output_line)
                if index >= len(single_eval_lines):
                    # print(single_eval_res_file)
                    # print(data["sql_id"])
                    # print(data["sql_id"] + " 超出index")
                    continue
                if type(data["message"]) == dict and "content" in data["message"]:
                    predict_query = data["message"]["content"]
                else:
                    predict_query = data["message"]
                predict_query = llm_output_process(predict_query, model_name)
                # TP_n, FP_n, FN_n
                # 将 tp, fp, fn更新到原本的数据上
                print(single_eval_res_file)
                old_data = json.loads(single_eval_lines[index])
                if data["sql_id"] != old_data["sql_id"]:
                    print(data["sql_id"])
                    print(data["sql_id"] + " not match.")
                    continue
                old_data["TP"], old_data["FP"], old_data["FN"] = dm_caculator.compute_tp_fn_fp_per_task(data["sql_id"],predict_query,db)
                if old_data["FP"] >=6:
                    old_data["FP"] = 5
                modified_data.append(old_data)
                print('---------------------')
            with open(single_eval_res_file, "w", encoding="utf-8") as w:
                for item in modified_data:
                    json.dump(item, w)
                    w.write('\n')
    # # ka
    for db in dbs:
        gold = os.path.join("bird-dlbench", f"bird-{db}.json")
        output_dic = os.path.join("Output-ka", db)
        for pred in os.listdir(output_dic):
            model_name = pred.replace(f"bird-{db}-result-", "").replace(".jsonl", "")
            evaluate_res_dic = os.path.join("evaluation_results-ka", db, model_name)
            single_eval_res_file = os.path.join(evaluate_res_dic, "single_eval_res.jsonl")
            eval_res_file = os.path.join(evaluate_res_dic, "eval_res.json")

            # 遍历output内的数据
            modified_data = []
            with open(os.path.join(output_dic, pred), "r", encoding="utf-8") as r:
                output_lines = r.readlines()
            with open(single_eval_res_file, "r", encoding="utf-8") as r:
                single_eval_lines = r.readlines()
            for index, output_line in enumerate(output_lines):
                data = json.loads(output_line)
                if index >= len(single_eval_lines):
                    # print(single_eval_res_file)
                    # print(data["sql_id"])
                    # print(data["sql_id"] + " 超出index")
                    continue
                if type(data["message"]) == dict and "content" in data["message"]:
                    predict_query = data["message"]["content"]
                else:
                    predict_query = data["message"]
                predict_query = llm_output_process(predict_query, model_name)
                # TP_n, FP_n, FN_n
                # 将 tp, fp, fn更新到原本的数据上
                print(single_eval_res_file)
                old_data = json.loads(single_eval_lines[index])
                if data["sql_id"] != old_data["sql_id"]:
                    print(data["sql_id"])
                    print(data["sql_id"] + " not match.")
                    continue
                old_data["TP"], old_data["FP"], old_data["FN"] = dm_caculator.compute_tp_fn_fp_per_task(data["sql_id"],predict_query,db)
                if old_data["FP"] >=6:
                    old_data["FP"] = 5
                modified_data.append(old_data)
                print('---------------------')
            with open(single_eval_res_file, "w", encoding="utf-8") as w:
                for item in modified_data:
                    json.dump(item, w)
                    w.write('\n')

def test_suites_evaluate(dataset_name):
    dbs = [
        'clickhouse',
        'duckdb',
        'monetdb',
        'postgresql',
        'mariadb',
    ]

    dbs = [
        "clickhouse",
        "duckdb",
        # "mariadb", # 不支持
        # "monetdb", # 不支持
        "mysql",
        "postgresql"
    ]

    # po
    output_dic = os.path.join(f"{dataset_name}-Output")
    for db in dbs:
        gold = os.path.join(dataset_name, "dataset-processed", f"{db}.json")
        pred_files = os.listdir(os.path.join(output_dic, db))
        for pred in pred_files:
            model_name = pred.replace(f"test-suites-{db}-result-", "").replace(".jsonl", "")
            print(model_name)
            evaluate_res_dic = os.path.join(f"{dataset_name}_evaluation_results", db, model_name)
            evaluate(dataset_name, gold, os.path.join(output_dic,db, pred), evaluate_res_dic, model_name)

    # # fs
    # output_dic = os.path.join(f"{dataset_name}-Output-fs")
    # for db in dbs:
    #     gold = os.path.join(dataset_name, "dataset-processed", f"{db}.json")
    #     pred_files = os.listdir(os.path.join(output_dic, db))
    #     for pred in pred_files:
    #         model_name = pred.replace(f"test-suites-{db}-result-", "").replace(".jsonl", "")
    #         print(model_name)
    #         evaluate_res_dic = os.path.join(f"{dataset_name}_evaluation_results-fs", db, model_name)
    #         evaluate(dataset_name, gold, os.path.join(output_dic,db, pred), evaluate_res_dic, model_name)
    #
    # # ka
    # output_dic = os.path.join(f"{dataset_name}-Output-ka")
    # for db in dbs:
    #     gold = os.path.join(dataset_name, "dataset-processed", f"{db}.json")
    #     pred_files = os.listdir(os.path.join(output_dic, db))
    #     for pred in pred_files:
    #         model_name = pred.replace(f"test-suites-{db}-result-", "").replace(".jsonl", "")
    #         print(model_name)
    #         evaluate_res_dic = os.path.join(f"{dataset_name}_evaluation_results-ka", db, model_name)
    #         evaluate(dataset_name, gold, os.path.join(output_dic,db, pred), evaluate_res_dic, model_name)


def test_suites_evaluate_dm(dataset_name):
    dbs = [
        # 'clickhouse', # ok
        # 'duckdb', # ok
        'monetdb',
        # 'mysql', # ok
        # 'mariadb', # ok
        # 'postgresql' # ok
    ]


    dataset_path = os.path.join(dataset_name, "dataset-processed")
    dialect_matching_keyword_filepath = os.path.join("dialect_matching_calculate", "mysql_test_suites_extension_dialect_matching_keywords.json")
    dm_caculator = DMCaculator(dataset_path, dialect_matching_keyword_filepath)

    # po
    for db in dbs:
        output_dic = os.path.join(f"{dataset_name}-Output", db)
        for pred in os.listdir(output_dic):
            model_name = pred.replace(f"test-suites-{db}-result-", "").replace(".jsonl", "")
            evaluate_res_dic = os.path.join(f"{dataset_name}_evaluation_results", db, model_name)
            single_eval_res_file = os.path.join(evaluate_res_dic, "single_eval_res.jsonl")
            eval_res_file = os.path.join(evaluate_res_dic, "eval_res.json")

            # 遍历output内的数据
            modified_data = []
            with open(os.path.join(output_dic, pred), "r", encoding="utf-8") as r:
                output_lines = r.readlines()
            with open(single_eval_res_file, "r", encoding="utf-8") as r:
                single_eval_lines = r.readlines()
            for index, output_line in enumerate(output_lines):
                data = json.loads(output_line)
                if index >= len(single_eval_lines):
                    # print(single_eval_res_file)
                    # print(data["sql_id"])
                    # print(data["sql_id"] + " 超出index")
                    continue
                if type(data["message"]) == dict and "content" in data["message"]:
                    predict_query = data["message"]["content"]
                else:
                    predict_query = data["message"]
                predict_query = llm_output_process(predict_query, model_name)
                # TP_n, FP_n, FN_n
                # 将 tp, fp, fn更新到原本的数据上
                print(single_eval_res_file)
                old_data = json.loads(single_eval_lines[index])
                if data["sql_id"] != old_data["sql_id"]:
                    print(data["sql_id"])
                    print(data["sql_id"] + " not match.")
                    continue
                old_data["TP"], old_data["FP"], old_data["FN"] = dm_caculator.compute_tp_fn_fp_per_task(data["sql_id"],predict_query,db)
                if old_data["FP"] >= 10:
                    old_data["FP"] = 6
                modified_data.append(old_data)
                print('---------------------')
            with open(single_eval_res_file, "w", encoding="utf-8") as w:
                for item in modified_data:
                    json.dump(item, w)
                    w.write('\n')


    # fs
    for db in dbs:
        output_dic = os.path.join(f"{dataset_name}-Output-fs", db)
        for pred in os.listdir(output_dic):
            model_name = pred.replace(f"test-suites-{db}-result-", "").replace(".jsonl", "")
            evaluate_res_dic = os.path.join(f"{dataset_name}_evaluation_results-fs", db, model_name)
            single_eval_res_file = os.path.join(evaluate_res_dic, "single_eval_res.jsonl")
            eval_res_file = os.path.join(evaluate_res_dic, "eval_res.json")

            # 遍历output内的数据
            modified_data = []
            with open(os.path.join(output_dic, pred), "r", encoding="utf-8") as r:
                output_lines = r.readlines()
            with open(single_eval_res_file, "r", encoding="utf-8") as r:
                single_eval_lines = r.readlines()
            for index, output_line in enumerate(output_lines):
                data = json.loads(output_line)
                if index >= len(single_eval_lines):
                    # print(single_eval_res_file)
                    # print(data["sql_id"])
                    # print(data["sql_id"] + " 超出index")
                    continue
                if type(data["message"]) == dict and "content" in data["message"]:
                    predict_query = data["message"]["content"]
                else:
                    predict_query = data["message"]
                predict_query = llm_output_process(predict_query, model_name)
                # TP_n, FP_n, FN_n
                # 将 tp, fp, fn更新到原本的数据上
                print(single_eval_res_file)
                old_data = json.loads(single_eval_lines[index])
                if data["sql_id"] != old_data["sql_id"]:
                    print(data["sql_id"])
                    print(data["sql_id"] + " not match.")
                    continue
                old_data["TP"], old_data["FP"], old_data["FN"] = dm_caculator.compute_tp_fn_fp_per_task(data["sql_id"],predict_query,db)
                if old_data["FP"] >= 10:
                    old_data["FP"] = 6
                modified_data.append(old_data)
                print('---------------------')
            with open(single_eval_res_file, "w", encoding="utf-8") as w:
                for item in modified_data:
                    json.dump(item, w)
                    w.write('\n')
    # # ka
    for db in dbs:
        output_dic = os.path.join(f"{dataset_name}-Output-ka", db)
        for pred in os.listdir(output_dic):
            model_name = pred.replace(f"test-suites-{db}-result-", "").replace(".jsonl", "")
            evaluate_res_dic = os.path.join(f"{dataset_name}_evaluation_results-ka", db, model_name)
            single_eval_res_file = os.path.join(evaluate_res_dic, "single_eval_res.jsonl")
            eval_res_file = os.path.join(evaluate_res_dic, "eval_res.json")

            # 遍历output内的数据
            modified_data = []
            with open(os.path.join(output_dic, pred), "r", encoding="utf-8") as r:
                output_lines = r.readlines()
            with open(single_eval_res_file, "r", encoding="utf-8") as r:
                single_eval_lines = r.readlines()
            for index, output_line in enumerate(output_lines):
                data = json.loads(output_line)
                if index >= len(single_eval_lines):
                    # print(single_eval_res_file)
                    # print(data["sql_id"])
                    # print(data["sql_id"] + " 超出index")
                    continue
                if type(data["message"]) == dict and "content" in data["message"]:
                    predict_query = data["message"]["content"]
                else:
                    predict_query = data["message"]
                predict_query = llm_output_process(predict_query, model_name)
                # TP_n, FP_n, FN_n
                # 将 tp, fp, fn更新到原本的数据上
                print(single_eval_res_file)
                old_data = json.loads(single_eval_lines[index])
                if data["sql_id"] != old_data["sql_id"]:
                    print(data["sql_id"])
                    print(data["sql_id"] + " not match.")
                    continue
                old_data["TP"], old_data["FP"], old_data["FN"] = dm_caculator.compute_tp_fn_fp_per_task(data["sql_id"],predict_query,db)
                if old_data["FP"] >= 10:
                    old_data["FP"] = 6
                modified_data.append(old_data)
                print('---------------------')
            with open(single_eval_res_file, "w", encoding="utf-8") as w:
                for item in modified_data:
                    json.dump(item, w)
                    w.write('\n')

if __name__ == "__main__":
    # bird_evaluate_dm()
    bird_evaluate()

    # test_suites_evaluate_dm("test-suites-extension")
    # test_suites_evaluate("test-suites-extension")




