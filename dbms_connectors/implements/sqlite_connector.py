import sqlite3
from datetime import datetime, date

from dbms_connectors.interfaces.dbms_connector import DbmsConnector


class SqliteConnector(DbmsConnector):
    def __init__(self, **db_config):
        self.db_path = db_config['db_path']
        self.conn = None
        super(SqliteConnector, self).__init__(**db_config)

    def _create_connection(self):
        self.conn = sqlite3.connect(self.db_path)

    def execute(self, sql):
        """
            返回执行结果和影响的行数（支持各种SQL语句的执行）
        """
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

    def stream_query(self, query_sql, batch_size: int = 100):
        cursor = self.conn.cursor()
        try:
            cursor.execute(query_sql)
            while True:
                rows = cursor.fetchmany(batch_size)
                if not rows:
                    break
                for row in rows:
                    yield row
        finally:
            cursor.close()

    def stream_query_record_count(self, table_name):
        sql_statement = f"SELECT COUNT(*) FROM {table_name};"
        result, _ = self.execute(sql_statement)
        return result[0][0]

    def stream_query_columns(self, table_name, column_names):
        sql_statement = f"SELECT {', '.join(column_names)} FROM {table_name};"
        yield from self.stream_query(sql_statement)

    def create_database(self, database_name):
        pass

    def drop_database(self, database_name):
        pass

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def record_to_str(self, record):
        # results = list()
        # for value in record:
        #     if value is None:
        #         results.append("NULL")
        #     elif isinstance(value, str):
        #         # 判断其是否可能为datetime类型的字符串
        #         try:
        #             if "." in value:
        #                 dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")  # sqlite中可能存在带毫秒的日期字符串
        #             else:
        #                 dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        #             results.append(f"""'{dt.strftime("%Y-%m-%d %H:%M:%S")}'""")
        #         except Exception:
        #             results.append(f"'{value}'")
        #     elif isinstance(value, datetime):
        #         results.append(f"""'{value.strftime("%Y-%m-%d %H:%M:%S")}'""")
        #     elif isinstance(value, date):
        #         results.append(f"""'{value.strftime("%Y-%m-%d")}'""")
        #     elif isinstance(value, int):
        #         results.append(str(value))
        #     elif isinstance(value, float):
        #         results.append("{:.5f}".format(value))
        #     elif isinstance(value, bytes):
        #         results.append(f"'0x{value.hex().upper()}'")
        #     else:
        #         results.append(str(value))
        # return f"({', '.join(results)})"

        results = list()
        for value in record:
            if value is None:
                results.append("NULL")
            elif isinstance(value, str):
                # 判断其是否可能为datetime类型的字符串
                try:
                    if "." in value:
                        dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")  # sqlite中可能存在带毫秒的日期字符串
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