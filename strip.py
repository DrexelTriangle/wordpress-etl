import re
with open("art.txt", "r") as html:
    content = html.read()
html.close()
match = re.match("(?!Sachin)", content)
print(match.group(0))
