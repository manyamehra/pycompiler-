# compiler/lexer.py

import re
from compiler.tokens import KEYWORDS

# List of token patterns
TOKEN_SPEC = [
    ('NUMBER',     r'\d+'),
    ('IDENTIFIER', r'[A-Za-z_][A-Za-z0-9_]*'),
    ('PLUS',       r'\+'),
    ('MINUS',      r'-'),
    ('STAR',       r'\*'),
    ('SLASH',      r'/'),
    ('EQUALS',     r'='),
    ('LPAREN',     r'\('),
    ('RPAREN',     r'\)'),
    ('NEWLINE',    r'\n'),
    ('SKIP',       r'[ \t]+'),   # Whitespace (to ignore)
    ('MISMATCH',   r'.'),        # Any other character (to flag errors)
]

# Combine all token patterns into a single regex
TOKEN_REGEX = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPEC)


def tokenize(code):
    tokens = []
    line_num = 1

    for match in re.finditer(TOKEN_REGEX, code):
        kind = match.lastgroup
        value = match.group()

        if kind == 'SKIP':
            continue
        elif kind == 'NEWLINE':
            line_num += 1
        elif kind == 'MISMATCH':
            raise SyntaxError(f"Unexpected character '{value}' on line {line_num}")
        elif kind == 'IDENTIFIER' and value in KEYWORDS:
            tokens.append(('KEYWORD', value))
        else:
            tokens.append((kind, value))

    tokens.append(('EOF', ''))  # End of input
    return tokens
