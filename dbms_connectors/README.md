# 一、 模块功能介绍
该模块主要定义了数据库访问的几个接口，用于方便转换逻辑与验证逻辑的设计

模块的文件结构如下：
- `./interfaces`目录下存放接口文件：`dbms_connector.py`，定义了一系列的访问接口（下文介绍）
- `./implements`存放针对各种数据库的实现，如`./implements/sqlite_connector.py`和`./implements/mysql_connector.py`

# 二、 单文件说明
## 1. dbms_connector.py
该接口在初始化方法中已经声明了数据库连接的创建，即：
```python
class dbms_connector:
    def __init__(self, **db_config):
        self.db_config = db_config
        self._create_connection()
```
为了匹配各种数据库，这里将数据库的连接信息封装在`db_config`中传入
> 在实现`mysql`这类数据库的连接时，需要注意：`mysql`的数据库要先创建才能使用，若我要创建针对`TEST`数据库的连接，则需要先连接到其他数据库执行`CREATE DATABASE TEST`语句，然后再创建`TEST`数据库的连接

主要定义了如下八个访问接口：
- `_create_connection(self)`：创建数据库连接
- `execute(self, sql)`：执行单条SQL语句，要求返回：（1）执行结果；（2）影响的行数
- `stream_query(self, query_sql, batch_size: int = 100)`：流式查询，只用于`SELECT`语句，需要传入SQL语句和`batch_size`；可作为迭代器使用，每次迭代返回一行数据
- `stream_query_record_count(self, table_name)`：获取一张表的记录数，需要传入表名
- `stream_query_columns(self, table_name, column_names)`：实现针对一张表的指定列的查询，需要传入表名以及要查询的列名
- `create_database(self, database_name)`：创建数据库
- `drop_database(self, database_name)`：删除数据库
- `close(self)`：关闭数据库连接

> `stream_query(...)`的设计是为了避免一次性将查询结果全部加载到内存中，从而避免内存溢出

# 三、 模块使用说明
该模块主要在转换逻辑（查询sqlite数据库中的数据，用于生成DMLs）和验证逻辑（查询sqlite数据库中的数据和目标数据库中的数据，用于验证转换结果是否正确），关于上述八大访问接口的具体应用的介绍如下：
- `_create_connection(self)`：默认在父类的初始化方法中调用；有需要的话可以在子类中初始化方法中再次调用（例如`mysql_connector.py`中的实现）
- `execute(self, sql)`：执行创建数据库语句、建表语句和插入语句时使用
- `stream_query(self, query_sql, batch_size: int = 100)`：查询数据库中的数据时使用
- `stream_query_record_count(self, table_name)`：在验证逻辑中使用（获取sqlite数据库和目标数据库中表的记录数是否一致）
- `stream_query_columns(self, table_name, column_names)`：在验证逻辑中使用（查询sqlite数据库和目标数据库中表的指定列的数据）
- `create_database(self, database_name)`：在验证逻辑时使用（为验证逻辑创建对应的数据库，这样才可以去执行转换得到的DDLs和DMLs）
- `drop_database(self, database_name)`：验证逻辑完毕后，删除数据库
- `close(self)`：关闭数据库连接

# 四、 模块拓展说明
将该模块拓展到新的数据库时需要注意如下几点：
- 注意实现`mysql`这类数据库的连接时，子类的初始化方法的操作（见上文的注释）
- 请按照流式查询的思路来实现`stream_query(...)`方法（参考已经实现的`sqlite_connector`和`mysql_connector`）