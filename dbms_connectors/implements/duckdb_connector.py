import os

import duckdb
from datetime import datetime, date
from dbms_connectors.interfaces.dbms_connector import DbmsConnector

class DuckDBConnector(DbmsConnector):
    def __init__(self, **db_config):
        """
        :param db_config: 需要包含数据库文件路径（'db_path'）
        """
        if 'db_path' in db_config:
            self.db_path = db_config['db_path']
        elif 'db_dir' in db_config and 'database_name' in db_config:
            self.db_path = os.path.join(db_config['db_dir'], f"{db_config['database_name']}.duckdb")
        else:
            self.db_path = ":memory:"

        # print(self.db_path)
        if db_config.get('drop_database', True):
            self.drop_database(self.db_path)
        super(DuckDBConnector, self).__init__(**db_config)

    def _create_connection(self):
        """
        创建与 DuckDB 数据库的连接
        """
        self.conn = duckdb.connect(database=self.db_path)

    def execute(self, sql):
        """
        执行 SQL 语句，返回查询结果（如果有）和影响的行数（或 -1 表示未知）
        """
        result = None
        rowcount = -1
        err = None
        try:
            result = self.conn.execute(sql).fetchall()
            return result, len(result) if result else -1, err
        except Exception as e:
            err = str(e)
            print(f"[SQL 执行错误] {e}\n出错语句: {sql}")
        return result, rowcount, err


    def stream_query(self, query_sql, batch_size: int = 100):
        """
        使用 server-side cursor 分批获取数据
        """
        cur = self.conn.cursor()
        cur.execute(query_sql)
        while True:
            rows = cur.fetchmany(batch_size)
            if not rows:
                break
            for row in rows:
                yield row

    def stream_query_record_count(self, table_name):
        sql = f"SELECT COUNT(*) FROM {table_name};"
        result, _ = self.execute(sql)
        return result[0][0] if result else 0

    def stream_query_columns(self, table_name, column_names):
        sql = f"SELECT {', '.join(column_names)} FROM {table_name};"
        yield from self.stream_query(sql)

    def create_database(self, database_name):
        """
        DuckDB 不支持创建数据库的方式。对于文件数据库，可以在指定路径创建新的数据库。
        """
        # 这里无需手动创建数据库，因为在指定文件路径时会自动创建数据库文件
        pass

    def drop_database(self, db_path):
        """
        删除数据库文件
        """
        import os
        try:
            if os.path.exists(db_path):
                print("remove " + db_path)
                os.remove(db_path)
                # os.remove("D:\\PycharmFiles\\DLBench\\bird-dlbench\\schemas-duckdb\\authors.duckdb")
                # print("D:\\PycharmFiles\\DLBench\\bird-dlbench\\schemas-duckdb\\authors.duckdb")
        except Exception as e:
            print(f"Error dropping database {db_path}: {e}")

    def close(self):
        if hasattr(self, 'conn'):
            self.conn.close()
            self.conn = None

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
            elif isinstance(value, bytes):
                # results.append(str(value))
                results.append(f"'0x{value.hex().upper()}'")
            else:
                results.append(str(value))
        return f"({', '.join(results)})"
