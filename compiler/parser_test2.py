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
    def __init__(self, parent=None):
        self.symbols = {}
        self.next_address = 0 if parent is None else parent.next_address
        self.parent = parent

    def declare(self, name, value=None):
        if name in self.symbols:  # vérifie uniquement dans CE scope
            raise NameError(f"Variable '{name}' déjà déclarée dans ce scope")
        address = self.next_address
        self.symbols[name] = {'address': address, 'value': value}
        self.next_address += 1
        return address

    def lookup(self, name):
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        raise NameError(f"Variable '{name}' non déclarée")

    def get_address(self, name):
        return self.lookup(name)['address']

    def exists(self, name):
        if name in self.symbols:
            return True
        if self.parent:
            return self.parent.exists(name)
        return False


# Node types for expressions
ND_CONST = "nd_const"
ND_NOT = "nd_not"
ND_NEG = "nd_neg"
ND_ADD = "nd_add"
ND_SUB = "nd_sub"
ND_MUL = "nd_mul"
ND_DIV = "nd_div"
ND_IDENT = "nd_ident"
ND_DECL = "nd_decl"
ND_ASSIGN = "nd_assign"


# Node types for instructions
ND_DEBUG = "nd_debug"
ND_BLOCK = "nd_block"
ND_DROP = "nd_drop"

# Table des opérateurs binaires (précédence/associativité → type de nœud)

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

# Garder tes ND_* comme avant



class Parser:
    def __init__(self, lexer, symbol_table=None):
        self.lexer = lexer
        self.last = None
        self.symbol_table = symbol_table if symbol_table else SymbolTable()

    def check(self, token_type):
        return self.lexer.check(token_type)

    def accept(self, token_type):
        if not self.check(token_type):
            token = self.lexer.peek()
            raise SyntaxError(
                f"Token attendu: {token_type}, reçu: {token[0]} à la ligne {self.lexer.line}"
            )
        self.last = self.lexer.peek()
        self.lexer.next()
        return self.last

    # --------- Expression avec précédences (precedence climbing) ---------
    def E(self, min_prio: int = 0):
        left = self.P()

        while True:
            look = self.lexer.peek()
            if not look or look[0] not in BINOPS:
                break

            tok_type, _ = look
            prec, assoc, nd_type = BINOPS[tok_type]
            if prec < min_prio:
                break

            self.accept(tok_type)
            next_min = prec if assoc == "R" else prec + 1
            right = self.E(next_min)
            left = node_2(nd_type, left, right)

        return left

    # --------- Préfixes / primaires ---------
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

    def A(self):
        """
        A -> nb | (E) | identifiant | True | False
        (avec auto-déclaration des identifiants pour rester compatible avec tes tests)
        """
        if self.check("tok_chiffre"):
            token = self.accept("tok_chiffre")
            return node_v(ND_CONST, token[1])

        if self.check("tok_lparen"):
            self.accept("tok_lparen")
            r = self.E()
            self.accept("tok_rparen")
            return r

        if self.check("tok_identifiant"):
            token = self.accept("tok_identifiant")
            var_name = token[1]
            # Auto-déclaration (comportement actuel)
            if not self.symbol_table.exists(var_name):
                self.symbol_table.declare(var_name)
                print(f"Variable '{var_name}' déclarée automatiquement")
            return Nd(ND_IDENT, chaine=var_name)

        if self.check("tok_motscle"):
            token = self.lexer.peek()
            if token[1] in ["True", "False"]:
                self.accept("tok_motscle")
                valeur = 1 if token[1] == "True" else 0
                return node_v(ND_CONST, valeur)
            raise SyntaxError(
                f"Token inattendu: {token[1]} à la ligne {self.lexer.line}"
            )

        token = self.lexer.peek()
        raise SyntaxError(
            f"Expression attendue, reçu: {token[0]} à la ligne {self.lexer.line}"
        )

    def I(self):

    # --- Déclaration ---
        if self.check("tok_motscle") and self.lexer.peek()[1] == "int":
            self.accept("tok_motscle")
            token = self.accept("tok_identifiant")
            var_name = token[1]
            self.accept("tok_semicolon")
            return Nd(ND_DECL, chaine=var_name)

            # --- Affectation ---
        if self.check("tok_identifiant"):
            token = self.accept("tok_identifiant")
            var_name = token[1]
            if self.check("tok_egal"):
                self.accept("tok_egal")
                expr = self.E()
                self.accept("tok_semicolon")
                # Créer un nœud ND_ASSIGN avec 2 enfants : identifiant et expression
                ident_node = Nd(ND_IDENT, chaine=var_name)
                n = Nd(ND_ASSIGN)
                n.ajouter_enfant(ident_node)
                n.ajouter_enfant(expr)
                return n

        # --- Debug ---
        if self.check("tok_motscle") and self.lexer.peek()[1] == "debug":
            self.accept("tok_motscle")
            N = self.E()
            self.accept("tok_semicolon")
            return node_1(ND_DEBUG, N)

        # --- Bloc ---
        if self.check("tok_lcurly"):
            self.accept("tok_lcurly")
            N = node(ND_BLOCK)
            while not self.check("tok_rcurly"):
                N.ajouter_enfant(self.I())
            self.accept("tok_rcurly")
            return N

        # --- Expression suivie de ";" ---
        N = self.E()
        self.accept("tok_semicolon")
        return node_1(ND_DROP, N)

