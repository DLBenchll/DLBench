import psycopg2
from datetime import datetime, date

from dbms_connectors.interfaces.dbms_connector import DbmsConnector


class PostgreSQLConnector(DbmsConnector):
    def __init__(self, **db_config):
        """
        :param db_config: 需要包含 host, user, password, database, port(可选)
        """
        self.conn = None
        self.host = db_config.get('host', 'localhost')
        self.user = db_config['user']
        self.password = db_config['password']
        self.database_name = db_config["database_name"]
        self.port = db_config.get('port', 5432)
        if db_config.get("drop_database", True):
            self.drop_database(database_name=db_config["database_name"])
            self.create_database(database_name=db_config["database_name"])
        super(PostgreSQLConnector, self).__init__(**db_config)

    def _create_connection(self):
        if self.conn is not None:
            self.conn.close()
        self.conn = psycopg2.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database_name,
            port=self.port
        )

    def _get_autocommit_connection(self):
        """
        返回一个 autocommit 模式的连接（连接到 postgres 管理数据库）
        """
        conn = psycopg2.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database='postgres',  # 使用管理数据库
            port=self.port
        )
        conn.set_session(autocommit=True)
        return conn

    def execute(self, sql):
        """
        执行 SQL 语句，返回执行结果和影响的行数（支持 SELECT、INSERT、UPDATE、DELETE 等）
        """
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
            err = None
        except Exception as e:
            err = str(e)
            print(f"[SQL 执行错误] {e}\n出错语句: {sql}")
            # self.conn.rollback()
            # raise e
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

    def create_database(self, database_name):
        """
        创建数据库（如果不存在）
        """
        conn = self._get_autocommit_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(f"CREATE DATABASE {database_name};")
        except Exception as e:
            print(f"Error creating database: {e}")
        finally:
            cursor.close()
            conn.close()

    def drop_database(self, database_name):
        """
        删除数据库
        """
        conn = self._get_autocommit_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(f"DROP DATABASE IF EXISTS {database_name};")
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