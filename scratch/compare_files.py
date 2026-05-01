import difflib

with open('c:/PROYECTOS/decrypt-chromium-suite/main.py.bk', 'r', encoding='utf-8') as f:
    bk = f.readlines()
with open('c:/PROYECTOS/decrypt-chromium-suite/main.py', 'r', encoding='utf-8') as f:
    main = f.readlines()

diff = difflib.unified_diff(bk, main, fromfile='main.py.bk', tofile='main.py')
print(''.join(diff))
