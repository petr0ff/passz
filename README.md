# passz
Small lib to set Jira Zephyr test executions via ZAPI

## you can:
- change execution status for all test-cases in a given cycle
- change execution status for a particular test-case, by issue key
- change execution status for test-cases with given list of labels

## usage:
- pip install -r requirements.txt
- create config.yml from config.yml.example
- update passz.py with required statuses and labels
- run passz.py
