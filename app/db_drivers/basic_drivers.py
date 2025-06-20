import math
import os
import sqlite3
from abc import abstractmethod
from datetime import datetime, date

import clickhouse_connect
import duckdb
import psycopg2
import pymysql
from pymonetdb import connect


class DBDriver:
    def __init__(self, **db_config):
        self.db_config = db_config
        self.conn = None

    @abstractmethod
    def init_db(self, database_name):
        pass

    @abstractmethod
    def execute_sql(self, sql):
        pass

    @abstractmethod
    def row_to_str(self, record):
        pass


class SQLiteDriver(DBDriver):
    def __init__(self, **db_config):
        super().__init__(**db_config)
        self.db_path = self.db_config["db_path"]

    def init_db(self, database_name):
        if self.conn:
            self.conn.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.conn = sqlite3.connect(self.db_path)

    def execute_sql(self, sql):
        cursor = self.conn.cursor()
        try:
            cursor.execute(sql)
            if sql.strip().upper().startswith("SELECT"):
                result = cursor.fetchall()
            else:
                result = None
                self.conn.commit()
            rowcount = cursor.rowcount
        finally:
            cursor.close()
        return result, rowcount

    def row_to_str(self, record):
        results = list()
        for value in record:
            if value is None:
                results.append("NULL")
            elif isinstance(value, str):
                try:
                    if "." in value:
                        dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
                    else:
                        dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                    results.append(f"""'{dt.strftime("%Y-%m-%d %H:%M:%S")}'""")
                except Exception:
                    value = value.replace("\\n", "\n").replace("\\r", "\r").replace("\\t", "\t").replace("\\b", "\b")
                    results.append(f"'{value}'")
            elif isinstance(value, datetime):
                results.append(f"""'{value.strftime("%Y-%m-%d %H:%M:%S")}'""")
            elif isinstance(value, date):
                results.append(f"""'{value.strftime("%Y-%m-%d")}'""")
            elif isinstance(value, int):
                results.append(str(value))
            elif isinstance(value, float):
                results.append("{:.6f}".format(value))
            elif isinstance(value, memoryview):
                value = bytes(value)
                results.append(f"'0x{value.hex().upper()}'")
            elif isinstance(value, bytes):
                results.append(f"'0x{value.hex().upper()}'")
            else:
                results.append(str(value))
        return f"({', '.join(results)})"


class MySQLDriver(DBDriver):
    def __init__(self, **db_config):
        super().__init__(**db_config)
        self.host = db_config.get('host', 'localhost')
        self.username = db_config['username']
        self.password = db_config['password']
        self.port = db_config.get('port', 3306)

    def init_db(self, database_name):
        if self.conn:
            self.conn.close()

        _conn = pymysql.connect(
            host=self.host,
            user=self.username,
            password=self.password,
            database="mysql",
            port=self.port,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.Cursor
        )

        try:
            _conn.autocommit(True)
            with _conn.cursor() as _cursor:
                _cursor.execute(f"DROP DATABASE IF EXISTS `{database_name}`;")
                _cursor.execute(f"CREATE DATABASE `{database_name}`;")
        finally:
            _conn.close()

        self.conn = pymysql.connect(
            host=self.host,
            user=self.username,
            password=self.password,
            database=database_name,
            port=self.port,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.Cursor
        )

    def execute_sql(self, sql):
        cursor = self.conn.cursor()
        result = None
        rowcount = -1
        try:
            cursor.execute(sql)
            if sql.strip().upper().startswith("SELECT"):
                result = cursor.fetchall()
            else:
                self.conn.commit()
            rowcount = cursor.rowcount
        finally:
            cursor.close()
        return result, rowcount

    def row_to_str(self, record):
        results = list()
        for value in record:
            if value is None:
                results.append("NULL")
            elif isinstance(value, str):
                try:
                    if "." in value:
                        dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
                    else:
                        dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                    results.append(f"""'{dt.strftime("%Y-%m-%d %H:%M:%S")}'""")
                except Exception:
                    value = value.replace("\\n", "\n").replace("\\r", "\r").replace("\\t", "\t").replace("\\b", "\b")
                    results.append(f"'{value}'")
            elif isinstance(value, datetime):
                results.append(f"""'{value.strftime("%Y-%m-%d %H:%M:%S")}'""")
            elif isinstance(value, date):
                results.append(f"""'{value.strftime("%Y-%m-%d")}'""")
            elif isinstance(value, int):
                results.append(str(value))
            elif isinstance(value, float):
                results.append("{:.6f}".format(value))
            elif isinstance(value, memoryview):
                value = bytes(value)
                results.append(f"'0x{value.hex().upper()}'")
            elif isinstance(value, bytes):
                results.append(f"'0x{value.hex().upper()}'")
            else:
                results.append(str(value))
        return f"({', '.join(results)})"


