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


class SymbolTable:
    """Table de symboles pour gérer les variables"""
    
    def __init__(self):
        self.symbols = {}  # nom -> adresse
        self.next_address = 0
    
    def declare(self, name, value=None):
        """Déclare une nouvelle variable"""
        if name in self.symbols:
            raise NameError(f"Variable '{name}' déjà déclarée")
        
        address = self.next_address
        self.symbols[name] = {
            'address': address,
            'value': value
        }
        self.next_address += 1
        return address
    
    def lookup(self, name):
        """Cherche une variable dans la table"""
        if name not in self.symbols:
            raise NameError(f"Variable '{name}' non déclarée")
        return self.symbols[name]
    
    def get_address(self, name):
        """Retourne l'adresse d'une variable"""
        return self.lookup(name)['address']
    
    def exists(self, name):
        """Vérifie si une variable existe"""
        return name in self.symbols
    
    def display(self):
        """Affiche le contenu de la table de symboles"""
        print("\n=== TABLE DE SYMBOLES ===")
        if not self.symbols:
            print("Aucune variable déclarée")
        else:
            for name, info in self.symbols.items():
                print(f"{name}: adresse={info['address']}, valeur={info['value']}")
        print("========================\n")


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
    def __init__(self, lexer, symbol_table=None):
        self.lexer = lexer
        self.last = None  # dernier token lu
        self.symbol_table = symbol_table if symbol_table else SymbolTable()
    
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
            var_name = token[1]
            
            # Déclarer automatiquement la variable si elle n'existe pas
            if not self.symbol_table.exists(var_name):
                self.symbol_table.declare(var_name)
                print(f"Variable '{var_name}' déclarée automatiquement")
            
            return Nd(ND_IDENT, chaine=var_name)
        
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
            self.accept("tok_debug")
            N = self.E()
            self.accept("tok_pointVirgule")
            return node_1(ND_DEBUG, N)
        
        elif self.check("tok_accoladeOuvrante"):
            self.accept("tok_accoladeOuvrante")
            N = node(ND_BLOCK)
            while not self.check("tok_accoladeFermante"):
                N.ajouter_enfant(self.I())
            self.accept("tok_accoladeFermante")
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


def gennode(A, symbol_table):
    """Generate assembly instructions from AST (ancienne version)"""
    if A.type == "nd_const":
        print("push", A.valeur)

    elif A.type == "nd_not":
        gennode(A.enfant[0], symbol_table)
        print("not")

    elif A.type == "nd_neg":
        gennode(A.enfant[0], symbol_table)
        print("neg")

    elif A.type == "nd_add":
        gennode(A.enfant[0], symbol_table)
        gennode(A.enfant[1], symbol_table)
        print("add")

    elif A.type == "nd_sub":
        gennode(A.enfant[0], symbol_table)
        gennode(A.enfant[1], symbol_table)
        print("sub")

    elif A.type == "nd_mul":
        gennode(A.enfant[0], symbol_table)
        gennode(A.enfant[1], symbol_table)
        print("mul")

    elif A.type == "nd_div":
        gennode(A.enfant[0], symbol_table)
        gennode(A.enfant[1], symbol_table)
        print("div")

    elif A.type == "nd_ident":
        address = symbol_table.get_address(A.chaine)
        print("load", address)

    elif A.type == "nd_debug":
        gennode(A.enfant[0], symbol_table)
        print("debug")

    elif A.type == "nd_block":
        for enfant in A.enfant:
            gennode(enfant, symbol_table)

    elif A.type == "nd_drop":
        gennode(A.enfant[0], symbol_table)
        print("drop")

    else:
        raise ValueError(f"Unknown node type: {A.type}")


