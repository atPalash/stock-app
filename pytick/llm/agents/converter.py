import logging
from pytick.llm.types import State
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage

from pytick.query.steps import StepData
from pytick.utility.utility import get_logger

logger = get_logger(__file__, logging.DEBUG)
step_data = StepData()

def __get_step_options(steps):
    """Get the options for a specific step."""
    ret = {}
    for step, data in steps.items():
        ret[step] = data.variables
    return ret

GIVEN_STEPS = __get_step_options(step_data.given_steps())
WHEN_STEPS = __get_step_options(step_data.when_steps())
THEN_STEPS = __get_step_options(step_data.then_steps())

# Create the system prompt once and cache it
SYSTEM_PROMPT = None

def get_system_prompt():
    """Get the cached system prompt or create it if it doesn't exist."""
    global SYSTEM_PROMPT
    if SYSTEM_PROMPT is None:
        SYSTEM_PROMPT = f"""You are a Gherkin converter agent. Transform user input into proper Gherkin format using the available step definitions below.

AVAILABLE GIVEN STEPS:
{format_steps_for_prompt(GIVEN_STEPS, "Given")}

AVAILABLE WHEN STEPS:
{format_steps_for_prompt(WHEN_STEPS, "When")}

AVAILABLE THEN STEPS:
{format_steps_for_prompt(THEN_STEPS, "Then")}

Instructions:
1. Analyze the user input to understand what they want to test
2. Match their intent to the most appropriate step patterns above
3. Convert their input into a complete Gherkin scenario with Given, When, and Then steps
4. Use the exact step formats shown above
5. Create variables in When steps and use them in Then steps
6. When there are multiple conditions in When, create separate steps on new lines
7. Use "*" at the beginning of additional steps (continuation lines)
8. Always start with a Feature as pytick llm 

Example conversions:
Input: "ema10 > close"
Output:
Feature: pytick llm
Scenario: EMA10 greater than close price analysis
Given stocks from index nifty50
When let ema10 = latest in 1 samples of day close ema 10
* let close = latest in 1 samples of day close
Then list result = tickers with ema10 > close

Input: "sma20 < open"  
Output:
Feature: pytick llm
Scenario: SMA20 less than close price analysis
Given stocks from index nifty50
When let sma20 = latest in 1 samples of day close sma 20
* let open = latest in 1 samples of day open
Then list result = tickers with sma20 < open

Input: "ema10 > close and rsi > 80 and close > 1000"
Output:
Feature: pytick llm
Scenario: Multiple indicator and price analysis
Given stocks from index nifty50
When let ema10 = latest in 1 samples of day close ema 10
* let rsi = latest in 1 samples of day close rsi 14
* let close = latest in 1 samples of day close
Then list result = tickers with ema10 > close and rsi > 80 and close > 1000

Convert the following user input:"""
    return SYSTEM_PROMPT

def converter_agent(state: State, llm: BaseChatModel) -> State:
    """Convert input messages to Gherkin format using available step definitions."""
    messages = state.get('messages', [])
    
    # Check if we already have a system message anywhere in the conversation
    has_system_message = any(isinstance(msg, SystemMessage) for msg in messages)
    
    # Only add system message if it's the first call
    if not has_system_message:
        system_msg = SystemMessage(content=get_system_prompt())
        messages = [system_msg] + messages
    
    # Find the last user message
    last_user_message = None
    for msg in reversed(messages):
        if hasattr(msg, 'type') and msg.type == 'human':
            last_user_message = msg.content
            break
    
    if not last_user_message:
        return state
    
    # Use the full conversation history for context
    reply = llm.invoke(messages)
    
    # Add the assistant's response to the conversation
    updated_messages = messages + [reply]
    
    return {
        **state,
        "messages": updated_messages,
        "gherkin_output": reply.content
    }
    
def format_steps_for_prompt(steps, step_type):
    """Format step definitions for the LLM prompt."""

    def create_step_prompt(step, step_data, step_type):
        place_holders = [r'(.+)', r'(\w+)', r'(\d+)']
        ret = "STEP:\n"
        step_split = step.split()
        for i, part in enumerate(step_split):
            if part in place_holders:
                step_split[i] = "{" + f"option {i}" + "}"
        
        ret = ret + " ".join(step_split) + "\n"
        
        ret += f"AVAILABLE OPTIONS:\n"
        for index, options in step_data.items(): 
            if step_type == "Given":
                ret += f"option {index}:\n- {options[0]}\n"
            elif step_type == "When" or step_type == "Then":
                ret += f"option {index}:\n- {(', ').join(options)}\n"
            else:
                logger
                raise Exception(f"Unknown step type: {step_type}")
        return ret 
    
    if not steps:
        return f"No {step_type} steps available"
    
    formatted_steps = []
    for pattern, step_data in steps.items():
        # Convert regex pattern to human-readable format with better examples
        readable_pattern = pattern.replace(r"^", "").replace(r"$", "")
        step_prompt = create_step_prompt(readable_pattern, step_data, step_type)
        formatted_steps.append(f"{step_prompt}")
    
    return "\n".join(formatted_steps)

if __name__ == "__main__":
    system_prompt = get_system_prompt()
    print(system_prompt)