import pathlib
p = pathlib.Path("/Users/winnerharry/Naincode AI Dept/projects/ekosistem-satwa-ai/src/sobatpaws/api/auth.py")
content = p.read_text()

# The broken line has unclosed string: "alt_header": "Authorization: Bearer ***
# Fix: close the string with ","
broken = '        "alt_header": "Authorization: Bearer *** = '        "alt_header": "Authorization: Bearer \u003c...e",'

if broken in content:
    content = content.replace(broken, fixed)
    p.write_text(content)
    print("Fixed!")
else:
    print("Pattern not found!")
    lines = content.split("\n")
    for i, l in enumerate(lines, 1):
        if "alt_header" in l:
            print(f"Line {i}: {repr(l)}")
