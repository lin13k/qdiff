#qDiff
##Overview
A tool for finding the difference between multiple data sources which are supposed to be the same.

---
##Goals
1. Reducing the efforts required for checking data validation from different source.
1. Reporting the differences to user.
1. Resolving the differences for user basing on input rules.

---
##System architecture
###Architecture

<img src="https://drive.google.com/uc?id=1GzHV_wweiGHNRarZlgLIKfL8TgOqlY5i&authuser=0&export=view">
<a href="https://drive.google.com/open?id=1GzHV_wweiGHNRarZlgLIKfL8TgOqlY5i">link</a>

###Data flow
<img src="https://drive.google.com/uc?id=1rTqiyL6w3TEEVXfZsxA1inN8pERg8vrF&authuser=0&export=view">
<a href="https://drive.google.com/open?id=1rTqiyL6w3TEEVXfZsxA1inN8pERg8vrF">link</a>


###Components
1. Data reader
    * Using ORM framework to read the data
    * Supporting multiple databases and file sources
1. file reader
    * Importing the file into the database, support  DSV(CSV, TSV) and excel
1. Comparator
    
    1. Algorithm.

        given m,n = len(data1),len(data2)
    
    1. Time complexity
    
        Average Case: O(m+n)

        Amortized Worst Case: O(m*n)

    1. Space complexity

        O(m+n)

    1. pseudo code in python

        ```python
        qDiff(data1, data2):
            iter1 = iter(sorted(data1))
            iter2 = iter(sorted(data2))
            temp_dict1 ={}
            temp_dict2 ={}
            item1 = None
            item2 = None
            try:
                while True:
                    item1 = next(iter1)
                    item2 = next(iter2)
                    h1 = hash(item1)
                    h2 = hash(item2)
                    if h1==h2:
                        item1 = None
                        item2 = None
                        continue
                    if h1 in temp_dict2:
                        temp_dict2.pop(h1)
                        saveToConflictedResult(temp_dict2.values())
                    elif h2 in temp_dict1:
                        temp_dict1.pop(h2) 
                        saveToConflictedResult(temp_dict1.values())
                    else:
                        temp_dict1[h1]=item1
                        temp_dict2[h2]=item2
                    item1 = None
                    item2 = None
            except StopIteration as e:
                if not item1:
                    saveToConflictedResult(list(iter2))
                else:
                    saveToConflictedResult([item1] + list(iter1))
        ```


1. Rule parser
    * Parsing the input rules and save as rule set for reuse

1. Report viewer
    * Providing the comparison result    
    * GUI for accepting rules for resolving (phase 3)

1. Conflict resolver
    * Filtering the conflicted results basing on the input rules

---

##Milestone
###Development
| phase | timeline | items
---|---|---
1 | Week 2 | Data reader, file reader, comparator
2 | Week 4 | Report viewer
3 | Week 6 | Rule parser, conflict resolver

###SIT
| phase | timeline | items
---|---|---
1 | Week 3 | Data reader, file reader, comparator
2 | Week 5 | Report viewer
3 | Week 7 | Rule parser, conflict resolver

###CAT/UAT
| phase | timeline | items
---|---|---
1 | Week 4 | Data reader, file reader, comparator
2 | Week 6 | Report viewer
3 | Week 8 | Rule parser, conflict resolver

---
##Scenarios
1. Comparing tables within same database
1. Comparing tables from different databases
1. Comparing tables with different range of data within same/different database
1. Comparing table and CSV file
1. Comparing unordered CSV file and database 
---

##ERD
###entities	
1. Task

    * Information of datasource
    * Uploaded file path
    * Database information (encryption required, use what as secret key, what as salt) 
    * Datetime

        Recording the start time and end time for performance evaluation
    * Owner 

1. Conflict record
    * Raw data
    * What source it belongs to
1. Rule set
    * Name 
    * Description
1. Rule
    * Formatted rule