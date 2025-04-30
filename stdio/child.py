import sys

for line in sys.stdin:
    if "quit" in line.lower():
        print("Quitting...")
        break
    else:
        print(f"Received: {line.strip()}")  # stdout
        print("No error", file=sys.stderr)  # stderr
