from lexer import Lexer


class Nd:
    def __init__(self, node_type, valeur=None, chaine=None):
        self.type = node_type
        self.valeur = valeur
        self.chaine = chaine
        self.enfant = []
        self.address = None  # For semantic analysis
    
    def ajouter_enfant(self, enfant_node):
        """Ajoute un enfant au nœud"""
        self.enfant.append(enfant_node)
    
    def afficher(self, indent=0):
        """Affiche l'arbre en format Lisp"""
        print("(" + self.type, end="")
        if self.valeur is not None:
            print(f" {self.valeur}", end="")
        if self.chaine is not None:
            print(f' "{self.chaine}"', end="")
        
        for enfant in self.enfant:
            print(" ", end="")
            enfant.afficher()
        
        print(")", end="")


# Node type constants
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
ND_DEBUG = "nd_debug"
ND_BLOCK = "nd_block"
ND_DROP = "nd_drop"

# Binary operators table
BINOPS = {
    "tok_plus":   (10, "L", ND_ADD),
    "tok_minus":  (10, "L", ND_SUB),
    "tok_star":   (20, "L", ND_MUL),
    "tok_slash":  (20, "L", ND_DIV),
}


def create_node(node_type, valeur=None, chaine=None, children=None):
    """Create a node with optional value, string, and children"""
    node = Nd(node_type, valeur, chaine)
    if children:
        for child in children:
            node.ajouter_enfant(child)
    return node


class Parser:
    def __init__(self, lexer):
        self.lexer = lexer
        self.last = None

    def check(self, token_type):
        return self.lexer.check(token_type)

    def accept(self, token_type):
        if not self.check(token_type):
            token = self.lexer.peek()
            raise SyntaxError(
                f"Expected: {token_type}, got: {token[0]} at line {self.lexer.line}"
            )
        self.last = self.lexer.peek()
        self.lexer.next()
        return self.last

    def parse_expression(self, min_prio=0): 
        """Parse expressions with precedence climbing"""
        left = self.parse_primary()

        while True:
            token = self.lexer.peek()
            if not token or token[0] not in BINOPS:
                break

            tok_type = token[0]
            prec, assoc, nd_type = BINOPS[tok_type]
            if prec < min_prio:
                break

            self.accept(tok_type)
            next_min = prec if assoc == "R" else prec + 1
            right = self.parse_expression(next_min)
            left = create_node(nd_type, children=[left, right])

        return left

    def parse_primary(self):
        """Parse primary expressions (unary operators and atoms)"""
        if self.check("tok_not"):
            self.accept("tok_not")
            return create_node(ND_NOT, children=[self.parse_primary()])
        
        if self.check("tok_minus"):
            self.accept("tok_minus")
            return create_node(ND_NEG, children=[self.parse_primary()])
        
        if self.check("tok_plus"):
            self.accept("tok_plus")
            return self.parse_primary()
        
        return self.parse_atom()

    def parse_atom(self):
        """Parse atomic expressions"""
        if self.check("tok_chiffre"):
            token = self.accept("tok_chiffre")
            return create_node(ND_CONST, valeur=token[1])

        if self.check("tok_lparen"):
            self.accept("tok_lparen")
            expr = self.parse_expression()
            self.accept("tok_rparen")
            return expr

        if self.check("tok_identifiant"):
            token = self.accept("tok_identifiant")
            return create_node(ND_IDENT, chaine=token[1])

        if self.check("tok_motscle"):
            token = self.lexer.peek()
            if token[1] in ["True", "False"]:
                self.accept("tok_motscle")
                valeur = 1 if token[1] == "True" else 0
                return create_node(ND_CONST, valeur=valeur)

        token = self.lexer.peek()
        raise SyntaxError(f"Expected expression, got: {token[0]} at line {self.lexer.line}")

    def parse_instruction(self):
        """Parse instructions"""
        # Variable declaration
        if self.check("tok_motscle") and self.lexer.peek()[1] == "int":
            self.accept("tok_motscle")
            token = self.accept("tok_identifiant")
            self.accept("tok_semicolon")
            return create_node(ND_DECL, chaine=token[1])

        # Debug statement
        if self.check("tok_motscle") and self.lexer.peek()[1] == "debug":
            self.accept("tok_motscle")
            expr = self.parse_expression()
            self.accept("tok_semicolon")
            return create_node(ND_DEBUG, children=[expr])

        # Block
        if self.check("tok_lcurly"):
            self.accept("tok_lcurly")
            block = create_node(ND_BLOCK)
            while not self.check("tok_rcurly"):
                block.ajouter_enfant(self.parse_instruction())
            self.accept("tok_rcurly")
            return block

        # If statement
        if self.check("tok_motscle") and self.lexer.peek()[1] == "if":
            self.accept("tok_motscle")
            self.accept("tok_lparen")
            condition = self.parse_expression()
            self.accept("tok_rparen")
            then_stmt = self.parse_instruction()
            
            children = [condition, then_stmt]
            if self.check("tok_motscle") and self.lexer.peek()[1] == "else":
                self.accept("tok_motscle")
                else_stmt = self.parse_instruction()
                children.append(else_stmt)
            
            return create_node(ND_IF, children=children)

        # Assignment or expression statement
        if self.check("tok_identifiant"):
            # Look ahead to see if it's assignment
            var_token = self.accept("tok_identifiant")
            
            if self.check("tok_egal"):
                # Assignment
                self.accept("tok_egal")
                expr = self.parse_expression()
                self.accept("tok_semicolon")
                ident_node = create_node(ND_IDENT, chaine=var_token[1])
                return create_node(ND_ASSIGN, children=[ident_node, expr])
            else:
                # Just identifier as expression
                self.accept("tok_semicolon")
                ident_node = create_node(ND_IDENT, chaine=var_token[1])
                return create_node(ND_DROP, children=[ident_node])

        # Expression statement
        expr = self.parse_expression()
        self.accept("tok_semicolon")
        return create_node(ND_DROP, children=[expr])


def parse(source_code):
    """Parse source code and return AST"""
    lexer = Lexer(source_code)
    parser = Parser(lexer)
    ast = parser.parse_instruction()
    return ast


if __name__ == "__main__":
    # Simple test
    print("--- Test parsing ---")
    ast = parse("42;")
    print("AST: ", end="")
    ast.afficher()
    print()