def GenNode(node, symbol_table):
    """Génération d’instructions assembleur avec print direct"""
    if node.type == ND_CONST:
        print("push", node.valeur)

    elif node.type == ND_NOT:
        GenNode(node.enfant[0], symbol_table)
        print("not")

    elif node.type == ND_NEG:
        GenNode(node.enfant[0], symbol_table)
        print("neg")

    elif node.type == ND_ADD:
        GenNode(node.enfant[0], symbol_table)
        GenNode(node.enfant[1], symbol_table)
        print("add")

    elif node.type == ND_SUB:
        GenNode(node.enfant[0], symbol_table)
        GenNode(node.enfant[1], symbol_table)
        print("sub")

    elif node.type == ND_MUL:
        GenNode(node.enfant[0], symbol_table)
        GenNode(node.enfant[1], symbol_table)
        print("mul")

    elif node.type == ND_DIV:
        GenNode(node.enfant[0], symbol_table)
        GenNode(node.enfant[1], symbol_table)
        print("div")

    elif node.type == ND_IDENT:
        address = symbol_table.get_address(node.chaine)
        print("load", address)

    elif node.type == ND_DEBUG:
        GenNode(node.enfant[0], symbol_table)
        print("debug")

    elif node.type == ND_BLOCK:
        for enfant in node.enfant:
            GenNode(enfant, symbol_table)

    elif node.type == ND_DROP:
        GenNode(node.enfant[0], symbol_table)
        print("drop")

    elif node.type == ND_DECL:
        # Déclaration → pas de code, juste réservation dans la table de symboles
        pass  

    elif node.type == ND_ASSIGN:
        # convention: enfant[0] = identifiant, enfant[1] = expression
        GenNode(node.enfant[1], symbol_table)  # calcule la valeur à stocker
        address = symbol_table.get_address(node.enfant[0].chaine)
        print("store", address)

    else:
        raise ValueError(f"Unknown node type: {node.type}")

def GenCode(parser, symbol_table, show_ast=False):
    """Phase globale : construit l’AST, analyse sémantique, génère le code"""
    ast = ana_sem(parser)                  
    if show_ast:
        ast.afficher()
    print("\n")
    GenNode(ast, symbol_table)      

def sem_node(node, symbol_table):
    if node.type == ND_CONST:
        return

    elif node.type in [ND_ADD, ND_SUB, ND_MUL, ND_DIV]:
        sem_node(node.enfant[0], symbol_table)
        sem_node(node.enfant[1], symbol_table)

    elif node.type in [ND_NOT, ND_NEG, ND_DROP, ND_DEBUG]:
        sem_node(node.enfant[0], symbol_table)

    elif node.type == ND_BLOCK:
        local_table = SymbolTable(parent=symbol_table)
        for child in node.enfant:
            sem_node(child, local_table)


    elif node.type == ND_IDENT:
        var_name = node.chaine
        if not symbol_table.exists(var_name):
            raise NameError(f"Variable '{var_name}' utilisée sans déclaration")
        node.valeur = symbol_table.get_address(var_name)

    elif node.type == ND_BLOCK:
        # Créer une nouvelle table qui pointe vers la table parente
        local_table = SymbolTable(parent=symbol_table)
        for child in node.enfant:
            sem_node(child, local_table)


    elif node.type == ND_ASSIGN:
        ident_node = node.enfant[0]
        expr_node = node.enfant[1]
        if not symbol_table.exists(ident_node.chaine):
            raise NameError(f"Variable '{ident_node.chaine}' utilisée sans déclaration")
        sem_node(expr_node, symbol_table)
        ident_node.valeur = symbol_table.get_address(ident_node.chaine)

    else:
        for child in node.enfant:
            sem_node(child, symbol_table)

def ana_sem(parser):
    """
    Analyse sémantique complète :
    - Construit l'AST via le parser
    - Vérifie sémantiquement l'AST
    - Retourne l'AST validé
    """
    ast = parser.I()  
    sem_node(ast, parser.symbol_table)  
    return ast

if __name__ == "__main__":
    symbol_table = SymbolTable()

    print("\n--- Test 1: constante ---")
    lexer1 = Lexer("42;")
    parser1 = Parser(lexer1, symbol_table)
    GenCode(parser1, symbol_table,show_ast=True)   

    print("\n--- Test 2: addition ---")
    lexer2 = Lexer("3 + 5;")
    parser2 = Parser(lexer2, symbol_table)
    GenCode(parser2, symbol_table,show_ast=True)   

    print("\n--- Test 3: debug ---")
    lexer3 = Lexer("debug 7;")
    parser3 = Parser(lexer3, symbol_table)
    GenCode(parser3, symbol_table,show_ast=True)   

    print("\n--- Test 4: bloc ---")
    lexer4 = Lexer("{ 1 + 2; debug 3; }")
    parser4 = Parser(lexer4, symbol_table)
    GenCode(parser4, symbol_table ,show_ast=True)

    print("\n--- Test 5: test prof ---")
    lexer5 = Lexer("{ int x ; x=3; { x=2; int x ; x=5; } x=7;}")
    parser5 = Parser(lexer5, symbol_table)
    GenCode(parser5, symbol_table,show_ast=True)
  
