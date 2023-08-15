# import re

# text = "1 of 52 week low < close"
# pattern = r'^([-+]?\d*\.\d+) of (\d+) (\w+) (\w+) ([><=!]+) (\w+)$$'
# # pattern = r"\b(?<!\w)\b\s\b(\d+)\b\sstocks"
# match = re.search(pattern, text)

# if match:
#     matched_word = match.group(1)
#     matched_int = match.group(2)
#     print("Match found! The matched word is:", matched_word)
# else:
#     print("No match found")

import re

pattern = r"^([-+]?\d*\.\d+) of (\d+) (\w+) (\w+) ([><=!]+) (\w+)$"
match = re.search(pattern, "1.25 of 52 week low > close")
if match:
    for g in match.groups():
        print(g)

    
