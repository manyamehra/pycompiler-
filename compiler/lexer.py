
import re
from compiler.tokens import KEYWORDS

TOKEN_SPEC = [
    ('tok_chiffre',     r'\d+'),
    ('tok_identifiant', r'[A-Za-z_][A-Za-z0-9_]*'),
    ('tok_+', r'\+'),
    ('tok_-', r'-'),
    ('tok_*', r'\*'),
    ('tok_/', r'/'),
    ('tok_=',r'='),
    ('tok_(', r'\('),
    ('tok_)',  r'\)'),
    ('tok_\n', r'\n'),
    ('tok_espace',       r'[ \t]+'),   
    ('tok_MISMATCH',   r'.'),     
    ("tok_{",r'\{'),
    ( "tok_}",r'\}'),
    ("tok_[",r'\['),
    ("tok_]",r'\]'),
    ("tok_;",r'\;'),
    ("tok_&",r'\&'),
    ("tok_&&",r'&&'),
    ("tok_!=",r'!'),
    ("tok_||",r'||'),
    ("tok_==",r'=='),
    ("tok_!",r'\+'),
    ("tok_%", r'\+'),  
]

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

    tokens.append(('tok_EOF', ''))  
    return tokens
