import subprocess
import os

os.chdir(r'c:\Users\Administrator\Desktop\皮皮虾模拟器')

def run(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout + result.stderr

output = []
output.append("=== git status ===")
output.append(run("git status"))

output.append("=== git add + commit ===")
output.append(run("git add -A"))
output.append(run('git commit -m "v8.0.0: immersive mobile simulator"'))

output.append("=== git log ===")
output.append(run("git log --oneline -3"))

output.append("=== git push ===")
output.append(run("git push origin master 2>&1"))

output.append("=== DONE ===")

with open("git_result.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(output))

print("Results written to git_result.txt")
