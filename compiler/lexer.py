
import re
from compiler.tokens import Identifiant

TOKEN_SPEC = [
    ('tok_chiffre',     r'\d+'),
    ('tok_identifiant', r'[A-Za-z_][A-Za-z0-9_]*'),
    ('tok_plus', r'\+'),
    ('tok_minus', r'-'),
    ('tok_star', r'\*'),
    ('tok_slash', r'/'),
    ('tok_egal',r'='),
    ('tok_lparen', r'\('),
    ('tok_rparen',  r'\)'),
    ('tok_espace', r'[ \t]+'),   
    ('tok_MISMATCH',   r'.'), 
    ('tok_NEWLINE', r'\n'),
    ("tok_lcurly",r'\{'),
    ( "tok_rcurly",r'\}'),
    ("tok_lbrack",r'\['),
    ("tok_rbrack",r'\]'),
    ("tok_semicolon",r'\;'),
    ("tok_and",r'\&'),
    ("tok_AND",r'&&'),
    ("tok_notequal",r'!'),
    ("tok_pipe",r'||'),
    ("tok_equalto",r'=='),
    ("tok_not",r'\+'),
    ("tok_pecent", r'\+'),  
]

TOKEN_REGEX = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPEC)


def tokenize(code):
    tokens = []
    line_num = 1

    for match in re.finditer(TOKEN_REGEX, code):
        kind = match.lastgroup
        value = match.group()

        if kind == 'tok_NEWLINE':
            line_num += 1
        elif kind == 'tok_MISMATCH':
            raise SyntaxError(f"Unexpected character '{value}' on line {line_num}")
        elif kind == 'tok_identifiant' and value in Identifiant:
            tokens.append(('tok_identifiant', value))
        else:
            tokens.append((kind, value))

    tokens.append(('tok_EOF', ''))  
    return tokens
