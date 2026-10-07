import traceback

try:
    with open('backend/utils.py', 'r', encoding='utf-8') as f:
        source = f.read()
    compile(source, 'backend/utils.py', 'exec')
    print('Syntax OK')
except SyntaxError as e:
    print(f'SyntaxError at line {e.lineno}, offset {e.offset}: {e.msg}')
    if e.text:
        print(f"Code: {e.text.strip()}")
except Exception as e:
    print('Other error:')
    traceback.print_exc()
