from lexer import Lexer


class Nd:
    def __init__(self, node_type, valeur=None, chaine=None):
        self.type = node_type
        self.valeur = valeur
        self.chaine = chaine
        self.nbEnfant = 0
        self.enfant = []
    
    def ajouter_enfant(self, enfant_node):
        """Ajoute un enfant au nœud"""
        self.enfant.append(enfant_node)
        self.nbEnfant += 1
    
    def afficher(self, indent=0):
        """Affiche l'arbre en format Lisp selon les notes"""
        print("(" + self.type, end="")
        if self.valeur is not None:
            print(f" {self.valeur}", end="")
        if self.chaine is not None:
            print(f' "{self.chaine}"', end="")
        
        for enfant in self.enfant:
            print(" ", end="")
            enfant.afficher()
        
        print(")", end="")

# Node types for expressions
ND_CONST = "nd_const"
ND_NOT = "nd_not"
ND_NEG = "nd_neg"
ND_ADD = "nd_add"
ND_SUB = "nd_sub"
ND_MUL = "nd_mul"
ND_DIV = "nd_div"
ND_IDENT = "nd_ident"

# Node types for instructions
ND_DEBUG = "nd_debug"
ND_BLOCK = "nd_block"
ND_DROP = "nd_drop"

OP = {
    "tok_plus":  {"prio": 10, "parg": 11, "Ntype": ND_ADD},
    "tok_minus": {"prio": 10, "parg": 11, "Ntype": ND_SUB},
    "tok_star":  {"prio": 20, "parg": 21, "Ntype": ND_MUL},
    "tok_slash": {"prio": 20, "parg": 21, "Ntype": ND_DIV},
}

BINOPS = {
    "tok_plus":   (10, "L", ND_ADD),
    "tok_minus":  (10, "L", ND_SUB),
    "tok_star":   (20, "L", ND_MUL),
    "tok_slash":  (20, "L", ND_DIV),
}

def node_v(node_type, valeur):
    """Crée un nœud avec une valeur"""
    return Nd(node_type, valeur=valeur)

def node_1(node_type, enfant):
    """Crée un nœud avec un enfant"""
    node = Nd(node_type)
    node.ajouter_enfant(enfant)
    return node

def node_2(node_type, enfant1, enfant2):
    """Crée un nœud avec deux enfants"""
    node = Nd(node_type)
    node.ajouter_enfant(enfant1)
    node.ajouter_enfant(enfant2)
    return node

def node(node_type):
    """Crée un nœud simple sans enfant ni valeur"""
    return Nd(node_type)


class Parser:
    def __init__(self, lexer):
        self.lexer = lexer
        self.last = None  # dernier token lu
    
    def check(self, token_type):
        """Vérifie si le token courant est du type donné"""
        return self.lexer.check(token_type)
    
    def accept(self, token_type):
        """Accepte (consomme) un token du type donné"""
        if not self.check(token_type):
            token = self.lexer.peek()
            raise SyntaxError(f"Token attendu: {token_type}, reçu: {token[0]} à la ligne {self.lexer.line}")
        
        self.last = self.lexer.peek()
        self.lexer.next()
        return self.last
    
    def E(self, prio=0):
        """Analyse récursive avec précédence (precedence climbing)."""
        N = self.P()   # parse a primary / prefix

        while self.lexer.peek() and self.lexer.peek()[0] in OP:
            entry = OP[self.lexer.peek()[0]]
            if entry["prio"] < prio:
                break

            op_tok = self.lexer.peek()[0]
            self.accept(op_tok)   # consume operator

            M = self.E(entry["parg"])   # right operand
            N = node_2(entry["Ntype"], N, M)

        return N

    def P(self):
        if self.check("tok_not"):
            self.accept("tok_not")
            n = self.P()
            return node_1(ND_NOT, n)
        
        elif self.check("tok_minus"):
            self.accept("tok_minus")
            return node_1(ND_NEG, self.P())
        
        elif self.check("tok_plus"):
            self.accept("tok_plus")
            return self.P()  
        
        else:
            return self.S()
    
    def S(self):
        """S -> A"""
        return self.A()
    
    def A(self):
        """
        A -> nb | (E) | identifiant
        """
        if self.check("tok_chiffre"):
            token = self.accept("tok_chiffre")
            return node_v(ND_CONST, token[1])
        
        elif self.check("tok_lparen"):
            self.accept("tok_lparen")
            r = self.E()
            self.accept("tok_rparen")
            return r
        
        elif self.check("tok_identifiant"):
            token = self.accept("tok_identifiant")
            return Nd(ND_IDENT, chaine=token[1])
        
        elif self.check("tok_motscle"):
            token = self.lexer.peek()
            if token[1] in ["True", "False"]:
                self.accept("tok_motscle")
                valeur = 1 if token[1] == "True" else 0
                return node_v(ND_CONST, valeur)
            else:
                raise SyntaxError(f"Token inattendu: {token[1]} à la ligne {self.lexer.line}")
        
        else:
            token = self.lexer.peek()
            raise SyntaxError(f"Expression attendue, reçu: {token[0]} à la ligne {self.lexer.line}")

    def I(self):
        """
        Instruction function - handles debug statements, blocks, and expressions
        I -> debug E ; | { I* } | E ;
        """
        if self.check("tok_debug"):
            #self.accept("tok_debug")
            N = self.E()
            self.accept("tok_pointVirgule")
            return node_1(ND_DEBUG, N)
        
        elif self.check("tok_accoladeOuvrante"):
            #self.accept("tok_accoladeOuvrante")
            N = node(ND_BLOCK)
            while not self.check("tok_accoladeFermante"):
                N.ajouter_enfant(self.I())
            #sself.accept("tok_accoladeFermante")
            return N
        
        else:
            N = self.E()
            self.accept("tok_pointVirgule")
            return node_1(ND_DROP, N)


