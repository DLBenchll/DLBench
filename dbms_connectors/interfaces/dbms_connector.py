from datetime import datetime, date


class DbmsConnector:
    def __init__(self, **db_config):
        self.db_config = db_config
        self._create_connection()

    def _create_connection(self):
        return NotImplementedError

    def execute(self, sql):
        return NotImplementedError

    def stream_query(self, query_sql, batch_size: int = 100):
        return NotImplementedError

    def stream_query_record_count(self, table_name):
        return NotImplementedError

    def stream_query_columns(self, table_name, column_names):
        return NotImplementedError

    def create_database(self, database_name):
        return NotImplementedError

    def drop_database(self, database_name):
        return NotImplementedError

    def close(self):
        return NotImplementedError

def record_to_str(record):
    raise NotImplementedError