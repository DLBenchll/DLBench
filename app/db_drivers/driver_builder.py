import yaml

from app.db_drivers.basic_drivers import SQLiteDriver, MySQLDriver, PostgreSQLDriver, ClickHouseDriver, MonetDBDriver, \
    DuckDBDriver

support_dbms = {"raw_sqlite", "mysql", "mariadb", "postgresql", "clickhouse", "monetdb", "duckdb"}

def build(dbms_config_path):
    with open(dbms_config_path, "r", encoding="utf-8") as file:
        dbms_config = yaml.safe_load(file)

    if len(support_dbms.intersection(set(dbms_config.keys()))) == 0:
        raise Exception(f"Error loading dbms config from {dbms_config_path}: missing dbms")

    db_drivers = dict()
    if "sqlite" in dbms_config:
        db_drivers["sqlite"] = SQLiteDriver(**dbms_config["sqlite"])
    if "mysql" in dbms_config:
        db_drivers["mysql"] = MySQLDriver(**dbms_config["mysql"])
    if "mariadb" in dbms_config:
        db_drivers["mariadb"] = MySQLDriver(**dbms_config["mariadb"])
    if "postgresql" in dbms_config:
        db_drivers["postgresql"] = PostgreSQLDriver(**dbms_config["postgresql"])
    if "clickhouse" in dbms_config:
        db_drivers["clickhouse"] = ClickHouseDriver(**dbms_config["clickhouse"])
    if "monetdb" in dbms_config:
        db_drivers["monetdb"] = MonetDBDriver(**dbms_config["monetdb"])
    if "duckdb" in dbms_config:
        db_drivers["duckdb"] = DuckDBDriver(**dbms_config["duckdb"])

    return db_drivers