class CodeGenerator:
    """Générateur de code amélioré avec optimisations"""
    
    def __init__(self, symbol_table):
        self.symbol_table = symbol_table
        self.instructions = []
        self.label_counter = 0
    
    def new_label(self):
        """Génère un nouveau label unique"""
        label = f"L{self.label_counter}"
        self.label_counter += 1
        return label
    
    def emit(self, instruction, *args):
        """Émet une instruction"""
        if args:
            self.instructions.append(f"{instruction} {' '.join(map(str, args))}")
        else:
            self.instructions.append(instruction)
    
    def gencode(self, node):
        """Version améliorée de génération de code"""
        if node.type == "nd_const":
            self.emit("push", node.valeur)
        
        elif node.type == "nd_not":
            self.gencode(node.enfant[0])
            self.emit("not")
        
        elif node.type == "nd_neg":
            self.gencode(node.enfant[0])
            self.emit("neg")
        
        elif node.type == "nd_add":
            self.gencode(node.enfant[0])
            self.gencode(node.enfant[1])
            self.emit("add")
        
        elif node.type == "nd_sub":
            self.gencode(node.enfant[0])
            self.gencode(node.enfant[1])
            self.emit("sub")
        
        elif node.type == "nd_mul":
            self.gencode(node.enfant[0])
            self.gencode(node.enfant[1])
            self.emit("mul")
        
        elif node.type == "nd_div":
            self.gencode(node.enfant[0])
            self.gencode(node.enfant[1])
            self.emit("div")
        
        elif node.type == "nd_ident":
            try:
                address = self.symbol_table.get_address(node.chaine)
                self.emit("load", address)
            except NameError:
                # Si la variable n'existe pas, on peut l'auto-déclarer
                address = self.symbol_table.declare(node.chaine)
                self.emit("load", address)
        
        elif node.type == "nd_debug":
            self.gencode(node.enfant[0])
            self.emit("debug")
        
        elif node.type == "nd_block":
            for enfant in node.enfant:
                self.gencode(enfant)
        
        elif node.type == "nd_drop":
            self.gencode(node.enfant[0])
            self.emit("drop")
        
        else:
            raise ValueError(f"Unknown node type: {node.type}")
    
    def get_code(self):
        """Retourne le code généré sous forme de liste"""
        return self.instructions
    
    def print_code(self):
        """Affiche le code généré"""
        for instruction in self.instructions:
            print(instruction)
    
    def clear(self):
        """Efface le code généré"""
        self.instructions.clear()


if __name__ == "__main__":
    # Créer une table de symboles globale
    symbol_table = SymbolTable()
    
    print("=== EXPRESSION TESTS AVEC TABLE DE SYMBOLES ===")
    
    print("\nTest 1: 42")
    print("AST:", end=" ")
    lexer1 = Lexer("42")
    parser1 = Parser(lexer1, symbol_table)
    arbre1 = parser1.E()
    arbre1.afficher()
    print("\nInstructions (gennode):")
    gennode(arbre1, symbol_table)
    
    print("\nInstructions (gencode):")
    gen1 = CodeGenerator(symbol_table)
    gen1.gencode(arbre1)
    gen1.print_code()
    print()
    
    print("\nTest 2: x + 5 (avec variable)")
    print("AST:", end=" ")
    lexer2 = Lexer("x + 5")
    parser2 = Parser(lexer2, symbol_table)
    arbre2 = parser2.E()
    arbre2.afficher()
    print("\nInstructions (gencode):")
    gen2 = CodeGenerator(symbol_table)
    gen2.gencode(arbre2)
    gen2.print_code()
    print()
    
    print("\nTest 3: (y * 2) + (z - 1)")
    print("AST:", end=" ")
    lexer3 = Lexer("(y * 2) + (z - 1)")
    parser3 = Parser(lexer3, symbol_table)
    arbre3 = parser3.E()
    arbre3.afficher()
    print("\nInstructions (gencode):")
    gen3 = CodeGenerator(symbol_table)
    gen3.gencode(arbre3)
    gen3.print_code()
    print()
    
    print("\nTest 4: !False + True")
    print("AST:", end=" ")
    lexer4 = Lexer("!False + True")
    parser4 = Parser(lexer4, symbol_table)
    arbre4 = parser4.E()
    arbre4.afficher()
    print("\nInstructions (gencode):")
    gen4 = CodeGenerator(symbol_table)
    gen4.gencode(arbre4)
    gen4.print_code()
    print()
    
    print("\nTest 5: -(a + b) * c")
    print("AST:", end=" ")
    lexer5 = Lexer("-(a + b) * c")
    parser5 = Parser(lexer5, symbol_table)
    arbre5 = parser5.E()
    arbre5.afficher()
    print("\nInstructions (gencode):")
    gen5 = CodeGenerator(symbol_table)
    gen5.gencode(arbre5)
    gen5.print_code()
    print()
    
    # Afficher la table de symboles finale
    symbol_table.display()
    
    print("\n=== COMPARAISON DES DEUX MÉTHODES ===")
    print("Test comparatif: 10 + variable")
    lexer_comp = Lexer("10 + variable")
    parser_comp = Parser(lexer_comp, symbol_table)
    arbre_comp = parser_comp.E()
    
    print("\nMéthode gennode:")
    gennode(arbre_comp, symbol_table)
    
    print("\nMéthode gencode (CodeGenerator):")
    gen_comp = CodeGenerator(symbol_table)
    gen_comp.gencode(arbre_comp)
    gen_comp.print_code()
    
    print("\n=== INSTRUCTION TESTS ===")
    print("\nInstruction tests nécessitent les tokens:")
    print("- tok_debug, tok_pointVirgule, tok_accoladeOuvrante, tok_accoladeFermante")
    print("\nExemples d'usage avec la table de symboles:")
    print("debug x + y;  -> charge x et y depuis leurs adresses")
    print("{ a * 2; debug b; }  -> bloc avec variables")