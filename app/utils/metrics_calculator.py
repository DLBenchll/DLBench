import re
from collections import Counter

from antlr4 import *

from app.utils.sql_lexer import SqlLexer


def query_clear(query):
    return query.replace("`","").replace(";","").lower().strip()

def tokenize_sql(sql):
    sql = query_clear(sql)
    sql_processed = re.sub(r'\s+', ' ', sql.strip())
    tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*|\d+|[^\s\w]", sql_processed)
    return tokens

def parse_sql(sql):
    input_stream = InputStream(sql)
    lexer = SqlLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    token_stream.fill()
    return token_stream.tokens

def calculate_dm_single(target_dbms, target_query, predicted_query, source_query_dialect_tokens, dm_matching_keywords):
    result = {"TP_n": 0, "FP_n": 0, "FN_n": 0}
    for source_query_dialect_token in source_query_dialect_tokens:
        matching_keywords = dm_matching_keywords[source_query_dialect_token][target_dbms][
            "matching_keyword"] if source_query_dialect_token in dm_matching_keywords else []
        for matching_keyword in matching_keywords:
            if matching_keyword in predicted_query:
                result["TP_n"] += 1
                break
    result["FN_n"] = len(source_query_dialect_tokens) - result["TP_n"]
    gt_sql_tokens = parse_sql(target_query)
    gt_identifiers = {token.text.replace("`", "").replace("\"", "") for token in gt_sql_tokens if
                      token.type == SqlLexer.IDENTIFIER}
    pd_sql_tokens = parse_sql(predicted_query)
    pd_identifiers = {token.text.replace("`", "").replace("\"", "") for token in pd_sql_tokens if
                      token.type == SqlLexer.IDENTIFIER}
    result["FP_n"] = len(pd_identifiers - gt_identifiers)

    return result

def calculate_em_single(target_query, predicted_query):
    tokens1 = tokenize_sql(target_query)
    tokens2 = tokenize_sql(predicted_query)
    return int(tokens1 == tokens2)

def calculate_ex_single(target_query, predicted_query, target_query_result, predicted_query_result):
    if predicted_query_result["err"]:
        ex_bool = False
        exec_able = False
    elif target_query.upper().startswith("SELECT"):
        ex_bool = set(target_query_result["result"]) == set(predicted_query_result["result"])
        exec_able = True
    else:
        ex_bool = predicted_query_result["row_count"] == target_query_result["row_count"]
        exec_able = True
    return {
        "ex_bool": ex_bool,
        "exec_able": exec_able,
        "ex_msg": predicted_query_result["err"]
    }

def calculate_metrics(dataset, predicted_results, dm_matching_keywords):
    dataset_dict = {item["sql_id"]: item for item in dataset}
    total_counter = Counter()
    total_cnt = len(dataset)
    for predicted_result in predicted_results:
        sql_id = predicted_result["sql_id"]
        data_item = dataset_dict[sql_id]
        source_query_dialect_tokens = [item["dialect_token"] for item in data_item["source_query_dialect_token_positions"]]
        target_dbms = data_item["target_dbms"]
        target_query = data_item["target_query"]
        predicted_query = predicted_result["transferred_query"]
        dm_result = calculate_dm_single(target_dbms, target_query, predicted_query, source_query_dialect_tokens, dm_matching_keywords)
        em_result = calculate_em_single(target_query, predicted_query)
        ex_result = calculate_ex_single(target_query, predicted_query, predicted_result["source_query_result"], predicted_result["transferred_query_result"])
        total_counter.update(dm_result)
        total_counter["em"] += em_result
        total_counter["ex"] += int(ex_result["ex_bool"])

    p_dm = total_counter['TP_n'] / (total_counter['TP_n'] + total_counter['FP_n']) if (total_counter['TP_n'] + total_counter['FP_n']) != 0 else 0
    r_dm = total_counter['TP_n'] / (total_counter['TP_n'] + total_counter['FN_n']) if (total_counter['TP_n'] + total_counter['FN_n']) != 0 else 0
    f1_dm = (2*p_dm*r_dm)/(p_dm+r_dm) if (p_dm+r_dm) != 0 else 0
    eval_result = {
        "P_DM": f"{str(p_dm)}({total_counter['TP_n']}/({total_counter['TP_n']}+{total_counter['FP_n']}))" if total_counter['TP_n'] + total_counter['FP_n'] != 0 else 0,
        "R_DM": f"{str(r_dm)}({total_counter['TP_n']}/({total_counter['TP_n']}+{total_counter['FN_n']}))" if total_counter['TP_n'] + total_counter['FN_n'] != 0 else 0,
        "F1_DM": f"{str(f1_dm)}",
        "EM": f"{str(total_counter['em']/total_cnt)}({total_counter['em']}/{total_cnt})",
        "EX": f"{str(total_counter['ex']/total_cnt)}({total_counter['ex']}/{total_cnt})"
    }
    return eval_result