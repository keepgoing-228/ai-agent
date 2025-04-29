import subprocess

proc = subprocess.Popen(["python", "child.py"],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        )


stdout, stderr = proc.communicate(input="hi\n hi again\nquit\n")

# print(stdout)
print(stderr)

