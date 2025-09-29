from compiler.analyse_lexique import tokenize

code = "int main (): x = 42 + y"
print(tokenize(code))