class PostgreSQLDriver(DBDriver):
    def __init__(self, **db_config):
        super().__init__(**db_config)
        self.host = db_config.get('host', 'localhost')
        self.username = db_config['username']
        self.password = db_config['password']
        self.port = db_config.get('port', 5432)

    def init_db(self, database_name):
        if self.conn:
            self.conn.close()

        _conn = psycopg2.connect(
            host=self.host,
            user=self.username,
            password=self.password,
            database='postgres',
            port=self.port
        )

        try:
            _conn.set_session(autocommit=True)
            with _conn.cursor() as _cursor:
                _cursor.execute(f"DROP DATABASE IF EXISTS {database_name};")
                _cursor.execute(f"CREATE DATABASE {database_name};")
        finally:
            _conn.close()

        self.conn = psycopg2.connect(
            host=self.host,
            user=self.username,
            password=self.password,
            database=database_name,
            port=self.port
        )

    def execute_sql(self, sql):
        cursor = self.conn.cursor()
        result = None
        rowcount = -1
        try:
            cursor.execute(sql)
            if sql.strip().upper().startswith("SELECT"):
                result = cursor.fetchall()
            else:
                result = None
                self.conn.commit()
            rowcount = cursor.rowcount
        finally:
            cursor.close()
        return result, rowcount

    def row_to_str(self, record):
        results = list()
        for value in record:
            if value is None:
                results.append("NULL")
            elif isinstance(value, str):
                try:
                    if "." in value:
                        dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
                    else:
                        dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                    results.append(f"""'{dt.strftime("%Y-%m-%d %H:%M:%S")}'""")
                except Exception:
                    # results.append(f"'{value}'")
                    value = value.replace("\\n", "\n").replace("\\r", "\r").replace("\\t", "\t").replace("\\b", "\b")
                    results.append(f"'{value}'")
            elif isinstance(value, datetime):
                results.append(f"""'{value.strftime("%Y-%m-%d %H:%M:%S")}'""")
            elif isinstance(value, date):
                results.append(f"""'{value.strftime("%Y-%m-%d")}'""")
            elif isinstance(value, int):
                results.append(str(value))
            elif isinstance(value, float):
                results.append("{:.6f}".format(value))
            elif isinstance(value, memoryview):
                value = bytes(value)
                results.append(f"'0x{value.hex().upper()}'")
            elif isinstance(value, bytes):
                results.append(f"'0x{value.hex().upper()}'")
            else:
                results.append(str(value))
        return f"({', '.join(results)})"


