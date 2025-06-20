import argparse
import json
import os
from tqdm import tqdm

from app.db_drivers import driver_builder
from app.models import model_builder
from app.utils.data_handler import load_dataset, load_few_shot_examples
from app.utils.logger_util import get_logger
from app.utils.metrics_calculator import calculate_metrics
from app.utils.testcase_executor import execute_query


def evaluate(model, dataset, schema_dir_path, db_drivers, output_dir, use_fs, use_ka, few_shots_dir, dm_matching_keywords, resume=False):
    logger_ = get_logger()
    result = None

    def single_infer(item_):
        try:
            few_shot_examples = None
            if use_fs and few_shots_dir:
                few_shot_examples = load_few_shot_examples(few_shots_dir, item_["source_dbms"], item_["target_dbms"])

            logger_.info(f"[{item_['sql_id']}] Translating from {item_['source_dbms']} to {item_['target_dbms']}...")

            predicted_query, raw_response = model.translateSQL(item_, use_fs, use_ka, few_shot_examples)

            logger_.info(f"[{item_['sql_id']}] Source query: {item_['source_query']}")
            logger_.info(f"[{item_['sql_id']}] Translated query: {predicted_query}")

            source_result = execute_query(db_drivers, item_["source_dbms"], item_["database_name"], schema_dir_path, item_["source_query"])
            target_result = execute_query(db_drivers, item_["target_dbms"], item_["database_name"], schema_dir_path, predicted_query)

            logger_.info(f"[{item_['sql_id']}] Query execution completed.")

            return {
                "sql_id": item_["sql_id"],
                "source_dbms": item_["source_dbms"],
                "target_dbms": item_["target_dbms"],
                "source_query": item_["source_query"],
                "predicted_query": predicted_query,
                "source_query_result": source_result,
                "predicted_query_result": target_result,
                "raw_response": raw_response
            }
        except Exception as e_:
            logger_.error(f"[{item_['sql_id']}] Error during inference: {e_}")
            return None

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "output.jsonl")

    running_results = []
    skipping_sql_ids = []

    if resume and os.path.exists(output_path):
        logger_.info(f"Resuming from existing results at {output_path}")
        with open(output_path, "r", encoding="utf-8") as file:
            for line in file:
                pre_item_result = json.loads(line)
                running_results.append(pre_item_result)
                skipping_sql_ids.append(pre_item_result["sql_id"])
        logger_.info(f"Loaded {len(skipping_sql_ids)} existing results. Will skip them.")

    logger_.info(f"Start processing {len(dataset)} queries.")

    with tqdm(total=len(dataset), desc="Evaluating", unit="query") as pbar:
        for item in dataset:
            if item["sql_id"] in skipping_sql_ids:
                pbar.update(1)
                continue

            item_result = single_infer(item)
            if item_result is None:
                pbar.update(1)
                continue

            running_results.append(item_result)
            with open(output_path, "a", encoding="utf-8") as file:
                file.write(json.dumps(item_result, ensure_ascii=False) + "\n")

            pbar.update(1)

    logger_.info("All queries processed. Calculating metrics...")

    eval_result = calculate_metrics(dataset, running_results, dm_matching_keywords)

    result_path = os.path.join(output_dir, "eval_result.json")
    with open(result_path, "w", encoding="utf-8") as file:
        json.dump(eval_result, file, ensure_ascii=False, indent=4)

    logger_.info(f"Evaluation completed. Results saved to {result_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="SQL Translation Evaluation Framework")

    parser.add_argument("--model_config_path", type=str, required=True, help="Path to the model configuration file.")
    parser.add_argument("--dataset_path", type=str, required=True, help="Directory containing evaluation dataset.")
    parser.add_argument("--schema_dir_path", type=str, required=True, help="Directory containing schema information.")
    parser.add_argument("--db_config_path", type=str, required=True, help="Path to database config file.")
    parser.add_argument("--dm_matching_keywords_path", type=str, required=True, help="Path to matching keywords file.")
    parser.add_argument("--output_dir", type=str, required=True, help="Directory to save output results.")
    parser.add_argument("--log_file_path", type=str, default="./logs/default.log", help="Path to log file.")
    parser.add_argument("--use_fs", action="store_true", help="Enable few-shot learning.")
    parser.add_argument("--use_ka", action="store_true", help="Enable augmented knowledge.")
    parser.add_argument("--few_shots_dir", type=str, default="", help="Directory of few-shot examples.")
    parser.add_argument("--resume", action="store_true", help="Resume from previous incomplete evaluation.")

    args = parser.parse_args()

    logger = get_logger(args.log_file_path)

    try:
        logger.info("Loading model...")
        model = model_builder.build(args.model_config_path)
        logger.info(f"Model ({model.model_name}) loaded from {args.model_config_path}")

        logger.info("Loading dataset...")
        dataset = load_dataset(args.dataset_path)
        logger.info(f"Loaded {len(dataset)} queries from {args.dataset_path}")

        logger.info("Loading database drivers...")
        db_drivers = driver_builder.build(args.db_config_path)

        logger.info("Loading DM matching keywords...")
        with open(args.dm_matching_keywords_path, "r", encoding="utf-8") as file:
            dm_matching_keywords = json.load(file)

        logger.info("Starting evaluation...")
        evaluate(
            model=model,
            dataset=dataset,
            schema_dir_path=args.schema_dir_path,
            db_drivers=db_drivers,
            output_dir=args.output_dir,
            use_fs=args.use_fs,
            use_ka=args.use_ka,
            few_shots_dir=args.few_shots_dir,
            dm_matching_keywords=dm_matching_keywords,
            resume=args.resume
        )

    except Exception as e:
        logger.error(f"Fatal error during setup or evaluation: {e}")
