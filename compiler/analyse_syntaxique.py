from analyse_lexique import Lexer


class Nd:
    def __init__(self, node_type, valeur=None, chaine=None):
        self.type = node_type
        self.valeur = valeur
        self.chaine = chaine
        self.enfant = []
        self.address = None  # For semantic analysis
        self.array_size= None 
        self.is_pointer = False  # NEW: track if variable is a pointer

    
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
ND_LT = "nd_lt"
ND_GT = "nd_gt"
ND_LE = "nd_le"
ND_GE = "nd_ge"
ND_EQ = "nd_eq"
ND_NE = "nd_ne"
ND_IDENT = "nd_ident"
ND_DECL = "nd_decl"
ND_ASSIGN = "nd_assign"
ND_IF = "nd_if"
ND_WHILE = "nd_while"
ND_DEBUG = "nd_debug"
ND_BLOCK = "nd_block"
ND_DROP = "nd_drop"
ND_FOR="nd_for"
ND_DOWHILE="nd_dowhile"
ND_ARRAY_DECL="nd_array_decl" #int arr[10];
ND_ARRAY_ACCESS="nd_array_access" #arr[5]
ND_ARRAY_ASSIGN="nd_array_assign" #arr[5]=10;
ND_FUNC_DECL="nd_func_decl"
ND_FUNC_CALL="nd_func_call"
ND_RETURN="nd_return"
ND_PTR_DECL = "nd_ptr_decl"        # int* ptr;
ND_ADDRESS_OF = "nd_address_of"    # &x
ND_DEREF = "nd_deref"              # *ptr (as expression)
ND_DEREF_ASSIGN = "nd_deref_assign" # *ptr = value;
ND_FOR_DECL = "nd_for_decl"  # Special node for for-loop declaration+init
ND_AND="nd_and"
ND_OR="nd_or"