class ClickHouseDriver(DBDriver):
    def __init__(self, **db_config):
        super().__init__(**db_config)
        self.host = db_config.get('host', 'localhost')
        self.username = db_config['username']
        self.password = db_config['password']
        self.port = db_config.get('port', 8123)

    def init_db(self, database_name):
        if self.conn:
            self.conn.close()

        _conn = clickhouse_connect.get_client(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            database="default"
        )

        try:
            _conn.command(f"DROP DATABASE IF EXISTS `{database_name}`;")
            _conn.command(f"CREATE DATABASE IF NOT EXISTS `{database_name}`;")
        finally:
            _conn.close()

        self.conn = clickhouse_connect.get_client(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            database=database_name
        )

    def _get_affected_rows_estimate(self, sql: str) -> int:
        sql_lower = sql.strip().lower()
        try:
            if sql_lower.startswith("insert"):
                values_part = sql[sql_lower.find("values") + len("values"):].strip()
                return values_part.count("(")
            elif sql_lower.startswith("delete") or sql_lower.startswith("update"):
                table = sql.split()[2]
                where_clause = sql_lower.split("where")[1] if "where" in sql_lower else ""
                count_sql = f"SELECT count() FROM {table} WHERE {where_clause}"
                count_result = self.conn.query(count_sql)
                return count_result.result_rows[0][0] if count_result.result_rows else -1
        except Exception as e:
            raise Exception(f"Error estimating affected rows: {e}")
        return -1

    def execute_sql(self, sql):
        sql = sql.replace(";", "")
        result = None
        rowcount = -1
        result = self.conn.query(sql)
        if result.result_set:
            return result.result_set, len(result.result_set)
        else:
            rowcount = self._get_affected_rows_estimate(sql)
            return [], rowcount

    def row_to_str(self, record):
        results = list()
        for value in record:
            if value is None:
                results.append("NULL")
            elif isinstance(value, str):
                try:
                    dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                    results.append(f"'{dt.strftime('%Y-%m-%d %H:%M:%S')}'")
                except Exception:
                    value = value.replace("\\n", "\n").replace("\\r", "\r").replace("\\t", "\t").replace("\\b", "\b")
                    results.append(f"'{value}'")
            elif isinstance(value, datetime):
                results.append(f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'")
            elif isinstance(value, date):
                results.append(f"'{value.strftime('%Y-%m-%d')}'")
            elif isinstance(value, int):
                results.append(str(value))
            elif isinstance(value, float):
                results.append("{:.6f}".format(value))
            else:
                results.append(str(value))
        return f"({', '.join(results)})"


class MonetDBDriver(DBDriver):
    def __init__(self, **db_config):
        super().__init__(**db_config)
        self.host = db_config.get('host', 'localhost')
        self.username = db_config['username']
        self.password = db_config['password']
        self.port = db_config.get('port', 50000)
        self.database_name = db_config.get('database_name', 'monetdb')

    def init_db(self, database_name):
        if self.conn:
            self.conn.close()

        self.conn = connect(
            username=self.username,
            password=self.password,
            hostname=self.host,
            port=self.port,
            database=self.database_name
        )

        with self.conn.cursor() as cursor:
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE is_system = false;")
            table_names = cursor.fetchall()
            if len(table_names) > 0:
                for (name,) in table_names:
                    cursor.execute(f'DROP TABLE "{name}";')
                self.conn.commit()

    def execute_sql(self, sql):
        cursor = self.conn.cursor()
        try:
            if sql.lower().startswith("select"):
                cursor.execute(sql)
                results = cursor.fetchall()
                return results, len(results)
            else:
                cursor.execute(sql)
                rowcount = cursor.rowcount
                self.conn.commit()
                return [], rowcount
        finally:
            cursor.close()

    def row_to_str(self, record):
        results = list()
        for value in record:
            if value is None:
                results.append("NULL")
            elif isinstance(value, str):
                value = value.replace("\\n", "\n").replace("\\r", "\r").replace("\\t", "\t").replace("\\b", "\b")
                results.append(f"'{value}'")
            elif isinstance(value, datetime):
                results.append(f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'")
            elif isinstance(value, date):
                results.append(f"'{value.strftime('%Y-%m-%d')}'")
            elif isinstance(value, int):
                results.append(str(value))
            elif isinstance(value, float):
                if math.isnan(value):
                    results.append("NULL")
                else:
                    results.append("{:.6f}".format(value))
            elif isinstance(value, bytes):
                results.append(f"'0x{value.hex().upper()}'")
            else:
                results.append(str(value))
        return f"({', '.join(results)})"

class DuckDBDriver(DBDriver):
    def __init__(self, **db_config):
        super().__init__(**db_config)
        self.db_path = db_config["db_path"]

    def init_db(self, database_name):
        if self.conn:
            self.conn.close()

        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        self.conn = duckdb.connect(database=self.db_path)

    def execute_sql(self, sql):
        result = self.conn.execute(sql).fetchall()
        return result, len(result) if result else -1

    def row_to_str(self, record):
        results = list()
        for value in record:
            if value is None:
                results.append("NULL")
            elif isinstance(value, str):
                try:
                    dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                    results.append(f"'{dt.strftime('%Y-%m-%d %H:%M:%S')}'")
                except Exception:
                    value = value.replace("\\n", "\n").replace("\\r", "\r").replace("\\t", "\t").replace("\\b", "\b")
                    results.append(f"'{value}'")
            elif isinstance(value, datetime):
                results.append(f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'")
            elif isinstance(value, date):
                results.append(f"'{value.strftime('%Y-%m-%d')}'")
            elif isinstance(value, int):
                results.append(str(value))
            elif isinstance(value, float):
                results.append("{:.6f}".format(value))
            elif isinstance(value, bytes):
                results.append(f"'0x{value.hex().upper()}'")
            else:
                results.append(str(value))
        return f"({', '.join(results)})"