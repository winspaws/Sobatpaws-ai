import pathlib
p = pathlib.Path("/Users/winnerharry/Naincode AI Dept/projects/ekosistem-satwa-ai/src/sobatpaws/api/auth.py")
content = p.read_text()

# Find the broken line and fix it
lines = content.split("\n")
fixed = False
for i, l in enumerate(lines):
    if "alt_header" in l and not l.rstrip().endswith('",'):
        # Close the string properly
        lines[i] = l.rstrip() + '",'
        fixed = True
        print(f"Fixed line {i+1}: {repr(lines[i])}")

if fixed:
    p.write_text("\n".join(lines))
    print("Done!")
else:
    print("No broken line found")
    for i, l in enumerate(lines):
        if "alt_header" in l:
            print(f"Line {i+1}: {repr(l)}")
