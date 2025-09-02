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

ND_CONST = "nd_const"
ND_NOT = "nd_not"
ND_NEG = "nd_neg"
ND_ADD = "nd_add"
ND_SUB = "nd_sub"
ND_MUL = "nd_mul"
ND_DIV = "nd_div"
ND_IDENT = "nd_ident"


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
    
    def E(self):
        """E -> P"""
        return self.P()
    
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



BINOPS = {
    "tok_plus":   (10, "L", ND_ADD),
    "tok_minus":  (10, "L", ND_SUB),
    "tok_star":   (20, "L", ND_MUL),
    "tok_slash":  (20, "L", ND_DIV),

}

class ParserOptimise(Parser):
  

    def E(self, min_prio: int = 0):

        gauche = self.P()

        while True:
            tok_type, _ = self.lexer.peek()
            if tok_type not in BINOPS:
                break

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

    else:
        raise ValueError(f"Unknown node type: {A.type}")
    