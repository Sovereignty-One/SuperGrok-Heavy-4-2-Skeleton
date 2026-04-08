# syntax_guard.py – tiny, offline, no deps except LibCST (pip install libcst)
import libcst as cst
import libcst.matchers as m

class SyntaxGuard:
    def __init__(self):
        pass

    def is_valid(self, code_str):
        try:
            tree = cst.parse_module(code_str)
            # optional: check for specific anti-patterns (e.g., no eval, no requests)
            matcher = m.Module(m.children(m.SimpleStatementLine(...)))
            if not matcher.match(tree):
                return False
            return True
        except Exception:
            return False

    def repair(self, broken_code, max_tries=3):
        # super naive: add parens, fix indents, etc.
        candidates = []
        for i in range(max_tries):
            candidate = f"    {broken_code.replace('def ', 'def ').replace(':', ': ')}"  # dumb indent fix
            if self.is_valid(candidate):
                return candidate
            candidates.append(candidate)
        return None  # fail

# usage:
guard = SyntaxGuard()
raw = "def hello(): print('hi')"
if not guard.is_valid(raw):
    fixed = guard.repair(raw)
    if fixed:
        print("Fixed:", fixed)
    else:
        print("Can't fix. Burn.")
        # q_resist()
# 7.887 rule: no cloud. no exec. no eval. no os.system. no subprocess.
BLACKLIST = [
    m.Call(func=m.Name('eval'), ...),
    m.Call(func=m.Name('exec'), ...),
    m.Call(func=m.Name('subprocess')),
    m.Call(func=m.Name('os.system')),
    m.Call(func=m.Name('requests')),
    m.Call(func=m.Name('urllib')),
    m.Assign(targets= , ...),
    m.Import(alias=m.Alias(value=m.Name('socket'))),
    m.Import(alias=m.Alias(value=m.Name('base64'))),  # if + eval → boom
]
