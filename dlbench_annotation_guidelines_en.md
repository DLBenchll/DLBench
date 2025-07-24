
# DLBench SQL Annotation Guidelines

To ensure the quality and consistency of SQL dialect translation annotations in DLBench, we design a structured, executable multi-stage annotation workflow, covering annotation types, operational specifications, conflict resolution, and quality assurance mechanisms.

**Disclaimer**: To preserve anonymization and comply with double-blind review requirements, we provide a simplified version of the annotation guidelines. Certain details  have been redacted.

------

## 1. Annotator Roles

- **Primary Annotators (2)**: Independently annotate all tasks, including semantic equivalence judgment, dialect feature identification, and knowledge supplementation.

- **Adjudicator (1)**: Resolves conflicts between annotators by consulting documentation and determining final labels.

- **Expert Validators (3 total)**: Review final annotations to ensure semantic correctness and accurate dialect identification.

| Annotator ID | Years of SQL Experience | Profession        | Specialty Domains                | DBMS Familiarity                                             | Qualification Score |
| ------------ | ----------------------- | ----------------- | -------------------------------- | ------------------------------------------------------------ | ------------------- |
| A01          | 5                       | PhD Student       | Databases                        | MySQL, PostgreSQL, SQLite, MariaDB, MonetDB                  | 95%                 |
| A02          | 3                       | PhD Student       | Databases                        | MySQL, PostgreSQL, SQLite, SQL Server, Oracle                | 97%                 |
| A036         | 5                       | Software Engineer | Telecom, Enterprise Applications | MySQL, PostgreSQL, SQLite, OceanBase, MonetDB, DuckDB, ClickHouse | 92%             |

------

## 2. Annotation Scope and Types

Each numbered folder under `preliminary conversion results` represents a Test Case, containing:

- `mysql.txt`: Cleaned MySQL SQL queries, one per line. Dialect-sensitive queries are annotated using `--`, e.g., `-- ROW`.
- Other `.txt` files (e.g., `mariadb.txt`, `postgresql.txt`) contain GPT-4o's preliminary translations.
- `dialect_info.json`: Stores dialect-specific mapping definitions for the current Test Case.
- `all_dialect_info.json`: Contains the full dialect knowledge base across all cases.

Each SQL pair (MySQL + translated version) requires three annotation types:

### 2.1 Semantic Equivalence

- `Exact`: Fully identical in logic and execution.
- `Approximate`: Slight syntactic differences but logically aligned.
- `Not Equivalent`: Incorrect logic or failure to execute.

**Reference Criteria**:

- Run both queries on the same dataset;
- Compare logic structures and result sets;
- Pay attention to NULL handling, ordering, type casting, etc.

------

### 2.2 Dialect Location

Annotate all dialect-specific SQL elements:

- `feature`: e.g., `LIMIT`, `TOP`, `ILIKE`
- `position`: Code snippet showing usage
- `dbms`: Target DBMS, e.g., `MySQL`, `PostgreSQL`, `ClickHouse`

> Example:

```json
{
  "feature": "LIMIT",
  "position": "LIMIT 10",
  "dbms": "MySQL"
}
```

### 2.3 Dialect Knowledge

For each dialect feature, include:

- `Feature`: Name
- `Explanation`: Formal description
- `Example`: Code snippet

> Example:

```sql
Feature: LIMIT  
Explanation: Used to limit the number of returned rows in MySQL and SQLite.  
Example: SELECT * FROM users LIMIT 5;
```

If documentation is missing, GPT-4o-mini may be used, followed by human validation.

------

## 3. Annotation Workflow

1. Read MySQL and translated SQL with DBMS and schema;
2. Execute both on the same dataset;
3. Label semantic equivalence;
4. Identify dialect features;
5. Complete dialect knowledge entries;
6. Submit to adjudicator, then validator.

### Translation and Correction Policy

✅ 1. Translation Goals

For each DBMS (MariaDB, PostgreSQL, ClickHouse, MonetDB, DuckDB):

- Ensure executable and syntactically valid SQL;
- Strictly apply mappings from `dialect_info.json`;
- Retain MySQL semantics where possible; otherwise ensure syntactic correctness.

✅ 2. Editing MySQL SQL

Permitted only if:

- MySQL test suite still runs correctly;
- All translations are synchronized accordingly.

✅ 3. Untranslatable Cases

Use comments to skip:

```sql
-- Don't support: ROW expressions in MonetDB
```

------

## 4. Conflict Resolution

- Disagreements resolved by adjudicator;
- Must be resolved before validation;
- Documented with references.

------

## 5. Quality Assurance

### 5.1 Inter-Annotator Agreement

- Use **Cohen’s kappa**;
- Kappa ≥ 0.85 = consistent;
- Otherwise, trigger training and guideline updates.

### 5.2 Expert Validation

Check:

- Execution results match;
- Dialect syntax is valid;
- Annotations follow protocol;
- Knowledge entries are accurate.

### 5.3 Manual Corrections

- Fix annotation or translation errors;
- Escalate complex cases;
- Mark unrecoverable cases as excluded.

### 5.4 Guideline Revision

- Update upon systematic errors;
- Re-annotate affected items;
- Retrain annotators if needed.

------

## 6. Common Errors

| Error Type         | Example                                  |
| ------------------ | ---------------------------------------- |
| Wrong logic        | Replacing `NULLIF(a,b)` with `a != b`   |
| Syntax not adapted | Using `LIMIT` in SQL Server             |
| Grouping ignored   | Missing `GROUP BY` / `ORDER BY`         |
| Type casting lost  | Removing `CAST(... AS TEXT)`            |

... ...

## 
