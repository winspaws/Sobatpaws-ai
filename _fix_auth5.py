import pathlib
p = pathlib.Path("/Users/winnerharry/Naincode AI Dept/projects/ekosistem-satwa-ai/src/sobatpaws/api/auth.py")
content = p.read_text()

# Find line with alt_header that doesn't end properly
lines = content.split("\n")
for i, l in enumerate(lines):
    if "alt_header" in l:
        stripped = l.rstrip()
        if not stripped.endswith('",'):
            lines[i] = stripped + '",'
            print(f"Fixed line {i+1}")

p.write_text("\n".join(lines))
print("Done")
