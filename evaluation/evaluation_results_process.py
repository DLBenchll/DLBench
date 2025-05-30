import os
import json
import pandas as pd
from evaluation_for_DLBench import llm_output_process
import re



def merge_evaluation_result(output_path_, evaluation_results_dic_):
    dbs = [
        'mysql',
        'postgresql',
        'mariadb',
        'monetdb',
        'duckdb',
        'clickhouse'
    ]

    models = [
        "sqlcoder-7b",
        "codellama-7b-instruct",
        "deepseek-coder-6.7b-instruct",
        "deepseek-r1-8b-llama-distill-q8_0",
        "gpt-3.5-turbo"
    ]

    all_rows = []  # 存储所有数据块
    empty_row_count = 2  # 不同数据库之间插入空白行数

    for db in dbs:
        json_data = {}

        for model in models:
            evaluate_res_path = os.path.join(evaluation_results_dic_, db, model, "eval_res.json")
            if os.path.exists(evaluate_res_path):
                with open(evaluate_res_path, "r", encoding="utf-8") as r:
                    json_data[model] = json.load(r)
                # 提取并处理 EM、EX
                em = json_data[model]["EM"]
                ex = json_data[model]["EX"]
                em = float(em.split("(")[0])
                ex = float(ex.split("(")[0])
                json_data[model]["EM"] = round(em, 6)
                json_data[model]["EX"] = round(ex, 6)

        if json_data:
            df = pd.DataFrame.from_dict(json_data, orient='index')
            df.index.name = 'model'
            df.reset_index(inplace=True)  # 把 model 作为列

            # 插入 DB 名字作为标题行
            db_title_row = pd.DataFrame([[db] + [""] * (len(df.columns) - 1)], columns=df.columns)
            df_with_title = pd.concat([db_title_row, df], ignore_index=True)

            # 加入结果列表
            all_rows.append(df_with_title)

            # 添加空白行
            for _ in range(empty_row_count):
                all_rows.append(pd.DataFrame([[""] * len(df.columns)], columns=df.columns))

    # 合并所有数据块
    final_df = pd.concat(all_rows, ignore_index=True)

    # 写入 Excel
    with pd.ExcelWriter(output_path_, engine='openpyxl') as writer:
        final_df.to_excel(writer, sheet_name="Evaluation", index=False)

    print(f"✅ 所有评估结果已写入：{output_path_}")

def evaluation_results_process(eval_dic, eval_file):
  db_name = eval_file.replace(f"bird-", "").replace("-result-deepseek-r1-8b-llama-distill-q8_0.jsonl", "")
  if not os.path.exists(os.path.join(eval_dic, eval_file)):
    return
  if os.path.exists(os.path.join("Output", db_name, eval_file)):
    return
  with open(os.path.join(eval_dic,eval_file), "r", encoding="utf-8") as r:
    lines = r.readlines()

  for line in lines:
    data = json.loads(line)
    new_str =  llm_output_process(data["message"]["content"], "deepseek-r1-8b-llama-distill-q8_0")
    data["message"]["content"] = new_str
    print(new_str+"\n")
    with open(os.path.join("Output", db_name, eval_file), "a", encoding="utf-8") as a:
      json.dump(data, a)
      a.write("\n")


def get_numerator_denominator(string):
    numerator=0
    denominator=0
    # 提取括号内的分数表达式
    match = re.search(r'\((.*)\)', string)
    if match:
        fraction_expr = match.group(1)  # e.g. '170/(170+1022)'
        # 按 / 分成分子和分母
        numerator_expr, denominator_expr = fraction_expr.split('/', 1)
        # 去除空格
        numerator_expr = numerator_expr.strip()
        denominator_expr = denominator_expr.strip()
        # 使用 eval 求值
        numerator = eval(numerator_expr)
        denominator = eval(denominator_expr)
    else:
        print("未找到括号内的表达式")
    return numerator, denominator

