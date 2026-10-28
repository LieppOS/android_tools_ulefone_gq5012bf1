"""Conservative Blueprint literal-reference discovery, NOT a Soong evaluator."""
import json
import re
from bisect import bisect_right

TOKEN = re.compile(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|[A-Za-z_][\w.]*|\S')


def parse_bp(text, path, diagnostic):
    newlines = [m.start() for m in re.finditer('\n', text)]
    tokens = [(m[0], bisect_right(newlines, m.start()) + 1) for m in TOKEN.finditer(text) if not m[0].startswith(('//', '/*'))]
    modules = []
    i = 0
    while i + 1 < len(tokens):
        kind, line = tokens[i]
        if tokens[i + 1][0] != '{' or not re.fullmatch(r'\w+', kind):
            i += 1
            continue
        end, depth = i + 2, 1
        while end < len(tokens) and depth:
            if tokens[end][0] == '{':
                depth += 1
            elif tokens[end][0] == '}':
                depth -= 1
            end += 1
        if depth:
            diagnostic('MALFORMED_BP', path, line, 'Unclosed module block')
            break
        props, cursor, unresolved = {}, i + 2, set()
        nested = 0
        while cursor < end - 1:
            tok = tokens[cursor][0]
            if tok == '{': nested += 1
            if tok == '}': nested -= 1
            if nested == 0 and cursor + 2 < end and tokens[cursor + 1][0] == ':':
                value = tokens[cursor + 2][0]
                if value.startswith('"'):
                    vals, finish = [value], cursor + 3
                elif value == '[':
                    finish = cursor + 3
                    while finish < end and tokens[finish][0] != ']': finish += 1
                    vals = [t[0] for t in tokens[cursor + 3:finish] if t[0].startswith('"')]
                    if any(t[0] not in {','} and not t[0].startswith('"') for t in tokens[cursor + 3:finish]):
                        diagnostic('BP_DYNAMIC', path, tokens[cursor][1], tok + ' contains nonliteral entries')
                        unresolved.add(tok)
                    finish += 1
                else:
                    if value not in {'true', 'false', '{'}:
                        unresolved.add(tok)
                        diagnostic('BP_DYNAMIC', path, tokens[cursor][1], tok + ' nonliteral value unresolved')
                    cursor += 1
                    continue
                if finish < end and tokens[finish][0] == '+':
                    diagnostic('BP_DYNAMIC', path, tokens[cursor][1], tok + ' concatenation unresolved')
                    unresolved.add(tok)
                try:
                    props[tok] = [json.loads(v) for v in vals]
                except ValueError:
                    diagnostic('MALFORMED_BP', path, line, 'Invalid string literal')
            cursor += 1
        if props.get('name'):
            modules.append(dict(name=props['name'][0], kind=kind, source=path, line=line,
                                stem=(props.get('stem') or props['name'])[0], properties=props,
                                unresolved_properties=sorted(unresolved)))
        i = end
    return modules
