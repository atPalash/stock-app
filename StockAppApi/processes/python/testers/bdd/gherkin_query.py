from StockAppApi.processes.python.testers.bdd import gherkin_parser
from StockAppApi.processes.python.testers.bdd import steps

# Gherkin string to be parsed
gherkin_string = '''
Feature: Query
    I want to query to get a list of matches
    
    Scenario: filter for ema and ma 
        Given all nifty 50 stocks
        When ema of window <window> is <condition> <rhs>
        And ma of window <window> is <condition> <rhs>
        Then get list of top 20 stocks
        
        Examples:
            | window    | condition     | rhs       |
            | 20        | >             | close     |
            | 60        | >             | close     |
    
    Scenario: check ema
        Given all nifty 50 stocks
        When ema of window 50 is > open
        Then get list of top 10 stocks
        
    Scenario: check ma
        Given all nifty 50 stocks
        When ma of window 100 is > high
        Then get list of top 10 stocks
            
'''

check = gherkin_parser.parse(gherkin_string=gherkin_string)
for scenario in check["scenarios"]:
    for step in check["scenarios"][scenario]:
        print(steps.call_matched(step['text']))