def merge_overall_translation_performance():
    models = [
        "sqlcoder-7b",
        "codellama-7b-instruct",
        "deepseek-coder-6.7b-instruct",
        "deepseek-r1-8b-llama-distill-q8_0",
        "gpt-3.5-turbo"
    ]
    # evaluation_results, test_suites_evaluation_results
    total_results = {}
    for model in models:
        # 记录分子分母，按照比例算总体的：分子numerator；分母denominator
        p_dm_numerator = 0
        p_dm_denominator = 0
        r_dm_numerator = 0
        r_dm_denominator = 0
        em_numerator = 0
        em_denominator = 0
        ex_numerator = 0
        ex_denominator = 0

        # 处理bird
        evaluation_results_dic = "evaluation_results"
        dbs = os.listdir(evaluation_results_dic)
        for db in dbs:
            eval_res_file = os.path.join(evaluation_results_dic, db, model, "eval_res.json")
            if not os.path.exists(eval_res_file):
                continue
            with open(eval_res_file,"r", encoding="utf-8") as r:
                data = json.load(r)
            # 将dm，em，ex数据解析并加入
            print(data)
            numerator, denominator = get_numerator_denominator(data["P_DM"])
            p_dm_numerator += numerator
            p_dm_denominator += denominator

            numerator, denominator = get_numerator_denominator(data["R_DM"])
            r_dm_numerator += numerator
            r_dm_denominator += denominator

            numerator, denominator = get_numerator_denominator(data["EM"])
            em_numerator += numerator
            em_denominator += denominator

            numerator, denominator = get_numerator_denominator(data["EX"])
            ex_numerator += numerator
            ex_denominator += denominator


        # 处理test suites
        test_suites_evaluation_results_dic = "test-suites-extension_evaluation_results"
        dbs = os.listdir(test_suites_evaluation_results_dic)
        for db in dbs:
            eval_res_file = os.path.join(test_suites_evaluation_results_dic, db, model, "eval_res.json")
            if not os.path.exists(eval_res_file):
                continue
            with open(eval_res_file,"r", encoding="utf-8") as r:
                data = json.load(r)
            # 将dm，em，ex数据解析并加入
            print(data)
            numerator, denominator = get_numerator_denominator(data["P_DM"])
            p_dm_numerator += numerator
            p_dm_denominator += denominator

            numerator, denominator = get_numerator_denominator(data["R_DM"])
            r_dm_numerator += numerator
            r_dm_denominator += denominator

            numerator, denominator = get_numerator_denominator(data["EM"])
            em_numerator += numerator
            em_denominator += denominator

            numerator, denominator = get_numerator_denominator(data["EX"])
            ex_numerator += numerator
            ex_denominator += denominator

        p_dm = p_dm_numerator/p_dm_denominator
        r_dm = r_dm_numerator/r_dm_denominator
        total_results[model]= {
            "P_DM_numerator": p_dm_numerator,
            "P_DM_denominator": p_dm_denominator,
            "R_DM_numerator": r_dm_numerator,
            "R_DM_denominator": r_dm_denominator,
            "EM_numerator": em_numerator,
            "EM_denominator": em_denominator,
            "EX_numerator": ex_numerator,
            "EX_denominator": ex_denominator,
            "F1_DM": (2*p_dm*r_dm)/(p_dm+r_dm),
            "EM": em_numerator/em_denominator,
            "EX": ex_numerator/ex_denominator
        }

    # 保存所有结果
    with open("overall_translation_performance.json", "w", encoding="utf-8") as w:
        json.dump(total_results, w, indent=4)


def BUTTERTRANS_overall_translation_performance():
    models = [
        # "sqlcoder-7b",
        "codellama-7b-instruct",
        "deepseek-coder-6.7b-instruct",
        "deepseek-r1-8b-llama-distill-q8_0",
        "gpt-3.5-turbo",
        "sqlglot"
    ]
    # evaluation_results, test_suites_evaluation_results
    total_results = {}
    for model in models:
        # 记录分子分母，按照比例算总体的：分子numerator；分母denominator
        p_dm_numerator = 0
        p_dm_denominator = 0
        r_dm_numerator = 0
        r_dm_denominator = 0
        em_numerator = 0
        em_denominator = 0
        ex_numerator = 0
        ex_denominator = 0


        # 处理test suites
        test_suites_evaluation_results_dic = "test-suites-extension_evaluation_results"
        dbs = os.listdir(test_suites_evaluation_results_dic)
        for db in dbs:
            if db in ["mariadb", "monetdb"]:
                continue
            eval_res_file = os.path.join(test_suites_evaluation_results_dic, db, model, "eval_res.json")
            # if not os.path.exists(eval_res_file):
            #     continue
            with open(eval_res_file,"r", encoding="utf-8") as r:
                data = json.load(r)
            # 将dm，em，ex数据解析并加入
            print(data)
            numerator, denominator = get_numerator_denominator(str(data["P_DM"]))
            p_dm_numerator += numerator
            p_dm_denominator += denominator

            numerator, denominator = get_numerator_denominator(str(data["R_DM"]))
            r_dm_numerator += numerator
            r_dm_denominator += denominator

            numerator, denominator = get_numerator_denominator(str(data["EM"]))
            em_numerator += numerator
            em_denominator += denominator

            numerator, denominator = get_numerator_denominator(str(data["EX"]))
            ex_numerator += numerator
            ex_denominator += denominator

        p_dm = p_dm_numerator/p_dm_denominator if p_dm_denominator != 0 else 0
        r_dm = r_dm_numerator/r_dm_denominator if r_dm_denominator != 0 else 0
        total_results[model]= {
            "P_DM_numerator": p_dm_numerator,
            "P_DM_denominator": p_dm_denominator,
            "R_DM_numerator": r_dm_numerator,
            "R_DM_denominator": r_dm_denominator,
            "EM_numerator": em_numerator,
            "EM_denominator": em_denominator,
            "EX_numerator": ex_numerator,
            "EX_denominator": ex_denominator,
            "F1_DM": (2*p_dm*r_dm)/(p_dm+r_dm) if p_dm + r_dm != 0 else 0,
            "EM": em_numerator/em_denominator if em_denominator != 0 else 0,
            "EX": ex_numerator/ex_denominator if ex_denominator != 0 else 0
        }

    # 保存所有结果
    with open("overall_BUTTERTRANS_translation_performance.json", "w", encoding="utf-8") as w:
        json.dump(total_results, w, indent=4)

