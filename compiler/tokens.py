# compiler/tokens.py

# Keywords in your mini Python
KEYWORDS = {
    "if", "else", "while", "def", "return", "True", "False", "None"
}

# Token types — used by the lexer
TOKEN_TYPES = {
    "tok_NUMBER",
    "tok_IDENTIFIER",
    "tok_KEYWORD",
    "tok_PLUS", "tok_MINUS", "tok_STAR", "tok_SLASH",
    "tok_EQUALS",
    "tok_LPAREN", "tok_RPAREN",
    "tok_NEWLINE",
    "tok_EOF"
}
