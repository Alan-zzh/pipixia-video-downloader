import subprocess, os, sys

os.chdir(r'c:\Users\Administrator\Desktop\皮皮虾模拟器')

steps = []

def run(name, cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        out = r.stdout + r.stderr
        steps.append(f"=== {name} ===\n{out}\n")
        return r.returncode
    except Exception as e:
        steps.append(f"=== {name} ===\nERROR: {e}\n")
        return -1

run("add", "git add -A")
run("commit", 'git commit -m "v8.0.0: immersive mobile simulator"')
run("log", "git log --oneline -3")
run("push", "git push origin master")

result = "\n".join(steps)
outpath = os.path.join(os.getcwd(), "git_out.txt")
with open(outpath, "w", encoding="utf-8") as f:
    f.write(result)

print("DONE: " + outpath)
sys.stdout.flush()