def BIRDTRANS_overall_translation_performance():
    models = [
        "sqlcoder-7b",
        "codellama-7b-instruct",
        "deepseek-coder-6.7b-instruct",
        "deepseek-r1-8b-llama-distill-q8_0",
        "gpt-3.5-turbo",
        "sqlglot"
    ]
    # evaluation_results, test_suites_evaluation_results
    total_results = {}
    for model in models:
        # 记录分子分母，按照比例算总体的：分子numerator；分母denominator
        p_dm_numerator = 0
        p_dm_denominator = 0
        r_dm_numerator = 0
        r_dm_denominator = 0
        em_numerator = 0
        em_denominator = 0
        ex_numerator = 0
        ex_denominator = 0

        # 处理bird
        evaluation_results_dic = "evaluation_results"
        dbs = os.listdir(evaluation_results_dic)
        for db in dbs:
            # if db in ["mariadb", "monetdb"]:
            #     continue
            eval_res_file = os.path.join(evaluation_results_dic, db, model, "eval_res.json")
            if not os.path.exists(eval_res_file):
                continue
            with open(eval_res_file,"r", encoding="utf-8") as r:
                data = json.load(r)
            # 将dm，em，ex数据解析并加入
            print(data)
            numerator, denominator = get_numerator_denominator(str(data["P_DM"]))
            p_dm_numerator += numerator
            p_dm_denominator += denominator

            numerator, denominator = get_numerator_denominator(str(data["R_DM"]))
            r_dm_numerator += numerator
            r_dm_denominator += denominator

            numerator, denominator = get_numerator_denominator(str(data["EM"]))
            em_numerator += numerator
            em_denominator += denominator

            numerator, denominator = get_numerator_denominator(str(data["EX"]))
            ex_numerator += numerator
            ex_denominator += denominator
        p_dm = p_dm_numerator/p_dm_denominator if p_dm_denominator != 0 else 0
        r_dm = r_dm_numerator/r_dm_denominator if r_dm_denominator != 0 else 0
        total_results[model]= {
            "P_DM_numerator": p_dm_numerator,
            "P_DM_denominator": p_dm_denominator,
            "R_DM_numerator": r_dm_numerator,
            "R_DM_denominator": r_dm_denominator,
            "EM_numerator": em_numerator,
            "EM_denominator": em_denominator,
            "EX_numerator": ex_numerator,
            "EX_denominator": ex_denominator,
            "F1_DM": (2*p_dm*r_dm)/(p_dm+r_dm) if p_dm + r_dm != 0 else 0,
            "EM": em_numerator/em_denominator,
            "EX": ex_numerator/ex_denominator
        }

    # 保存所有结果
    with open("overall_BIRDTRANS_translation_performance.json", "w", encoding="utf-8") as w:
        json.dump(total_results, w, indent=4)


output_path = "bird-evaluation_metrics.xlsx"
evaluation_results_dic = "evaluation_results"
merge_evaluation_result(output_path, evaluation_results_dic)

output_path = "bird-evaluation_metrics-fs.xlsx"
evaluation_results_dic = "evaluation_results-fs"
merge_evaluation_result(output_path, evaluation_results_dic)

output_path = "bird-evaluation_metrics-ka.xlsx"
evaluation_results_dic = "evaluation_results-ka"
merge_evaluation_result(output_path, evaluation_results_dic)


output_path = "test-suites-extension-evaluation_metrics.xlsx"
evaluation_results_dic = "test-suites-extension_evaluation_results"
merge_evaluation_result(output_path, evaluation_results_dic)

output_path = "test-suites-extension-evaluation_metrics-fs.xlsx"
evaluation_results_dic = "test-suites-extension_evaluation_results-fs"
merge_evaluation_result(output_path, evaluation_results_dic)

output_path = "test-suites-extension-evaluation_metrics-ka.xlsx"
evaluation_results_dic = "test-suites-extension_evaluation_results-ka"
merge_evaluation_result(output_path, evaluation_results_dic)

merge_overall_translation_performance()
BIRDTRANS_overall_translation_performance()
BUTTERTRANS_overall_translation_performance()
# files = os.listdir("Output/Others")
# for file in files:
#   evaluation_results_process(os.path.join("Output", "Others"), file)