from datetime import datetime, date
from bson import Binary
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dbms_connectors.interfaces.dbms_connector import DbmsConnector


class MongoDBConnector(DbmsConnector):

    def __init__(self, **db_config):
        self.host = db_config.get('host', 'localhost')
        self.port  = db_config.get('port', 27017)
        self.database_name = db_config.get("database_name", "test")
        if db_config.get("drop_database", True):
            self.drop_database(self.database_name)
        super(MongoDBConnector, self).__init__(**db_config)
    def _create_connection(self):
        """
        建立 MongoDB 连接
        """
        self.client = MongoClient(f"mongodb://{self.host}:{self.port}")
        self.db = self.client[self.database_name]

    def execute(self, sql):
        """
        查询指定 collection 的指定字段（非流式）。

        :param sql: dict，格式如下：
            {
                'collection': 'users',             # 必须
                'projection': ['name', 'age'],     # 可选，不指定则返回所有字段
                'filter': {'country': 'USA'}       # 可选，不指定则匹配所有记录
            }
        :return: 查询结果的列表
        """
        if not isinstance(sql, dict):
            raise ValueError("参数 sql 必须是字典格式")

        collection_name = sql.get("collection")
        if not collection_name:
            raise ValueError("必须指定 collection 名称")

        filter_ = sql.get("filter", {})  # 默认为空字典，表示全部匹配
        projection = sql.get("projection")
        if projection is not None:
            projection = {field: 1 for field in projection}

        collection = self.db[collection_name]
        cursor = collection.find(filter_, projection)

        return list(cursor)
    def stream_query(self, query_sql, batch_size: int = 100):
        """
        query_sql 是一个 (collection_name, query_dict) 元组
        """
        collection_name, query_dict = query_sql
        cursor = self.db[collection_name].find(query_dict, batch_size=batch_size)
        for doc in cursor:
            yield doc

    def stream_query_record_count(self, table_name):
        """
        获取集合中文档总数
        """
        return self.db[table_name].count_documents({})

    def stream_query_columns(self, table_name, column_names):
        """
        返回指定字段
        """
        projection = {col: 1 for col in column_names}
        cursor = self.db[table_name].find({}, projection)
        for doc in cursor:
            yield [doc.get(col, None) for col in column_names]

    def get_connection(self):
        return MongoClient(f"mongodb://{self.host}:{self.port}")

    def create_database(self, database_name):
        """
        MongoDB 会在插入文档时自动创建数据库和集合
        """
        self.db = self.client[database_name]

    def drop_database(self, database_name):
        client = self.get_connection()
        client.drop_database(database_name)
        client.close()

    def close(self):
        if hasattr(self, "client"):
            self.client.close()

    def record_to_str(self, record):
        """
        将一个 MongoDB 文档对象转为字符串（如插入语句中用的 JSON 字符串）
        """
        import json
        def default(o):
            if isinstance(o, (datetime, date)):
                return o.isoformat()
            elif isinstance(o, Binary):
                return f"BinData(0, '{o.base64}')"
            elif isinstance(o, bytes):
                return o.hex()
            return str(o)

        return json.dumps(record, default=default, ensure_ascii=False)
