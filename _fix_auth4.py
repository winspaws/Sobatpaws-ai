import pathlib
p = pathlib.Path("/Users/winnerharry/Naincode AI Dept/projects/ekosistem-satwa-ai/src/sobatpaws/api/auth.py")
content = p.read_text()
# The broken line is missing closing quote and comma
old_line = '        "alt_header": "Authorization: Bearer *** = '        "alt_header": "Authorization: Bearer \u003c...
result = content.replace(old_line, new_line)
p.write_text(result)
print("Fixed!")
