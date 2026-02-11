#Bug.py

def function_with_unclosed_bracket(x):
    if x > 5:
        return x * 2
    else:
        return x + 3 # Missing closing bracket

result = function_with_unclosed_bracket(7)

#Bugfix.py
def function_with_closed_bracket(x):
    if x > 5:
        return x * 2
    else:
        return x + 3

result = function_with_closed_bracket(7)
print(result) # Output: 14
