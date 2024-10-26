Updated README
text
# Rule Engine with AST

This project implements a simple 3-tier rule engine application using Flask and MongoDB. It allows for the creation, combination, and evaluation of rules based on Abstract Syntax Trees (ASTs).

## Setup

1. Install the required dependencies:
   ```bash
   pip install flask pymongo

Run the Flask application:
bash
python main.py

**COMPONENTS**

1. Backend :  main.py (Flask Python pymongo)
2. Frontend : ui.py (Tkinter UI Python)
3. Automated test script : test.py (Automatically test the app) (requests)


**APP COMPONENTS**

1. CREATE RULE : will create a rule and show id in UI. for eg: you create two rules it will create two rules with id 1 and 2
2. COMBINE RULE: for eg : you add rule number id with comma separated format, it will create a mega rule with separate id on the tkinteR UI
3. EVALUATE RULE : Add the mega rule Id and data params that you need to provide in json format
