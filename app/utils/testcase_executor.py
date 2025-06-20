import os

from app.utils.logger_util import get_logger


def execute_query(db_drivers, dbms_name, database_name, schema_dir_path, query):
    logger = get_logger()
    db_driver = db_drivers[dbms_name]
    try:
        db_driver.init_db(database_name)
        with open(file=os.path.join(schema_dir_path, dbms_name, f"{database_name}.txt"), mode="r",
                  encoding="utf-8") as file:
            for line in file:
                db_driver.execute_sql(line)
    except Exception as e_:
        logger.error(f"Error occurs when initializing {database_name} of {dbms_name}: {e_}")
        return {
            "result": [],
            "row_count": -1,
            "err": f"Error occurs when initializing {database_name} of {dbms_name}: {e_}"
        }

    try:
        raw_result, row_count = db_driver.execute_sql(query)
        if raw_result:
            result_ = [db_driver.row_to_str(row) for row in raw_result]
        else:
            result_ = []
        return {
            "result": result_,
            "row_count": row_count,
            "err": None
        }
    except Exception as e_:
        logger.error(f"Error occurs when executing query in {database_name} of {dbms_name}: {e_}")
        return {
            "result": [],
            "row_count": -1,
            "err": f"Error occurs when executing query in {database_name} of {dbms_name}: {e_}"
        }
