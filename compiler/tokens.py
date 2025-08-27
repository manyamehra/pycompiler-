# compiler/tokens.py

# Keywords in your mini Python
KEYWORDS = {
    "if", "else", "while", "def", "return", "True", "False", "None"
}

# Token types — used by the lexer
TOKEN_TYPES = {
    "NUMBER",
    "IDENTIFIER",
    "KEYWORD",
    "PLUS", "MINUS", "STAR", "SLASH",
    "EQUALS",
    "LPAREN", "RPAREN",
    "NEWLINE",
    "EOF"
}
