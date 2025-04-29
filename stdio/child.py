import sys

for line in sys.stdin:
    if "quit" in line.lower():
        print("Quitting...")
        break
    else:
        print(f"Received: {line.strip()}")
        print("record successfully", file=sys.stderr)
