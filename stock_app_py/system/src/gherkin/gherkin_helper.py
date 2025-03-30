from stock_app_py.utility.src import gherkin_parser, logger


def merge_gherkin_list(gherkins: dict, scenario: str) -> str:
    merged_query = f"""Feature: v2\nScenario: {scenario}\n"""
    nodes = {"Given": [], "When": [], "Then": []}
    conjunction_keyword = ["And", "*"]
    for gid, gherkin in gherkins.items():
        check = gherkin_parser.parse(gherkin_string=gherkin)
        # It is possible to have 1 scenario per query
        feature = check["feature"]
        scenario = next(iter(check["scenarios"]))
        # Make user name the scenario, unnamed scenario may causes issues
        if scenario != "" and feature == "v2":
            current_keyword = ""
            for step in check["scenarios"][scenario]:
                keyword = step["keyword"].strip()
                step_text = step["text"]
                if keyword == "Given" or (
                    current_keyword == "Given" and keyword in conjunction_keyword
                ):
                    current_keyword = "Given"
                elif keyword == "When" or (
                    current_keyword == "When" and keyword in conjunction_keyword
                ):
                    current_keyword = "When"
                elif keyword == "Then" or (
                    current_keyword == "Then" and keyword in conjunction_keyword
                ):
                    current_keyword = "Then"
                else:
                    logger.error(f"{keyword} not allowed")

                if step_text not in nodes[current_keyword]:
                    # need to re-id list tickers since bear and bull for multiple
                    # can be same
                    if current_keyword == "Then":
                        temp = step_text.split(" ")
                        command = temp[0]
                        id = temp[1]
                        if command == "list":
                            id = f"{id}_{gid}"
                            temp[1] = id
                        step_text = " ".join(temp)
                    nodes[current_keyword].append(step_text)
    for node, steps in nodes.items():
        new_node = False
        for step in steps:
            append_step = f"{node} {step}\n" if not new_node else f"* {step}\n"
            merged_query += append_step
            new_node = True
    return merged_query