# Binary operators table
BINOPS = {
    "tok_plus":   (10, "L", ND_ADD),
    "tok_minus":  (10, "L", ND_SUB),
    "tok_star":   (20, "L", ND_MUL),
    "tok_slash":  (20, "L", ND_DIV),
    "tok_lt":     (5, "L", ND_LT),
    "tok_gt":     (5, "L", ND_GT),
    "tok_le":     (5, "L", ND_LE),
    "tok_ge":     (5, "L", ND_GE),
    "tok_equalto": (5, "L", ND_EQ),
    "tok_notequal": (5, "L", ND_NE),
    "tok_egal": (5, "R", ND_ASSIGN), 
    "tok_and": (3,"L",ND_AND),
    "tok_or": (2,"L",ND_OR),
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
        
        # Address-of operator: &x
        if self.check("tok_ampersand"):
            self.accept("tok_ampersand")
            operand = self.parse_primary()
            return create_node(ND_ADDRESS_OF, children=[operand])
        
        # Dereference or negation
        if self.check("tok_star"):
            self.accept("tok_star")
            # Need to check context - is this dereference or multiply?
            # In primary position, it's always dereference
            operand = self.parse_primary()
            return create_node(ND_DEREF, children=[operand])
        
        # Logical NOT
        if self.check("tok_not"):
            self.accept("tok_not")
            return create_node(ND_NOT, children=[self.parse_primary()])
        
        # Unary minus
        if self.check("tok_minus"):
            self.accept("tok_minus")
            return create_node(ND_NEG, children=[self.parse_primary()])
        
        # Unary plus (just ignored)
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
            # --- Vérifie si c'est un appel de fonction ---
            if self.check("tok_lparen"):
                self.accept("tok_lparen")
                args = []
                if not self.check("tok_rparen"):
                    while True:
                        args.append(self.parse_expression())
                        if self.check("tok_rparen"):
                            break
                        self.accept("tok_comma")
                self.accept("tok_rparen")

                func_node = create_node(ND_FUNC_CALL, chaine=token[1])
                for a in args:
                    func_node.ajouter_enfant(a)
                return func_node
            #Check for array access
            if self.check("tok_lbrack"):
                self.accept("tok_lbrack")
                index_expr=self.parse_expression()
                self.accept("tok_rbrack")

                ident_node=create_node(ND_IDENT, chaine=token[1])
                return create_node(ND_ARRAY_ACCESS, children=[ident_node, index_expr])
            
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
        # Function definition - simple approach without complex lookahead
        if self.check("tok_motscle") and self.lexer.peek()[1] in ["int", "void"]:
            # Store current position for error reporting
            start_line = self.lexer.line
            
            try:
                # Parse return type and function name
                return_type = self.accept("tok_motscle")[1]
                func_name_token = self.accept("tok_identifiant")
                
                # If next token is '(', parse as function
                if self.check("tok_lparen"):
                    func_name = func_name_token[1]
                    self.accept("tok_lparen")
                    
                    params = []
                    if not self.check("tok_rparen"): #there are parameters
                        while True: 
                            # Parse parameter type (int, int*, etc.)
                            param_type = self.accept("tok_motscle")[1]
                            is_ptr_param = False
                            if self.check("tok_star"):
                                self.accept("tok_star")
                                is_ptr_param = True
                            param_name = self.accept("tok_identifiant")[1]
                            params.append((param_type, param_name, is_ptr_param))
                            
                            if self.check("tok_rparen"):
                                break
                            self.accept("tok_comma")

                    self.accept("tok_rparen")
                    body = self.parse_instruction()
                    func_node = create_node(ND_FUNC_DECL, chaine=func_name)
                    func_node.return_type = return_type  # Store return type

                    # Add parameters as child nodes
                    for param_type, param_name, is_ptr in params:
                        param_node = create_node(ND_IDENT, chaine=param_name)
                        param_node.is_pointer = is_ptr
                        param_node.param_type = param_type
                        param_node.is_parameter = True  # Mark as parameter
                        func_node.ajouter_enfant(param_node)

                    func_node.ajouter_enfant(body)
                    return func_node
                else:
                    # Not a function - it's a variable declaration
                    # We already consumed "int" and identifier, so parse as variable
                    # Check if it's an array declaration: int arr[10];
                    if self.check("tok_lbrack"):
                        self.accept("tok_lbrack")
                        size_token = self.accept("tok_chiffre")
                        self.accept("tok_rbrack")
                        self.accept("tok_semicolon")
                        
                        node = create_node(ND_ARRAY_DECL, chaine=func_name_token[1])
                        node.array_size = size_token[1]
                        return node
                    else:
                        # Regular variable
                        self.accept("tok_semicolon")
                        return create_node(ND_DECL, chaine=func_name_token[1])
                        
            except SyntaxError as e:
                raise SyntaxError(f"Syntax error at line {start_line}: {str(e)}")

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
        
        # For statement 
        if self.check("tok_motscle") and self.lexer.peek()[1] == "for":
            self.accept("tok_motscle")
            self.accept("tok_lparen")
            
            # Check if first part is a declaration
            has_decl = False
            decl_node = None
            
            if self.check("tok_motscle") and self.lexer.peek()[1] == "int":
                # Variable declaration: int i = 0
                has_decl = True
                self.accept("tok_motscle")
                
                var_name = self.accept("tok_identifiant")[1]
                self.accept("tok_egal")
                init_expr = self.parse_expression()
                
                # Create combined decl+init node
                decl_node = create_node(ND_DECL, chaine=var_name)
                ident_node = create_node(ND_IDENT, chaine=var_name)
                assign_node = create_node(ND_ASSIGN, children=[ident_node, init_expr])
                
                # Create a special for-decl node that combines both
                E1 = create_node(ND_FOR_DECL, children=[decl_node, assign_node])
            else:
                # Regular expression
                E1 = self.parse_expression()
            
            self.accept("tok_semicolon")
            E2 = self.parse_expression()  # Condition
            self.accept("tok_semicolon")
            E3 = self.parse_expression()  # Increment
            self.accept("tok_rparen")
            I1 = self.parse_instruction()  # Body
            return create_node(ND_FOR, children=[E1, E2, E3, I1])


        # While statement
        if self.check("tok_motscle") and self.lexer.peek()[1] == "while":
            self.accept("tok_motscle")
            self.accept("tok_lparen")
            condition = self.parse_expression()
            self.accept("tok_rparen")
            body = self.parse_instruction()
            return create_node(ND_WHILE, children=[condition, body])
        
        # Do-While statement
        if self.check("tok_motscle") and self.lexer.peek()[1] == "do":
            self.accept("tok_motscle")
            body = self.parse_instruction()
            
            if not (self.check("tok_motscle") and self.lexer.peek()[1] == "while"):
                raise SyntaxError(f"Expected 'while' after do-body at line {self.lexer.line}")
            self.accept("tok_motscle")
            
            self.accept("tok_lparen")
            condition = self.parse_expression()
            self.accept("tok_rparen")
            self.accept("tok_semicolon")
            
            return create_node(ND_DOWHILE, children=[body, condition])

        # Return statement
        if self.check("tok_motscle") and self.lexer.peek()[1] == "return":
            self.accept("tok_motscle")
            expr = self.parse_expression()
            self.accept("tok_semicolon")
            return create_node(ND_RETURN, children=[expr])

        # Assignment or expression statement
        if self.check("tok_identifiant"):
            var_token = self.accept("tok_identifiant")
            
            # Check for array assignment: arr[index] = value;
            if self.check("tok_lbrack"):
                self.accept("tok_lbrack")
                index_expr = self.parse_expression()
                self.accept("tok_rbrack")
                self.accept("tok_egal")
                value_expr = self.parse_expression()
                self.accept("tok_semicolon")
                
                ident_node = create_node(ND_IDENT, chaine=var_token[1])
                return create_node(ND_ARRAY_ASSIGN, children=[ident_node, index_expr, value_expr])
            
            # Check for regular assignment: ident = value;
            if self.check("tok_egal"):
                self.accept("tok_egal")
                expr = self.parse_expression()
                self.accept("tok_semicolon")
                ident_node = create_node(ND_IDENT, chaine=var_token[1])
                return create_node(ND_ASSIGN, children=[ident_node, expr])
            
            # Expression statement (likely function call or standalone identifier)
            # Put it back and parse as expression
            # Since we already consumed it, check if there's more
            if self.check("tok_lparen"):
                # It's a function call as a statement
                self.accept("tok_lparen")
                args = []
                if not self.check("tok_rparen"):
                    while True:
                        args.append(self.parse_expression())
                        if self.check("tok_rparen"):
                            break
                        self.accept("tok_comma")
                self.accept("tok_rparen")
                self.accept("tok_semicolon")
                
                node = create_node(ND_FUNC_CALL, chaine=var_token[1])
                for a in args:
                    node.ajouter_enfant(a)
                return create_node(ND_DROP, children=[node])
            
            # Just an identifier as a statement
            self.accept("tok_semicolon")
            ident_node = create_node(ND_IDENT, chaine=var_token[1])
            return create_node(ND_DROP, children=[ident_node])

        # Add handling for dereference assignment: *ptr = value;
        if self.check("tok_star"):
            self.accept("tok_star")
            ptr_expr = self.parse_primary()  # Get the pointer expression
            self.accept("tok_egal")
            value_expr = self.parse_expression()
            self.accept("tok_semicolon")
            return create_node(ND_DEREF_ASSIGN, children=[ptr_expr, value_expr])
        
        # Generic expression statement
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
    print("--- Test parsing ---")
    ast = parse("42;")
    print("AST: ", end="")
    ast.afficher()
    print()