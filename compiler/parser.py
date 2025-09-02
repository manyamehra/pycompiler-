from lexer import Lexer

# --- Structure de nœud selon les notes de cours ---

class Nd:
    """
    Structure de nœud d'arbre selon les notes:
    - type: type du nœud
    - valeur: valeur si c'est une constante
    - chaine: chaîne si nécessaire
    - nbEnfant: nombre d'enfants
    - enfant: liste des enfants
    """
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

# --- Types de nœuds (préfixés avec nd_) ---
ND_CONST = "nd_const"
ND_NOT = "nd_not"
ND_NEG = "nd_neg"
ND_ADD = "nd_add"
ND_SUB = "nd_sub"
ND_MUL = "nd_mul"
ND_DIV = "nd_div"
ND_IDENT = "nd_ident"

# --- Fonctions utilitaires pour créer des nœuds ---

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

# --- Parser selon les notes de cours ---

class Parser:
    """
    Parser basé sur les notes de cours
    Grammaire:
    E -> P
    P -> S | !P | -P | +P
    S -> A
    A -> nb | (E)
    """
    
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
        """
        P -> S | !P | -P | +P
        Selon les notes:
        - !P -> not avec P comme enfant
        - -P -> neg avec P comme enfant  
        - +P -> juste P (pas de nœud)
        - sinon -> S
        """
        if self.check("tok_not"):
            self.accept("tok_not")
            n = self.P()
            return node_1(ND_NOT, n)
        
        elif self.check("tok_minus"):
            self.accept("tok_minus")
            return node_1(ND_NEG, self.P())
        
        elif self.check("tok_plus"):
            self.accept("tok_plus")
            return self.P()  # +P -> P (pas de nœud spécial)
        
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

# --- Extension pour les opérations binaires (optionnel) ---

class ParserEtendu(Parser):
    """
    Version étendue qui gère aussi les opérations binaires
    E -> T ((+|-) T)*
    T -> F ((*|/) F)*  
    F -> P
    P -> S | !P | -P | +P
    S -> A
    A -> nb | (E) | identifiant
    """
    
    def E(self):
        """E -> T ((+|-) T)*"""
        gauche = self.T()
        
        while self.check("tok_plus") or self.check("tok_minus"):
            if self.check("tok_plus"):
                self.accept("tok_plus")
                droite = self.T()
                gauche = node_2(ND_ADD, gauche, droite)
            else:  # tok_minus
                self.accept("tok_minus")
                droite = self.T()
                gauche = node_2(ND_SUB, gauche, droite)
        
        return gauche
    
    def T(self):
        """T -> F ((*|/) F)*"""
        gauche = self.F()
        
        while self.check("tok_star") or self.check("tok_slash"):
            if self.check("tok_star"):
                self.accept("tok_star")
                droite = self.F()
                gauche = node_2(ND_MUL, gauche, droite)
            else:  # tok_slash
                self.accept("tok_slash")
                droite = self.F()
                gauche = node_2(ND_DIV, gauche, droite)
        
        return gauche
    
    def F(self):
        """F -> P"""
        return self.P()

# --- Tests selon les notes ---

if __name__ == "__main__":
    print("=== Test Parser Simple (selon notes) ===")
    
    # Test 1: Constante simple
    print("\nTest 1: 42")
    lexer1 = Lexer("42")
    parser1 = Parser(lexer1)
    arbre1 = parser1.E()
    arbre1.afficher()
    print()
    
    # Test 2: Expression avec parenthèses
    print("\nTest 2: (123)")
    lexer2 = Lexer("(123)")
    parser2 = Parser(lexer2)
    arbre2 = parser2.E()
    arbre2.afficher()
    print()
    
    # Test 3: Négation
    print("\nTest 3: -42")
    lexer3 = Lexer("-42")
    parser3 = Parser(lexer3)
    arbre3 = parser3.E()
    arbre3.afficher()
    print()
    
    # Test 4: NOT
    print("\nTest 4: !True")
    lexer4 = Lexer("!True")
    parser4 = Parser(lexer4)
    arbre4 = parser4.E()
    arbre4.afficher()
    print()
    
    print("\n=== Test Parser Étendu (avec opérations binaires) ===")
    
    # Test 5: Addition
    print("\nTest 5: 12 + 34")
    lexer5 = Lexer("12 + 34")
    parser5 = ParserEtendu(lexer5)
    arbre5 = parser5.E()
    arbre5.afficher()
    print()
    
    # Test 6: Expression complexe
    print("\nTest 6: 12 + 3 * 5")
    lexer6 = Lexer("12 + 3 * 5")
    parser6 = ParserEtendu(lexer6)
    arbre6 = parser6.E()
    arbre6.afficher()
    print()
    
    # Test 7: Avec parenthèses et négation
    print("\nTest 7: -(12 + 3) * 5")
    lexer7 = Lexer("-(12 + 3) * 5")
    parser7 = ParserEtendu(lexer7)
    arbre7 = parser7.E()
    arbre7.afficher()
    print()

    