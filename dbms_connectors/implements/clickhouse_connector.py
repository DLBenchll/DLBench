from datetime import datetime, date
import clickhouse_connect
from clickhouse_connect.driver.client import Client

from dbms_connectors.interfaces.dbms_connector import DbmsConnector


class ClickHouseConnector(DbmsConnector):
    def __init__(self, **db_config):
        """
        :param db_config: 需要包含 host, user, password, database, port（可选）
        """
        self.host = db_config.get('host', 'localhost')
        self.user = db_config.get('user', 'admin')
        self.password = db_config.get('password', '123456')
        self.port = db_config.get('port', 8123)
        self.database_name = db_config.get("database_name", "default")
        if db_config.get("drop_database", True):
            self.drop_database(self.database_name)
            self.create_database(self.database_name)
        super(ClickHouseConnector, self).__init__(**db_config)

    def _create_connection(self):
        self.client = clickhouse_connect.get_client(
            host=self.host,
            port=self.port,
            username=self.user,
            password=self.password,
            database=self.database_name
        )

    def _get_affected_rows_estimate(self, sql: str) -> int:
        """
        粗略估算 INSERT/DELETE/UPDATE 语句影响的行数。
        对于 INSERT，可以尝试解析 VALUES 数量；
        对于 DELETE/UPDATE，可在执行前后做 COUNT 差值（建议用户自己确保语句幂等）。
        """
        sql_lower = sql.strip().lower()
        try:
            if sql_lower.startswith("insert"):
                # 粗略计算插入值的行数（适用于 INSERT INTO ... VALUES (...)）
                values_part = sql[sql_lower.find("values") + len("values"):].strip()
                return values_part.count("(")  # 每个左括号代表一行
            elif sql_lower.startswith("delete") or sql_lower.startswith("update"):
                # 不安全，但可以考虑提取 where 条件构造 count 语句（高风险，仅建议测试用途）
                table = sql.split()[2]
                where_clause = sql_lower.split("where")[1] if "where" in sql_lower else ""
                count_sql = f"SELECT count() FROM {table} WHERE {where_clause}"
                count_result = self.client.query(count_sql)
                return count_result.result_rows[0][0] if count_result.result_rows else -1
        except Exception as e:
            print(f"[Warning] 无法估算影响行数: {e}")
        return -1

    def execute(self, sql):
        sql = sql.replace(";", "")
        result = None
        rowcount = -1
        err = None
        try:
            result = self.client.query(sql)
            if result.result_set:
                return result.result_set, len(result.result_set), err
            else:
                # INSERT / DELETE / UPDATE 语句尝试估算行数
                rowcount = self._get_affected_rows_estimate(sql)
                return [], rowcount, err
        except Exception as e:
            err = str(e)
            print(f"[SQL 执行错误] {e}\n出错语句: {sql}")
        return result, rowcount, err

    def stream_query(self, query_sql, batch_size: int = 100):
        """
        使用 server-side cursor 分批获取数据
        """
        result = self.client.query(query_sql, settings={'max_block_size': batch_size})
        for row in result.result_set:
            yield row

    def stream_query_record_count(self, table_name):
        sql = f"SELECT COUNT(*) FROM {table_name};"
        result, _ = self.execute(sql)
        return result[0][0] if result else 0

    def stream_query_columns(self, table_name, column_names):
        sql = f"SELECT {', '.join(column_names)} FROM {table_name};"
        yield from self.stream_query(sql)

    def get_default_connection(self):
        return clickhouse_connect.get_client(
            host=self.host,
            port=self.port,
            username=self.user,
            password=self.password,
            database="default"
        )

    def create_database(self, database_name):
        """
        创建数据库
        """
        client = self.get_default_connection()
        try:
            client.command(f"CREATE DATABASE IF NOT EXISTS `{database_name}`;")
        except Exception as e:
            print(f"Error creating database {database_name}: {e}")

    def drop_database(self, database_name):
        """
        删除数据库
        """
        client = self.get_default_connection()
        try:
            client.command(f"DROP DATABASE IF EXISTS `{database_name}`;")
        except Exception as e:
            print(f"Error dropping database {database_name}: {e}")
        finally:
            client.close()

    def close(self):
        if self.client:
            self.client.close()
            self.client = None

    def record_to_str(self, record):
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