class ParserOptimise(Parser):
    def E(self, min_prio: int = 0):
        gauche = self.P()

        while True:
            if not self.lexer.peek() or self.lexer.peek()[0] not in BINOPS:
                break

            tok_type, _ = self.lexer.peek()
            prec, assoc, nd_type = BINOPS[tok_type]
            if prec < min_prio:
                break

            self.accept(tok_type)
            next_min = prec if assoc == "R" else prec + 1
            droite = self.E(next_min)
            gauche = node_2(nd_type, gauche, droite)

        return gauche

    def P(self):
        if self.check("tok_not"):
            self.accept("tok_not")
            return node_1(ND_NOT, self.P())
        if self.check("tok_minus"):
            self.accept("tok_minus")
            return node_1(ND_NEG, self.P())
        if self.check("tok_plus"):
            self.accept("tok_plus")
            return self.P()
        return self.S()

    def S(self):
        return self.A()  


def gennode(A):
    """Generate assembly instructions from AST"""
    if A.type == "nd_const":
        print("push", A.valeur)

    elif A.type == "nd_not":
        gennode(A.enfant[0])
        print("not")

    elif A.type == "nd_neg":
        gennode(A.enfant[0])
        print("neg")

    elif A.type == "nd_add":
        gennode(A.enfant[0])
        gennode(A.enfant[1])
        print("add")

    elif A.type == "nd_sub":
        gennode(A.enfant[0])
        gennode(A.enfant[1])
        print("sub")

    elif A.type == "nd_mul":
        gennode(A.enfant[0])
        gennode(A.enfant[1])
        print("mul")

    elif A.type == "nd_div":
        gennode(A.enfant[0])
        gennode(A.enfant[1])
        print("div")

    elif A.type == "nd_ident":
        print("load", A.chaine)

    elif A.type == "nd_debug":
        gennode(A.enfant[0])
        print("debug")

    elif A.type == "nd_block":
        for enfant in A.enfant:
            gennode(enfant)

    elif A.type == "nd_drop":
        gennode(A.enfant[0])
        print("drop")

    else:
        raise ValueError(f"Unknown node type: {A.type}")


if __name__ == "__main__":
    
    print("=== EXPRESSION TESTS ===")
    
    print("\nTest 1: 42")
    print("AST:", end=" ")
    lexer1 = Lexer("42")
    parser1 = Parser(lexer1)
    arbre1 = parser1.E()
    arbre1.afficher()
    print("\nInstructions:")
    gennode(arbre1)
    print()
    
    print("\nTest 2: (123)")
    print("AST:", end=" ")
    lexer2 = Lexer("(123)")
    parser2 = Parser(lexer2)
    arbre2 = parser2.E()
    arbre2.afficher()
    print("\nInstructions:")
    gennode(arbre2)
    print()
    
    print("\nTest 3: -42")
    print("AST:", end=" ")
    lexer3 = Lexer("-42")
    parser3 = Parser(lexer3)
    arbre3 = parser3.E()
    arbre3.afficher()
    print("\nInstructions:")
    gennode(arbre3)
    print()
    
    print("\nTest 4: !True")
    print("AST:", end=" ")
    lexer4 = Lexer("!True")
    parser4 = Parser(lexer4)
    arbre4 = parser4.E()
    arbre4.afficher()
    print("\nInstructions:")
    gennode(arbre4)
    print()
    
    print("\nTest 5: 12 + 34")
    print("AST:", end=" ")
    lexer5 = Lexer("12 + 34")
    parser5 = Parser(lexer5)
    arbre5 = parser5.E(0)
    arbre5.afficher()
    print("\nInstructions:")
    gennode(arbre5)
    print()
    
    print("\nTest 6: 12 + 3 * 5")
    print("AST:", end=" ")
    lexer6 = Lexer("12 + 3 * 5")
    parser6 = Parser(lexer6)
    arbre6 = parser6.E(0)
    arbre6.afficher()
    print("\nInstructions:")
    gennode(arbre6)
    print()
    
    print("\nTest 7: -(12 + 3) * 5")
    print("AST:", end=" ")
    lexer7 = Lexer("-(12 + 3) * 5")
    parser7 = Parser(lexer7)
    arbre7 = parser7.E(0)
    arbre7.afficher()
    print("\nInstructions:")
    gennode(arbre7)
    print()

    print("\n=== INSTRUCTION TESTS ===")
    
    # Note: These tests would require your lexer to support the new tokens
    # tok_debug, tok_pointVirgule, tok_accoladeOuvrante, tok_accoladeFermante
    
    print("\nInstruction tests would require lexer support for:")
    print("- tok_debug (debug keyword)")
    print("- tok_pointVirgule (semicolon ;)")
    print("- tok_accoladeOuvrante (opening brace {)")
    print("- tok_accoladeFermante (closing brace })")
    print("\nExample usage:")
    print("parser.I() for parsing: debug 42;")
    print("parser.I() for parsing: { 12 + 34; }")
    print("parser.I() for parsing: x + y;")

