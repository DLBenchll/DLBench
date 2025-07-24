## Comparision with Existing Benchmarks

The comparison below emphasizes the broader dialect coverage, diverse data sources (including both test suites and real-world queries), detailed dialect annotations, and comprehensive evaluation metrics (including semantic equivalence) offered by **DLBench** and other benchmarks.

| Benchmark                          | Supported Statement Type    | Dialect Numbers | Target       | Supported DBMS                                               |
| ---------------------------------- | --------------------------- | --------------- | ----------------- | ------------------------------------------------------------ |
| **TPC-DS Benchmark**               | DDL, DQL                    | 99              | Workload analysis | Apache Hive                                                  |
| **Text-to-SQL Bench** (e.g., BIRD) | DQL, DDL                    | 660             | Text-to-SQL tasks | SQLite                                                       |
| **SQLProcBench**                   | DQL, DDL, TCL               | 1069            | Workload analysis | T-SQL, PL/pgSQL, PL/SQL                                      |
| **DLBench**                        | DQL, DDL, DML, DCL, TCL, ML | 9,320           | SQL Translation   | MySQL, PostgreSQL, MariaDB, MonetDB, DuckDB, ClickHouse, SQLite |

### Key Features of DLBench:

- **Comprehensive Query Coverage**: DLBench supports a diverse range of SQL statements, including DDL, DQL, DML, DCL, TCL, and other statements. This makes it a versatile benchmark for evaluating SQL translation tasks across different use cases.
- **Massive Dialect Support**: With over 9,000 dialects, DLBench offers extensive dialect coverage, far surpassing the 99 dialects supported by TPC-DS. This ensures that DLBench captures a wide array of dialects, including subtle variations across different DBMSs.
- **Real-World Data Sources**: Unlike some other benchmarks that rely primarily on text-to-sql datasets, DLBench integrates both test suites and real-world queries. This combination ensures that it provides a realistic and comprehensive evaluation of SQL translation tasks.
- **Advanced Evaluation Metrics**: DLBench evaluates **semantic equivalence**, which ensures that the translated queries are not only syntactically correct but also maintain semantic fidelity across different DBMSs. This is crucial for high-quality SQL translation. We also introduce new metrics, **Dialect Matching**, which evaluates the performance of the SQL translation system by measuring how many dialect-specific features are successfully translated from the source dialect to the target dialect.
- **Detailed Dialect Annotation**: DLBench features well-documented dialects, including comprehensive dialect documentation, dialect positions, and other key metadata. These annotations provide valuable insights into the syntax and semantics of various SQL dialects, making DLBench an excellent resource for **model training**. The detailed dialect knowledge can be leveraged to enhance machine learning models, allowing them to better handle different SQL dialects and improve translation accuracy.
- **Explicit Semantic Annotation**: DLBench incorporates manual annotation by experts to verify semantic equivalence, ensuring not only syntactic correctness but also consistency in query behavior across DBMSs. This semantic annotation, which distinguishes DLBench from existing benchmarks, guarantees high-quality evaluation by accounting for dialect-specific representations and behaviors.

DLBench's ability to handle a wide variety of SQL statements and its robust evaluation metrics make it particularly valuable for SQL translation tasks and benchmarking across multiple DBMS platforms.

