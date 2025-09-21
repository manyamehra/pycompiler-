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
    def __init__(self):
        self.scopes = [{}]  # pile : [scope global]
        self.next_address = 0

    def enter_scope(self):
        self.scopes.append({})

    def leave_scope(self):
        scope = self.scopes.pop()
        for _ in range(len(scope)):
            print("drop")

    def declare(self, name, value=None):
        current = self.scopes[-1]
        if name in current:
            raise NameError(f"Variable '{name}' déjà déclarée dans ce scope")
        address = self.next_address
        current[name] = {'address': address, 'value': value}
        self.next_address += 1
        return address

    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise NameError(f"Variable '{name}' non déclarée")

    def get_address(self, name):
        return self.lookup(name)['address']

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
ND_IF = "nd_if"
label_counter = 0

def new_label():
    global label_counter
    label = f"L{label_counter}"
    label_counter += 1
    return label

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
            return Nd(ND_IDENT, chaine=var_name)

        if self.check("tok_motscle"):
            token = self.lexer.peek()
            if token[1] in ["True", "False"]:
                self.accept("tok_motscle")
                valeur = 1 if token[1] == "True" else 0
                return node_v(ND_CONST, valeur)

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
        # --- If ---
        if self.check("tok_motscle") and self.lexer.peek()[1] == "if":
            self.accept("tok_motscle")          # if
            self.accept("tok_lparen")           # (
            cond = self.E()                     # E
            self.accept("tok_rparen")           # )
            instr1 = self.I()                   # I1
            instr2 = None
            if self.check("tok_motscle") and self.lexer.peek()[1] == "else":
                self.accept("tok_motscle")
                instr2 = self.I()               # I2
            
            n = Nd(ND_IF)
            n.ajouter_enfant(cond)              # enfant[0] = condition
            n.ajouter_enfant(instr1)            # enfant[1] = bloc vrai
            if instr2:
                n.ajouter_enfant(instr2)        # enfant[2] = bloc faux
            return n

        if self.check("tok_identifiant"):
            saved_pos = self.lexer.current_pos if hasattr(self.lexer, 'current_pos') else 0
            
            token = self.accept("tok_identifiant")
            var_name = token[1]
            
            if self.check("tok_egal"):
                self.accept("tok_egal")
                expr = self.E()
                self.accept("tok_semicolon")
                ident_node = Nd(ND_IDENT, chaine=var_name)
                n = Nd(ND_ASSIGN)
                n.ajouter_enfant(ident_node)
                n.ajouter_enfant(expr)
                return n
            else:
                
                self.accept("tok_semicolon")
                return node_1(ND_DROP, Nd(ND_IDENT, chaine=var_name))
            
        N = self.E()
        self.accept("tok_semicolon")
        return node_1(ND_DROP, N)


def GenNode(node, symbol_table):
    """Génération d'instructions assembleur avec print direct"""
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
        if hasattr(node, 'address'):
            print("load", node.address)
        else:
            address = symbol_table.get_address(node.chaine)
            print("load", address)

    elif node.type == ND_DEBUG:
        GenNode(node.enfant[0], symbol_table)
        print("debug")

    elif node.type == ND_BLOCK:
        symbol_table.enter_scope()
        nb_locals = sum(1 for child in node.enfant if child.type == ND_DECL)
        if nb_locals > 0:
            print("resn", nb_locals)

        for child in node.enfant:
            GenNode(child, symbol_table)

        symbol_table.leave_scope()


    elif node.type == ND_DROP:
        GenNode(node.enfant[0], symbol_table)
        print("drop")

    elif node.type == ND_DECL:
        pass  

    elif node.type == ND_ASSIGN:
        GenNode(node.enfant[1], symbol_table)  
        print("dup")
        print("set", node.enfant[0].address)
        print("drop 1")

    elif node.type == ND_IF:
        GenNode(node.enfant[0], symbol_table)
        
        L1 = new_label()
        L2 = new_label()
        
        print("jumpf", L1)       # si faux → L1
        GenNode(node.enfant[1], symbol_table)  # partie vraie
        print("jump", L2)        # saute après le else
        print(L1 + ":")
        if len(node.enfant) > 2: # partie else
            GenNode(node.enfant[2], symbol_table)
        print(L2 + ":")

    else:
        raise ValueError(f"Unknown node type: {node.type}")


def GenCode(parser, symbol_table, show_ast=False):
    """Phase globale : construit l'AST, analyse sémantique, génère le code"""
    ast = ana_sem(parser)                  
    if show_ast:
        print("AST: ", end="")
        ast.afficher()
        print()
    print("Instructions:")
    GenNode(ast, symbol_table)      

def sem_node(node, symbol_table):
    if node.type == ND_CONST:
        return

    elif node.type in [ND_ADD, ND_SUB, ND_MUL, ND_DIV]:
        sem_node(node.enfant[0], symbol_table)
        sem_node(node.enfant[1], symbol_table)

    elif node.type in [ND_NOT, ND_NEG, ND_DROP, ND_DEBUG]:
        sem_node(node.enfant[0], symbol_table)

    elif node.type == ND_IDENT:
        var_name = node.chaine
        for scope in reversed(symbol_table.scopes):
            if var_name in scope:
                node.address = scope[var_name]['address']
                return
        raise NameError(f"Variable '{var_name}' utilisée sans déclaration")

    elif node.type == ND_DECL:
        var_name = node.chaine
        address = symbol_table.declare(var_name)
        node.address = address  
        print(f"Variable '{var_name}' déclarée à l'adresse {address}")

    elif node.type == ND_ASSIGN:
        ident_node = node.enfant[0]
        expr_node = node.enfant[1]

        sem_node(expr_node, symbol_table)

        for scope in reversed(symbol_table.scopes):
            if ident_node.chaine in scope:
                ident_node.address = scope[ident_node.chaine]['address']
                break
        else:
            raise NameError(f"Variable '{ident_node.chaine}' utilisée sans déclaration")

    elif node.type == ND_BLOCK:
        symbol_table.enter_scope()
        for child in node.enfant:
            sem_node(child, symbol_table)
        symbol_table.leave_scope()

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
    GenCode(parser1, symbol_table, show_ast=True)   

    print("\n--- Test 2: addition ---")
    lexer2 = Lexer("3 + 5;")
    parser2 = Parser(lexer2, symbol_table)
    GenCode(parser2, symbol_table, show_ast=True)   

    print("\n--- Test 3: debug ---")
    lexer3 = Lexer("debug 7;")
    parser3 = Parser(lexer3, symbol_table)
    GenCode(parser3, symbol_table, show_ast=True)   

    print("\n--- Test 4: bloc ---")
    lexer4 = Lexer("{ 1 + 2; debug 3; }")
    parser4 = Parser(lexer4, symbol_table)
    GenCode(parser4, symbol_table, show_ast=True)

    print("\n--- Test 5: test prof ---")
    lexer5 = Lexer("{ int x ; x=3; { x=2; int x ; x=5; } x=7;}")
    parser5 = Parser(lexer5, SymbolTable()) 
    GenCode(parser5, parser5.symbol_table, show_ast=True)

    print("\n--- Test 5: test confition if  ---")
    lexer6 = Lexer("{ int x; if (1) { x=3; } else { x=5; } }")
    parser6 = Parser(lexer6, SymbolTable())  
    GenCode(parser6, parser6.symbol_table, show_ast=True)