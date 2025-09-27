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


class SymbolTable:
    def __init__(self):
        self.scopes = [{}]  # Stack of scopes
        self.next_address = 0

    def enter_scope(self):
        """Enter a new scope"""
        self.scopes.append({})

    def leave_scope(self):
        """Leave current scope and return number of variables to drop"""
        if len(self.scopes) <= 1:
            raise RuntimeError("Cannot leave global scope")
        scope = self.scopes.pop()
        return len(scope)

    def declare(self, name):
        """Declare a variable in current scope"""
        current_scope = self.scopes[-1]
        if name in current_scope:
            raise NameError(f"Variable '{name}' already declared in this scope")
        
        address = self.next_address
        current_scope[name] = address
        self.next_address += 1
        return address

    def lookup(self, name):
        """Look up a variable in all scopes (innermost first)"""
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise NameError(f"Variable '{name}' not declared")


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

# Label generation
label_counter = 0

def new_label():
    global label_counter
    label = f"L{label_counter}"
    label_counter += 1
    return label


# Node creation helpers
def create_node(node_type, valeur=None, chaine=None, children=None):
    """Create a node with optional value, string, and children"""
    node = Nd(node_type, valeur, chaine)
    if children:
        for child in children:
            node.ajouter_enfant(child)
    return node


class Parser:
    def __init__(self, lexer, symbol_table=None):
        self.lexer = lexer
        self.last = None
        self.symbol_table = symbol_table or SymbolTable()

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


class SemanticAnalyzer:
    def __init__(self, symbol_table):
        self.symbol_table = symbol_table

    def analyze(self, node):
        """Perform semantic analysis on the AST"""
        method_name = f'analyze_{node.type}'
        method = getattr(self, method_name, self.generic_analyze)
        return method(node)

    def generic_analyze(self, node):
        """Default analysis for nodes with children"""
        for child in node.enfant:
            self.analyze(child)

    def analyze_nd_const(self, node):
        """Constants need no analysis"""
        pass

    def analyze_nd_ident(self, node):
        """Look up identifier and store its address"""
        node.address = self.symbol_table.lookup(node.chaine)

    def analyze_nd_decl(self, node):
        """Declare variable and store its address"""
        node.address = self.symbol_table.declare(node.chaine)

    def analyze_nd_assign(self, node):
        """Analyze assignment"""
        # Analyze the expression first
        self.analyze(node.enfant[1])
        # Then look up the identifier
        ident_node = node.enfant[0]
        ident_node.address = self.symbol_table.lookup(ident_node.chaine)

    def analyze_nd_block(self, node):
        """Analyze block with new scope"""
        is_root_block = len(self.symbol_table.scopes) == 1  # Check if this is the outermost block
        
        self.symbol_table.enter_scope()
        
        if is_root_block:
            # For the root block, count ALL declarations recursively
            node.total_declarations = self._count_all_declarations(node)
            node.is_root = True
        else:
            # For nested blocks, don't emit resn
            node.is_root = False
        
        # Count direct declarations for this scope
        node.direct_decl_count = sum(1 for child in node.enfant if child.type == ND_DECL)
        
        # Analyze all children
        for child in node.enfant:
            self.analyze(child)
        
        # Store number of variables to drop when leaving scope
        node.drop_count = self.symbol_table.leave_scope()
    
    def _count_all_declarations(self, node):
        """Count all declarations recursively"""
        count = 0
        if node.type == ND_DECL:
            return 1
        
        for child in node.enfant:
            count += self._count_all_declarations(child)
        
        return count


class CodeGenerator:
    def __init__(self, symbol_table):
        self.symbol_table = symbol_table

    def generate(self, node):
        """Generate code for a node"""
        method_name = f'gen_{node.type}'
        method = getattr(self, method_name, None)
        if method:
            method(node)
        else:
            raise ValueError(f"Unknown node type: {node.type}")

    def gen_nd_const(self, node):
        print("push", node.valeur)

    def gen_nd_not(self, node):
        self.generate(node.enfant[0])
        print("not")

    def gen_nd_neg(self, node):
        self.generate(node.enfant[0])
        print("neg")

    def gen_nd_add(self, node):
        self.generate(node.enfant[0])
        self.generate(node.enfant[1])
        print("add")

    def gen_nd_sub(self, node):
        self.generate(node.enfant[0])
        self.generate(node.enfant[1])
        print("sub")

    def gen_nd_mul(self, node):
        self.generate(node.enfant[0])
        self.generate(node.enfant[1])
        print("mul")

    def gen_nd_div(self, node):
        self.generate(node.enfant[0])
        self.generate(node.enfant[1])
        print("div")

    def gen_nd_ident(self, node):
        print("load", node.address)

    def gen_nd_debug(self, node):
        self.generate(node.enfant[0])
        print("debug")

    def gen_nd_drop(self, node):
        self.generate(node.enfant[0])
        print("drop")

    def gen_nd_decl(self, node):
        """Declarations don't generate code by themselves"""
        pass

    def gen_nd_assign(self, node):
        self.generate(node.enfant[1])  # Generate expression
        print("dup")
        print("set", node.enfant[0].address)
        print("drop", "1")

    def gen_nd_block(self, node):
        # Only emit resn for the root block with total count
        if hasattr(node, 'is_root') and node.is_root and node.total_declarations > 0:
            print("resn", node.total_declarations)

        # Generate code for all children
        for child in node.enfant:
            self.generate(child)

        # Only emit drop for the root block with total count
        if hasattr(node, 'is_root') and node.is_root:
            # Calculate total variables to drop (sum of all scopes)
            total_to_drop = self.symbol_table.next_address
            if total_to_drop > 0:
                print("drop", total_to_drop)

    def gen_nd_if(self, node):
        self.generate(node.enfant[0])  # Condition
        
        L1 = new_label()
        L2 = new_label()
        
        print("jumpf", L1)
        self.generate(node.enfant[1])  # Then branch
        print("jump", L2)
        print(L1 + ":")
        if len(node.enfant) > 2:  # Else branch exists
            self.generate(node.enfant[2])
        print(L2 + ":")


def compile_code(source_code, show_ast=False):
    """Complete compilation pipeline"""
    # Lexical analysis
    lexer = Lexer(source_code)
    
    # Syntactic analysis
    symbol_table = SymbolTable()
    parser = Parser(lexer, symbol_table)
    ast = parser.parse_instruction()
    
    # Semantic analysis
    analyzer = SemanticAnalyzer(symbol_table)
    analyzer.analyze(ast)
    
    # Show AST if requested
    if show_ast:
        print("AST: ", end="")
        ast.afficher()
        print()
    
    # Code generation
    print("Instructions:")
    generator = CodeGenerator(symbol_table)
    generator.generate(ast)


if __name__ == "__main__":
    print("\n--- Test 1: constante ---")
    compile_code("42;", show_ast=True)

    print("\n--- Test 2: addition ---")
    compile_code("3 + 5;", show_ast=True)

    print("\n--- Test 3: debug ---")
    compile_code("debug 7;", show_ast=True)

    print("\n--- Test 4: bloc ---")
    compile_code("{ 1 + 2; debug 3; }", show_ast=True)

    print("\n--- Test 5: test prof ---")
    compile_code("{ int x ; x=3; { x=2; int x ; x=5; } x=7;}", show_ast=True)