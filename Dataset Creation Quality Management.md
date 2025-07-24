# Dataset Creation Quality Management

## Annotators

**Annotator Selection.** We recruited trained domain experts with substantial experience in database development and SQL dialects. Before participating in the main annotation phase, each annotator completed a qualification task consisting of 20 SQL translation items sampled from known dialect transformations. Only annotators who achieved at least 90% agreement with the reference annotations were included in the final pool.

**Training. **Qualified annotators received comprehensive training materials, including:

- A detailed annotation guideline,

- Examples of exact vs. approximate semantic equivalence,

- Dialect-specific transformation rules (e.g., LIMIT vs. TOP, function name variations),

**Feedback.** We conducted an onboarding session to walk annotators through sample cases and to answer clarification questions. This ensured consistent understanding of tasks and guidelines. To maintain high annotation quality, annotators received a base compensation plus bonus payments.

| Annotator ID | Years of SQL Experience | Profession        | Specialty Domains                | DBMS Familiarity                                             | Qualification Score |
| ------------ | ----------------------- | ----------------- | -------------------------------- | ------------------------------------------------------------ | ------------------- |
| A01          | 5                       | PhD Student       | Databases                        | MySQL, PostgreSQL, SQLite, MariaDB, MonetDB                  | 95%                 |
| A02          | 3                       | PhD Student       | Databases                        | MySQL, PostgreSQL, SQLite, SQL Server, Oracle                | 97%                 |
| A036         | 5                       | Software Engineer | Telecom, Enterprise Applications | MySQL, PostgreSQL, SQLite, OceanBase , MonetDB, DuckDB, ClickHouse | 92%                 |



## Annotation Process and Quality Estimation

To ensure high-quality annotations of dialect-specific SQL translation tasks in DLBench, we implemented a rigorous multi-step annotation protocol carried out by a team of experienced database practitioners.

**Annotator Assignment and Disagreement Resolution. **Two primary annotators were selected based on their extensive experience and familiarity with the SQL dialects involved (e.g., MySQL, PostgreSQL, SQLite). These annotators were responsible for independently labeling each translation instance. In cases of disagreement, a third author served as an adjudicator, reviewing both annotations and consulting relevant documentation to determine the final label. This triadic setup ensured both domain expertise and annotation consistency.

**Annotation Procedure.** The two primary annotators followed the annotation guidelines to sequentially complete the tasks of **Human Translation** and **SQL Annotation**. During the annotation process, we focused on labeling three complementary types of annotations:

- Semantic Equivalence: Categorized as either exact or approximate equivalence. Approximate equivalence refers to cases where the translated query yields a semantically similar result under practical execution, even if the syntax or operators differ.

- Dialect Location: Specific dialect features within the query (e.g., keywords, operators, syntax variations) were identified and highlighted. For instance, dialect-specific constructs such as LIMIT (MySQL) versus TOP (PostgreSQL) were carefully noted.

- Dialect Knowledge: For each dialect feature identified, the annotators consulted the official documentation of the target DBMS (e.g., MySQL Docs, PostgreSQL Manual) to extract authoritative definitions and usage patterns. When official documentation was incomplete or ambiguous, we used GPT-4o-mini to generate concise summaries or examples. These enriched annotations provide models with a clearer understanding of the functional behavior behind dialect features.

**Consistency and Reliability.** To evaluate annotation reliability, we measured inter-annotator agreement using Cohen’s kappa, which accounts for agreement due to chance. The overall kappa score achieved between the two primary annotators was **0.92**, indicating a high level of consistency and confidence in annotation quality. This result reflects both the clarity of our annotation guidelines and the expertise of our annotators.



## Quality Control

**Validation.** To ensure the reliability, correctness, and consistency of each translation task in DLBench, we design a multi-pronged quality control framework that combines expert validation, guideline refinement, annotator feedback, and selective filtering. Each translation task is validated by three experts. They verify syntactic correctness, semantic equivalence, and proper handling of dialect-specific features using dialect-aware parsers and execution comparisons under identical datasets.

**Manual Correction and Updateing Guidelines.** For incorrect or low-quality translations, the team directly applies manual correction. Difficult cases are escalated to paper' authors. In cases where queries are fundamentally untranslatable—such as using DBMS-specific functions unsupported in the target system—we mark them for exclusion. Similarly, translations with unresolved logic mismatches or ambiguous semantics may be filtered out. When recurring errors or ambiguities are identified, we update the annotation guidelines to improve clarity and coverage. Updated guidelines trigger a re-review of affected annotations to ensure consistency.





