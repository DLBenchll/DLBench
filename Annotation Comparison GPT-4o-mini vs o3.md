## **Annotation Comparison: GPT-4o-mini vs o3**

 *Supplementary Document*

To evaluate the impact of LLM choice on annotation quality, we randomly sampled 100 cases and compared the performance of **GPT-4o-mini** and **o3**, following Reviewer#C's suggestion.

### Summary of Results

| Model       | Execution Success Rate | Cases Requiring Manual Fix |
| ----------- | ---------------------- | -------------------------- |
| GPT-4o-mini | 42%                    | 71                         |
| o3      | 52%                    | 65                         |

Notably, o3 showed a higher rate of successful execution, but the success was often superficial—several queries produced incorrect or incomplete results due to misinterpretation of dialect-specific logic.



### **Example: Semantic Divergence Despite Successful Execution (o3)**

- **Source Query (SQLite):**

- ```sql
  SELECT SUBSTR(CAST(T1.start_date AS TEXT), INSTR(T1.start_date, ' '), -4)  
  FROM trip AS T1  
  INNER JOIN station AS T2 ON T2.name = T1.start_station_name  
  WHERE T2.city = 'San Francisco'  
  GROUP BY T1.start_station_name  
  ORDER BY COUNT(T1.id) DESC  
  LIMIT 1;
  ```

  **Expected Semantic Meaning from SQL documentation:**
   Extract the **year** component (last 4 characters) from the time part of `start_date`.

- o3 Translation (MySQL):

- ```sql
  SELECT MAX(SUBSTR(CAST(`T1`.`start_date` AS CHAR), INSTR(`T1`.`start_date`, ' ') - 4, 4))  
  FROM `trip` AS `T1`  
  INNER JOIN `station` AS `T2` ON `T2`.`name` = `T1`.`start_station_name`  
  WHERE `T2`.`city` = 'San Francisco'  
  GROUP BY `T1`.`start_station_name`  
  ORDER BY COUNT(`T1`.`id`) DESC  
  LIMIT 1;
  ```

  **Execution Result:**
   `{"('2014')"}`

**Semantic Issue:**
 While executable, the MySQL translation misinterprets the SUBSTR behavior.

- In **SQLite**, `SUBSTR(..., start, -4)` means “take up to the 4th character from the end”.
- In **MySQL**, `SUBSTR(..., pos, 4)` means “take 4 characters to the right from pos”.
   This leads to a fundamentally different substring range and logic.
