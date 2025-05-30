from dbms_connectors.connector_factory import get_connector_by_dbms_name
import os
from Tools.DatabaseConnect.database_connector import run_command
from evaluation_for_DLBench_fs_mariadb import init_database
# mysql_config = {
#     "host": "127.0.0.1",
#     "port": 13306,
#     "user": "root",
#     "password": "123456",
#     "database_name":"app_store",
#     "drop_database": True
# }
# mysql_connector = get_connector_by_dbms_name("mysql", **mysql_config)
# result, rowcount, err = mysql_connector.execute("SELECT;")
#
# print(result)
# print(rowcount)
# print(err)



# mariadb：
# mariadb_config = {
#     "host": "127.0.0.1",
#     "port": 9901,
#     "user": "root",
#     "password": "123456",
#     "database_name":"app_store",
#     "drop_database": True
# }
# connector = get_connector_by_dbms_name("mariadb", **mariadb_config)
# result, rowcount, err = connector.execute("SELECT 1;")
#
# print(result)
# print(rowcount)
# print(err)


#
# postgresql：
# config = {
#     "host": "127.0.0.1",
#     "port": 5432,
#     "user": "postgres",
#     "password": "123456",
#     "database_name":"app_store",
#     "drop_database": True
# }
# connector = get_connector_by_dbms_name("postgresql", **config)
# result, rowcount, err = connector.execute("SELE;")
#
# print(result)
# print(rowcount)
# print(err)


#
# clickhouse：
# config = {
#     "host": "127.0.0.1",
#     "port": 8123,
#     "user": "admin",
#     "password": "123456",
#     "database_name":"app_store",
#     "drop_database": True
# }
# connector = get_connector_by_dbms_name("clickhouse", **config)
# result, rowcount, err = connector.execute("SELECT 1;")
#
# print(result)
# print(rowcount)
# print(err)


#
# monetdb：
# config = {
#     "host": "127.0.0.1",
#     "port": 50000,
#     "user": "monetdb",
#     "password": "monetdb",
#     "database_name":"app_store",
#     "drop_database": True
# }
# connector = get_connector_by_dbms_name("monetdb", **config)
# result, rowcount, err = connector.execute("SELCT 1;")
#
# print(result)
# print(rowcount)
# print(err)


#
# duckdb：
# duckdb_connector = DuckDBConnector(db_path=os.path.join(self.duck_dbfiles, f"{duckdb_database.database_name}.duckdb"))


# init_database("duckdb", "app_store")
# connector = get_connector_by_dbms_name("duckdb", db_path=os.path.join("../bird-dlbench/schemas", f"app_store.duckdb"))
# result, rowcount, err = connector.execute("SHOW TABLES;")
# print(result)
# print(rowcount)
# print(err)



