import json
import os
import argparse
import logging

from app.db_drivers import driver_builder
from app.models import model_builder
from app.utils.data_handler import load_input_data, load_few_shot_examples
from app.utils.logger_util import get_logger
from app.utils.testcase_executor import execute_query


def infer(model, input_data, schema_dir_path, db_drivers, output_dir, use_fs, use_ka, few_shots_dir):
    logger_ = get_logger()
    result = None

    def single_infer(item_):
        try:
            few_shot_examples = None
            if use_fs and few_shots_dir != "":
                few_shot_examples = load_few_shot_examples(few_shots_dir, item_["source_dbms"], item_["target_dbms"])
            logger_.info(f"[{item_['sql_id']}] Translating from {item_['source_dbms']} to {item_['target_dbms']}...")
            predicted_query, raw_response = model.translateSQL(item_, use_fs, use_ka, few_shot_examples)
            logger_.info(f"[{item_['sql_id']}] Source query: {item_['source_query']}")
            logger_.info(f"[{item_['sql_id']}] Translated query: {predicted_query}")
            if db_drivers:
                logger_.info(f"Execute transferred query...")
                source_query_result = execute_query(db_drivers, item_["source_dbms"], item_["database_name"], schema_dir_path, item_["source_query"])
                predicted_query_result = execute_query(db_drivers, item_["target_dbms"], item_["database_name"], schema_dir_path, predicted_query)
                logger_.info(f"[{item_['sql_id']}] Query execution completed.")
            else:
                source_query_result, predicted_query_result = None, None

            return {
                "sql_id": item_["sql_id"],
                "source_dbms": item_["source_dbms"],
                "target_dbms": item_["target_dbms"],
                "source_query": item_["source_query"],
                "predicted_query": predicted_query,
                "source_query_result": source_query_result,
                "predicted_query_result": predicted_query_result,
                "raw_response": raw_response
            }
        except Exception as e_:
            logger_.error(f"[{item_['sql_id']}] Error during inference: {e_}")
            return None

    if isinstance(input_data, list):
        result = list()
        for item in input_data:
            item_result = single_infer(item)
            if item_result is None:
                continue
            result.append(item_result)
    elif isinstance(input_data, dict):
        result = single_infer(input_data)
    if output_dir and result:
        output_path = os.path.join(output_dir, "output.json")
        with open(file=os.path.join(output_dir, "output.json"), mode="w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)

        logger_.info(f"Inference completed. Results saved to {output_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_config_path", type=str, help="Filepath of the model configuration.", required=True)
    parser.add_argument("--input_data_path", type=str, help="Filepath of the input data for sql translation.",
                        required=True)
    parser.add_argument("--schema_dir_path", type=str, help="Filepath of the directory which stores the schema information.", required=False)
    parser.add_argument("--db_config_path", type=str, help="Filepath of the database configuration.", required=False)
    parser.add_argument("--output_dir", type=str, help="Filepath of the directory which stores the output data for sql translation.",
                        required=False)
    parser.add_argument("--log_file_path", type=str, help="Filepath of the log file.", default="./logs/default.log", required=False)
    parser.add_argument("--use_fs", action='store_true', help="Whether to use few-shot examples.")
    parser.add_argument("--use_ka", action='store_true', help="Whether to use augmented-knowledge.")
    parser.add_argument("--few_shots_dir", type=str,
                        help="Filepath of the Directory which stores the few-shot examples.", default="",
                        required=False)

    args = parser.parse_args()
    logger = get_logger(args.log_file_path)
    try:
        logger.info("Loading model...")
        model = model_builder.build(args.model_config_path)
        logger.info(f"Model ({model.model_name}) loaded from {args.model_config_path}")

        logger.info("Loading dataset...")
        input_data = load_input_data(args.input_data_path)
        logger.info(f"Input data loaded from {args.input_data_path}.")

        db_drivers = None
        if args.schema_dir_path and args.db_config_path:
            logger.info("Loading database drivers...")
            db_drivers = driver_builder.build(args.db_config_path)

        logger.info("Start inferring...")
        infer(
            model=model,
            input_data=input_data,
            schema_dir_path=args.schema_dir_path,
            db_drivers=db_drivers,
            output_dir=args.output_dir,
            use_fs=args.use_fs,
            use_ka=args.use_ka,
            few_shots_dir=args.few_shots_dir)
    except Exception as e:
        logger.error(f"Fatal error during setup or inference: {e}")