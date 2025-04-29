import sys

input_line = sys.stdin.readline()
print(f"Received input: {input_line}") # stdout
print("error", file=sys.stderr) # stderr