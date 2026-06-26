#!/usr/bin/env python3
"""Find corrupt JSON files."""
import pathlib

for f in sorted(pathlib.Path("data").rglob("*.json")):
    try:
        text = f.read_bytes()
        text.decode("utf-8")
    except UnicodeDecodeError as e:
        print(f"CORRUPT: {f}")
        print(f"  Position: {e.start}")
        print(f"  Hex: {text[max(0,e.start-5):e.start+15].hex()}")
        # Remove the file
        f.unlink()
        print(f"  -> DELETED")
    else:
        # Verify it's valid JSON
        try:
            import json
            json.loads(text)
        except json.JSONDecodeError as e:
            print(f"INVALID JSON: {f} -> {e}")

print("=== DONE ===")
