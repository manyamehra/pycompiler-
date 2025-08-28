from compiler.lexer import tokenize

code = "int main (): x = 42 + y"
print(tokenize(code))
