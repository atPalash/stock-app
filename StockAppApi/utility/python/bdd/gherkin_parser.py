import copy
from gherkin.parser import Parser

def parse(gherkin_string:str):
    """
    Read the whole gherkin formatted @gherkin_string and return the steps in the
    scenarios.

    Args:
        gherkin_string (str): text to read from

    Returns:
        _type_: _description_
    """
    # Create the parser
    parser = Parser()

    # Parse the Gherkin string
    feature = parser.parse(gherkin_string)

    # Access the parsed feature and scenarios
    feature_name = feature['feature']['name']
    scenarios = feature['feature']['children']

    ret = {
        "feature": feature_name,
        "scenarios": {}
    }
    for scene in scenarios:      
        # Check if scenario is a Scenario Outline
        scenario = scene['scenario']
        steps = []
        if len(scenario['examples']) != 0:
            examples = scenario['examples']

            '''
            Search for place holder column wise and replace in the replaced_steps
            1. Take the 1st example row. 20   >   close.
                2. Take the 1st column
                    3. Take the first step, update place holder at col1 ie. window. 
                    4. Repeat step 3 for all steps.
                5. Take the next column
                    6. Repeat step 3,4 with next col.
                7. Update till all columns are updated 
            8. Take the next row
                9. Repeat 2. -> 5 -> 7.
            '''
            for row in examples[0]['tableBody']:
                replaced_steps = copy.deepcopy(scenario['steps'])
                # Replace placeholders in steps with example values
                i = 0
                for col in examples[0]['tableHeader']['cells']:
                    for j in range(len(replaced_steps)):
                        placeholder = "<" + col['value'] + ">"
                        step = str(replaced_steps[j]['text'])
                        replaced_steps[j]['text'] = step.replace(placeholder, row['cells'][i]['value'])
                    i += 1 
                for step in replaced_steps:
                    steps.append(step)

        else:
            for step in scenario['steps']:
                steps.append(step)
        ret["scenarios"][scenario['name']] = steps
    return ret
