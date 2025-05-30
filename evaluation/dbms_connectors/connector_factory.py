from dbms_connectors.implements.clickhouse_connector import ClickHouseConnector
from dbms_connectors.implements.duckdb_connector import DuckDBConnector
from dbms_connectors.implements.monetdb_connector import MonetDBConnector
from dbms_connectors.implements.mysql_connector import MySQLConnector
from dbms_connectors.implements.postgresql_connector import PostgreSQLConnector
from dbms_connectors.implements.sqlite_connector import SqliteConnector


def get_connector_by_dbms_name(db_name: str, **db_config):
    if db_name == "sqlite":
        return SqliteConnector(**db_config)
    elif db_name in ["mysql", "mariadb"]:
        return MySQLConnector(**db_config)
    elif db_name == "postgresql":
        return PostgreSQLConnector(**db_config)
    elif db_name == "clickhouse":
        return ClickHouseConnector(**db_config)
    elif db_name == "duckdb":
        return DuckDBConnector(**db_config)
    elif db_name == "monetdb":
        return MonetDBConnector(**db_config)
    else:
        return SqliteConnector(**db_config)