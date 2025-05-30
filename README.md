# DLBENCH: A Comprehensive Benchmark for SQL Translation with Large Language Models
DLBENCH is a comprehensive benchmark for evaluating the SQL translation capabilities of Large Language Models (LLMs). It contains 6,402 translation tasks across seven popular DBMSs and 9,320 SQL dialects, covering both real-world and diverse synthetic scenarios. The quality and difficulty of DLBENCH are validated through a rigorous multi-step cleaning process and cross-checked by both LLM-based and human annotations. Please check our [Leaderboard](https://dlbenchll.github.io/leaderboard.html) for a visualization of the evaluation results.

## Updates
- 2025-05-30 Publish benchmark and leaderboard

## Benchmark Dataset

DLBENCH includes two comprehensive SQL translation datasets: **BIRDTRANS** and **BUTTERTRANS**. These datasets cover a diverse range of SQL queries across multiple relational DBMS dialects, carefully selected to reflect both real-world and synthetic query scenarios.

The benchmark dataset is accessible at `./datasets`. We provide two types of datasets based on their data sources and dialect coverage:

- **BIRDTRANS**: Derived from the BIRD benchmark (SQLite dialect), containing 3,206 translation tasks across 4,669 dialect variants.
- **BUTTERTRANS**: Collected from official MySQL and PostgreSQL test suites, containing 3,196 translation tasks across 4,651 dialect-specific instances.

Each dataset supports translation to six widely-used open-source DBMSs: **MySQL**, **PostgreSQL**, **MariaDB**, **MonetDB**, **DuckDB**, and **ClickHouse**.

Below is the structure of the dataset directory:
```swift
./datasets/
├── BIRDTrans/
│ ├── mysql.json
│ ├── mariadb.json
│ ├── ...
│ └── schemas/
│ ├──── mysql/
│ ├────── app_store.txt
│ └────── ...
│ └──── ...
│ └──── duckdb/
├── BUTTERTrans/
│ ├── mysql.json
│ ├── monetdb.json
│ ├── ...
│ └── schemas/
│ ├──── mysql/
│ ├────── BUTTERTrans_1.txt
│ └────── ...
│ └──── ...
└ └──── duckdb/
```
Each translation task contains the following fields:

- `sql_id`: The unique identifier for each SQL translation task.
- `database_name`: The name of the database associated with the task, corresponding to a schema file in `./schemas/{source_dbms}/{database_name}.txt`.
- `source_dbms`: The source DBMS name (possible values: `sqlite`, `mysql`, `postgresql`).
- `target_dbms`: The target DBMS name (possible values: `mysql`, `mariadb`, `postgresql`, `clickhouse`, `monetdb`, `duckdb`).
- `source_query`: The original SQL query to be translated.
- `target_query`: The ground truth translated SQL query for the target DBMS.
- `semantic_equivalent_type`: The semantic equivalence type of the translation (`exact_equivalence` or `appr_equivalence`).
- `source_query_dialect_token_positions`: The positions of dialect-specific tokens in the source query.
- `source_dialect_knowledge`: Detailed knowledge of each dialect token in the source DBMS.
- `target_dialect_knowledge`: The corresponding mapping of each dialect token in the target DBMS.
- `source_related_schemas`: Schema information for the source DBMS environment.
- `target_related_schemas`: Schema information for the target DBMS environment.

Here is an example translation task:

```json
{
  "sql_id": "BIRDTrans_1",
  "database_name": "app_store",
  "source_dbms": "sqlite",
  "target_dbms": "clickhouse",
  "source_query": "SELECT CAST(SUM(CASE WHEN SUBSTR('Last Updated', -4) > '2018' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(App) PER FROM playstore WHERE Type = 'Free' AND Rating >= 4.5",
  "target_query": "SELECT SUM(CASE WHEN substring('Last Updated', -4) > '2018' THEN 1 ELSE 0 END) * 100 / COUNT(`App`) AS `PER` FROM `playstore` WHERE `_Type` = 'Free' AND `Rating` >= 4.5;",
  "semantic_equivalent_type": "exact_equivalence",
  "source_query_dialect_token_positions": [
            {
                "dialect_token": "SUBSTR",
                "start_pos": 26,
                "end_pos": 32
            }
        ],
        "source_dialect_knowledge": [
            {
                "feature": "substr(X,Y,Z)substr(X,Y)substring(X,Y,Z)substring(X,Y)",
                "explanation": "The substr(X,Y,Z) function returns a substring of input string X that begins\n  with the Y-th character and which is Z characters long.\n  If Z is omitted then substr(X,Y) returns all characters through the end\n  of the string X beginning with the Y-th.\n  The left-most character of X is number 1.  If Y is negative\n  then the first character of the substring is found by counting from the\n  right rather than the left.  If Z is negative then\n  the abs(Z) characters preceding the Y-th character are returned.\n  If X is a string then characters indices refer to actual UTF-8 \n  characters.  If X is a BLOB then the indices refer to bytes.\n  \n  \"substring()\" is an alias for \"substr()\" beginning with SQLite version 3.34.\n",
                "examples": [
                    "SELECT substr('Hello World', 1, 5); -- Returns 'Hello'",
                    "SELECT substr('Hello World', -5, 3); -- Returns 'Wor'"
                ]
            }
        ],
        "target_dialect_knowledge": [
            {
                "feature": "substring(str, start, length) | substring(str, start)",
                "explanation": "The substring(str, start, length) function extracts a substring from the given string str. It starts at position start and extracts length characters. If length is omitted, the function returns the substring from start to the end of the string. The first character in ClickHouse is indexed as 1, similar to SQLite. If start is negative, it counts from the end of the string.",
                "examples": [
                    "SELECT substring('Hello World', 1, 5); -- Returns 'Hello'",
                    "SELECT substring('Hello World', -5, 3); -- Returns 'Wor'"
                ]
            }
        ],
        "source_related_schemas": [
            "Table: `playstore`\nColumns:\n(`App`, text)\n(`Category`, text)\n(`Rating`, real)\n(`Reviews`, integer)\n(`Size`, text)\n(`Installs`, text)\n(`Type`, text)\n(`Price`, text)\n(`Content Rating`, text)\n(`Genres`, text)\n(`rowid`, integer, primary key)\n"
        ],
        "target_related_schemas": [
            "Table: `playstore`\nColumns:\n(`App`, String)\n(`Category`, String)\n(`Rating`, Float64)\n(`Reviews`, Int64)\n(`Size`, String)\n(`Installs`, String)\n(`_Type`, String)\n(`Price`, String)\n(`Content_Rating`, String)\n(`Genres`, String)\n(`rowid`, Int64, primary key)\n"
        ]
}
```
DLBENCH ensures the dataset's quality through SQL92-based validation, dialect-specific parsing, and both LLM-based and human annotations. For a detailed comparison of LLM performance on these tasks, please visit our [Leaderboard](https://dlbenchll.github.io/leaderboard.html).

## Usage

### Setup

### Inference

### Evaluation

### Submission

## Contributors

## Citation