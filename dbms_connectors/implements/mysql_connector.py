from datetime import datetime, date

import pymysql

from dbms_connectors.interfaces.dbms_connector import DbmsConnector


class MySQLConnector(DbmsConnector):
    def __init__(self, **db_config):
        """
        :param db_config: 需要包含 host, user, password, database, port(可选)
        """
        self.conn = None
        self.host = db_config.get('host', 'localhost')
        self.user = db_config['user']
        self.password = db_config['password']
        self.database_name = db_config["database_name"]
        self.port = db_config.get('port', 3306)
        if db_config.get("drop_database", True):
            self.drop_database(database_name=db_config["database_name"])
            self.create_database(database_name=db_config["database_name"])
        super(MySQLConnector, self).__init__(**db_config)

    def _create_connection(self):
        self.conn = pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database_name,
            port=self.port,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.Cursor
        )

    def execute(self, sql):
        """
        返回执行结果和影响的行数（支持各种SQL语句的执行）。
        如果执行出错，返回 None 和 -1，并打印错误信息。
        """
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
            err = None
        except Exception as e:
            err = str(e)
            print(f"[SQL 执行错误] {e}\n出错语句: {sql}")
        finally:
            cursor.close()
        return result, rowcount, err

    def stream_query(self, query_sql, batch_size: int = 100):
        """
        以流式方式查询数据，每次获取 batch_size 条数据
        """
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
        """
        获取表的总行数
        """
        sql_statement = f"SELECT COUNT(*) FROM {table_name};"
        result, _ = self.execute(sql_statement)
        return result[0][0]

    def stream_query_columns(self, table_name, column_names):
        """
        以流式方式查询指定表的指定列
        """
        sql_statement = f"SELECT {', '.join(column_names)} FROM {table_name};"
        yield from self.stream_query(sql_statement)

    def get_default_connection(self):
        """
        获取默认的数据库连接
        """
        return pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database="mysql",
            port=self.port,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.Cursor
        )
    def create_database(self, database_name):
        """
        创建数据库（如果不存在）

        :param database_name: 要创建的数据库名称
        """
        conn = self.get_default_connection()
        cursor = conn.cursor()
        try:
            sql_statement = f"CREATE DATABASE IF NOT EXISTS `{database_name}`;"
            cursor.execute(sql_statement)
        except Exception as e:
            print(f"Error creating database: {e}")
        finally:
            cursor.close()
            conn.close()


    def drop_database(self, database_name):
        """
        删除数据库
        """
        conn = self.get_default_connection()
        cursor = conn.cursor()
        try:
            sql_statement = f"DROP DATABASE IF EXISTS `{database_name}`;"
            # print(sql_statement)
            cursor.execute(sql_statement)
            print(f"drop {database_name} success!")
        except Exception as e:
            print(f"Error dropping database: {e}")
        finally:
            cursor.close()
            conn.close()

    def close(self):
        """
        关闭数据库连接
        """
        if self.conn:
            self.conn.close()
            self.conn = None

    def record_to_str(self, record):
        # results = list()
        # for value in record:
        #     if value is None:
        #         results.append("NULL")
        #     elif isinstance(value, str):
        #         results.append(f"'{value}'")
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