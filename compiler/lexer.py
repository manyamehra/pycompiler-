# compiler/lexer.py

import re
from compiler.tokens import KEYWORDS

# List of token patterns
TOKEN_SPEC = [
    ('tok_NUMBER',     r'\d+'),
    ('tok_IDENTIFIER', r'[A-Za-z_][A-Za-z0-9_]*'),
    ('tok_PLUS',       r'\+'),
    ('tok_MINUS',      r'-'),
    ('tok_STAR',       r'\*'),
    ('tok_SLASH',      r'/'),
    ('tok_EQUALS',     r'='),
    ('tok_LPAREN',     r'\('),
    ('tok_RPAREN',     r'\)'),
    ('tok_NEWLINE',    r'\n'),
    ('tok_SKIP',       r'[ \t]+'),   # Whitespace (to ignore)
    ('tok_MISMATCH',   r'.'),        # Any other character (to flag errors)
]

# Combine all token patterns into a single regex
TOKEN_REGEX = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPEC)


def tokenize(code):
    tokens = []
    line_num = 1

    for match in re.finditer(TOKEN_REGEX, code):
        kind = match.lastgroup
        value = match.group()

        if kind == 'tok_SKIP':
            continue
        elif kind == 'tok_NEWLINE':
            line_num += 1
        elif kind == 'tok_MISMATCH':
            raise SyntaxError(f"Unexpected character '{value}' on line {line_num}")
        elif kind == 'tok_IDENTIFIER' and value in KEYWORDS:
            tokens.append(('tok_KEYWORD', value))
        else:
            tokens.append((kind, value))

    tokens.append(('tok_EOF', ''))  # End of input
    return tokens
