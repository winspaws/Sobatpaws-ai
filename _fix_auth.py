import sys
path = "/Users/winnerharry/Naincode AI Dept/projects/ekosistem-satwa-ai/src/sobatpaws/api/auth.py"
content = open(path).read()
old = 'alt_header": "Authorization: Bearer '
new = 'alt_header": "Authorization: Bearer \u003ckey\u003e",'
content = content.replace(old, new)
open(path, "w").write(content)
print("Fixed!")
