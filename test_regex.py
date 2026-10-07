import re
inputs = ["NaN", "nan", "Infinity", "inf", "1.5", "1.", ".5", "-1", "+1", "", None, float('nan'), float('inf')]
for i in inputs:
    num_match = re.search(r"[-+]?\d*\.\d+|\d+", str(i))
    if num_match:
        try:
            print(f"Input: {repr(i)}, Match: {num_match.group(0)}, Float: {float(num_match.group(0))}")
        except Exception as e:
            print(f"Input: {repr(i)}, Match: {num_match.group(0)}, Float Error: {e}")
    else:
        print(f"Input: {repr(i)}, Match: None")