## Quality Management in Annotation Process

Figure 3 illustrates the entire process involved in building our benchmark, starting from the collection of databases and SQL statements to the final SQL annotation and quality control steps. Now, we explicitly define the corresponding dataset creation quality management protocols and annotation guidelines to ensure the reliability, reproducibility, and robustness of DLBench.

### 1. Database and Statements Collection

- **Sources**: 
  - *BIRD* Text-to-SQL benchmark, which includes queries from diverse domains such as e-commerce, finance, and healthcare. It covers the SQLite dialect.
  - Popular DBMS test suites like MySQL and PostgreSQL, which contain a variety of SQL dialects and features.
  
- **Quality Management:**
  - The sampling process follows a systematic and scientifically grounded methodology [1]. Selected SQL statements are representative of real-world database systems, featuring complex query structures, nested subqueries, and transactional control operations.
  - The BIRD dataset is a human-annotated corpus widely adopted in the Text-to-SQL research community, with over 500 academic citations. The MySQL and PostgreSQL test suites are recognized as authoritative sources for testing DBMSs.
  - To ensure data integrity [1], we retain complete database context, including schema definitions and example data, which provides a reliable foundation for subsequent SQL translation and evaluation.
### 2. Data Cleaning and Filtering
- **Filtering Process**:
  - SQL statements are filtered to conform to the SQL-92 standard using an *ANTLR* parser.
  - Syntax is checked using a dialect-specific parser, ensuring the queries are executable for the target DBMS.
  - A refined set of SQL statements is prepared for translation.
- **Quality Management:**
  - All statements undergo dual-layer validation, including standard-based parsing and dialect-aware syntax checking, which guarantees that each query is structurally sound and semantically meaningful for its target DBMS.


### 3. Benchmark Construction
- **Translation**:
  - *GPT-4o-mini* is used to translate SQL queries across DBMSs.
  - Human experts verify that the translations are semantically equivalent to the originals.
- **Quality Management:**
  - For queries that fail translation or execution due to dialect incompatibilities (e.g., unsupported functions), human translators rewrite them to ensure benchmark completeness.
  - Throughout the process, schema context, query intent, and execution behavior are documented and preserved for downstream analysis.


### 4. SQL Annotation
- **Annotations**:
  Three labels are assigned to each SQL query:
  - Semantic Equivalent: Identifies whether the queries are approximately or exactly equivalent.
  - Dialect Location: Labels dialect-specific features within the SQL query (e.g., `LIMIT 10`).
  - Dialect Knowledge: Provides external knowledge about the dialect, such as the behavior of SQL functions.
- **Quality Management:**
  - Two primary annotators conduct all annotations following a detailed annotation guideline, with a third expert resolving disagreements to ensure consistency.
  - Annotators consult official documentation (e.g., MySQL and PostgreSQL manuals) to verify the behavior and usage of dialect-specific features. When documentation is unavailable or ambiguous, GPT-4o-mini is used to assist in generating reliable summaries and examples.
  - For ambiguous or complex queries, annotators execute SQL statements in live DBMS environments to empirically verify their semantics, ensuring labels reflect real execution behavior.
  - Inter-annotator agreement is measured using Cohen’s κ, and a score of 0.92 confirms high consistency and annotation reliability.


### 5. Quality Control

- **Review Process**:
  - Three domain experts conduct a comprehensive review of each translation task.
  - They validate syntactic and semantic correctness, ensuring consistency between the source and translated queries.
  - Discrepancies like unsupported functions are resolved through re-translation or manual adjustments.
- **Quality Management:**
  - All translation tasks are double-checked by experts to ensure both syntactic correctness and semantic equivalence.
  - Each query is executed on the target DBMS to confirm it runs successfully and produces results consistent with the source query.
  - Errors such as unsupported functions, incorrect logic, or dialect mismatches are recorded and corrected through re-translation or manual edits.
  - Only translations that pass both execution validation and manual review are included in the final benchmark.




## References

[1] Cao J, Chan Y K, Ling Z, et al. How Should We Build A Benchmark?  Revisiting 274 Code-Related Benchmarks For LLMs[J]. arXiv preprint  arXiv:2501.10711, 2025.