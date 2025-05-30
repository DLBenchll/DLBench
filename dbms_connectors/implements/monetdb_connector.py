import math
import subprocess
from pymonetdb import connect
from datetime import datetime, date

from tests.test_control import database_name

from dbms_connectors.interfaces.dbms_connector import DbmsConnector
class MonetDBConnector(DbmsConnector):
    def __init__(self, **db_config):
        """
        :param db_config: 需要包含 host, user, password, database, port(可选)
        """
        self.conn = None
        self.host = db_config.get('host', 'localhost')
        self.user = db_config.get('user', 'monetdb')
        self.password = db_config.get('password', '123456')
        self.database_name = db_config.get('database_name', 'demo')
        self.port = db_config.get('port', 50000)
        if db_config.get("drop_database", True):
            self.drop_database(self.database_name)

        if database_name not in str(run_command(["docker", "exec", "monetdb_QTRAN"] + ["monetdb", "status"])):
            create_databases = [
                ["monetdb", "create", self.database_name],
                ["monetdb", "release", self.database_name],
                ["monetdb", "start", self.database_name]
            ]
            for sql in create_databases:
                if isinstance(sql, list):
                    run_command(["docker", "exec", "monetdb_QTRAN"] + sql)
        else:
            create_databases = [
                ["monetdb", "start", self.database_name]
            ]
            for sql in create_databases:
                if isinstance(sql, list):
                    run_command(["docker", "exec", "monetdb_QTRAN"] + sql)
        super(MonetDBConnector, self).__init__(**db_config)

    def _create_connection(self):
        self.conn = connect(
            username=self.user,
            password=self.password,
            hostname=self.host,
            port=self.port,
            database=self.database_name
        )
        self.conn.set_autocommit(True)

    def execute(self, sql):
        cur = self.conn.cursor()
        try:
            cur.execute(sql)
            results = cur.fetchall()
            # self.conn.commit()
            return results, len(results), None
        except Exception as e:
            # self.conn.rollback()
            return None, cur.rowcount, str(e)
            # raise e
        finally:
            cur.close()

    def stream_query(self, query_sql, batch_size: int = 100):
        cur = self.conn.cursor()
        cur.execute(query_sql)
        while True:
            rows = cur.fetchmany(batch_size)
            if not rows:
                break
            for row in rows:
                yield row
        cur.close()

    def stream_query_record_count(self, table_name):
        sql = f"SELECT COUNT(*) FROM {table_name};"
        result, _ = self.execute(sql)
        return result[0][0] if result else 0

    def stream_query_columns(self, table_name, column_names):
        sql = f"SELECT {', '.join(column_names)} FROM {table_name};"
        yield from self.stream_query(sql)

    def get_default_connection(self):
        return connect(
            username=self.user,
            password=self.password,
            hostname=self.host,
            port=self.port,
            database=self.database_name
        )
    def create_database(self, database_name):
        """
        嵌入式不支持数据库创建，留空。
        """
        pass

    def drop_database(self, db_path):
        """
        删除数据库文件
        """
        container_name = "monetdb_QTRAN"
        # 停止数据库
        try:
            print("试图drop database")
            print(db_path)
            subprocess.run(["docker", "exec", container_name, "monetdb", "stop", db_path])
            subprocess.run(["docker", "exec", container_name, "monetdb", "set", "maintenance=true", db_path])
            subprocess.run(["docker", "exec", container_name, "monetdb", "destroy", "-f", db_path])
            subprocess.run(["docker", "exec", container_name, "monetdb", "status"])
        except Exception as e:
            print(e)
            return
        # subprocess.run(["docker", "exec", container_name, "monetdb", "create", db_path])
        # subprocess.run(["docker", "exec", container_name, "monetdb", "release", db_path])
        # subprocess.run(["docker", "exec", container_name, "monetdb", "start", db_path])


        # conn = self.get_default_connection()
        # cursor = conn.cursor()
        # try:
        #     cursor.execute("SELECT table_name FROM information_schema.tables WHERE is_system = false;")
        #     for (name,) in cursor.fetchall():
        #         cursor.execute(f'DROP TABLE "{name}";')
        #     conn.commit()
        # except Exception as e:
        #     print(f"Error dropping database: {e}")
        # finally:
        #     cursor.close()
        #     conn.close()

    def close(self):
        if hasattr(self, 'conn'):
            self.conn.close()
            self.conn = None

    def record_to_str(self, record):
        results = []
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
                results.append(f"'0x{value.hex().upper()}'")  # 使用 MonetDB 格式的 blob 表达方式
            else:
                results.append(str(value))
        return f"({', '.join(results)})"


def run_command(command, capture_output=True, shell=True):
    """
    执行命令并打印结果。
    :param command: 要执行的命令列表。
    :param capture_output: 是否捕获输出。
    :param shell: 是否通过 shell 执行。
    """
    command_str = ' '.join(command)
    print(f"执行命令: {command_str}")
    result = subprocess.run(
        ["wsl", "-e", "bash", "-c", command_str],  # 使用 wsl -d 指定进入 Ubuntu，展开列表命令
        text=True,  # 以文本模式返回输出
        capture_output=capture_output,  # 捕获标准输出和标准错误
        shell=shell
    )
    """
    result = subprocess.run(
        ["wsl", "-e", "bash", "-c", "cd ~ && " + command_str],  # 使用 wsl -d 指定进入 Ubuntu，展开列表命令
        text=True,  # 以文本模式返回输出
        capture_output=capture_output,  # 捕获标准输出和标准错误
        shell=shell
    )
    """
    print(f"命令输出: {result.stdout}")
    print(f"命令错误: {result.stderr}")
    """
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, command, output=result.stdout, stderr=result.stderr)
    """
    print('---------------------------------------------------')
    return result