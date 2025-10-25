from analyse_syntaxique import (
    Nd, parse,
    ND_CONST, ND_NOT, ND_NEG, ND_ADD, ND_SUB, ND_MUL, ND_DIV,
    ND_LT, ND_GT, ND_LE, ND_GE, ND_EQ, ND_NE,
    ND_IDENT, ND_DECL, ND_ASSIGN, ND_IF, ND_WHILE, ND_DEBUG, ND_BLOCK, ND_DROP,
    ND_ARRAY_DECL, ND_ARRAY_ACCESS, ND_ARRAY_ASSIGN, ND_DOWHILE,ND_FOR,
)


class SymbolTable:
    def __init__(self):
        self.scopes = [{}]  
        self.next_address = 0
        self.array_info={}

    def enter_scope(self):
        """Enter a new scope"""
        self.scopes.append({})

    def leave_scope(self):
        """Leave current scope and return number of variables to drop"""
        if len(self.scopes) <= 1:
            raise RuntimeError("Cannot leave global scope")
        scope = self.scopes.pop()
        return len(scope)

    def declare(self, name, array_size=None):
        """Declare a variable in current scope"""
        current_scope = self.scopes[-1]
        if name in current_scope:
            raise NameError(f"Variable '{name}' already declared in this scope")
        
        address = self.next_address
        current_scope[name] = address

        if array_size:
            self.array_info[address]=array_size
            self.next_address+=array_size
        else:
            self.next_address += 1

        return address
    
    def is_array(self, address):
        return address in self.array_info
    
    def get_array_size(self,address):
        return self.array_info.get(address)

    def lookup(self, name):
        """Look up a variable in all scopes (innermost first)"""
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise NameError(f"Variable '{name}' not declared")


# Label generation
label_counter = 0

def new_label():
    global label_counter
    label = f"L{label_counter}"
    label_counter += 1
    return label


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
    
    def analyze_nd_func_decl(self, node):
        # Nouvelle portée pour les parametre
        self.symbol_table.enter_scope()
        for param_node in node.enfant[:-1]: #tous sauf le corps 
            self.symbol_table.declare(param_node.chaine)
        self.analyze(node.enfant[-1]) # corps
        self.symbol_table.leave_scope()

    def analyze_nd_func_call(self, node):
        for arg in node.enfant:
            self.analyze(arg)

    def analyze_nd_return(self, node):
        self.analyze(node.enfant[0])

    def analyze_nd_decl(self, node):
        """Declare variable and store its address"""
        node.address = self.symbol_table.declare(node.chaine)

    def analyze_nd_assign(self, node):
        """Analyze assignment"""
        self.analyze(node.enfant[1])
        ident_node = node.enfant[0]
        ident_node.address = self.symbol_table.lookup(ident_node.chaine)

    def analyze_nd_block(self, node):
        """Analyze block with new scope"""
        is_root_block = len(self.symbol_table.scopes) == 1  
        
        self.symbol_table.enter_scope()
        
        if is_root_block:
            node.total_declarations = self._count_all_declarations(node)
            node.is_root = True
        else:
            node.is_root = False
        
        node.direct_decl_count = sum(1 for child in node.enfant if child.type == ND_DECL)
        
        for child in node.enfant:
            self.analyze(child)
        
        node.drop_count = self.symbol_table.leave_scope()

    def analyze_nd_array_decl(self, node):
        """Declare array and store its address"""
        node.address = self.symbol_table.declare(node.chaine, node.array_size)
    
    def analyze_nd_array_access(self,node):
        self.analyze(node.enfant[1])
        ident_node=node.enfant[0]
        ident_node.address = self.symbol_table.lookup(ident_node.chaine)

        # Verify it's actually an array
        if not self.symbol_table.is_array(ident_node.address):
            raise TypeError(f"'{ident_node.chaine}' is not an array")

    def analyze_nd_array_assign(self, node):
        """Analyze array assignment"""
        self.analyze(node.enfant[1])  # index
        self.analyze(node.enfant[2])  # value
        
        ident_node = node.enfant[0]
        ident_node.address = self.symbol_table.lookup(ident_node.chaine)
        
        if not self.symbol_table.is_array(ident_node.address):
            raise TypeError(f"'{ident_node.chaine}' is not an array")
    
    def _count_all_declarations(self, node):
        """Count all declarations recursively"""
        count = 0
        if node.type == ND_DECL:
            return 1
        if node.type == ND_ARRAY_DECL:  # NEW
            return node.array_size
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

    def gen_nd_lt(self, node):
        self.generate(node.enfant[0])
        self.generate(node.enfant[1])
        print("cmplt")

    def gen_nd_gt(self, node):
        self.generate(node.enfant[0])
        self.generate(node.enfant[1])
        print("cmpgt")

    def gen_nd_le(self, node):
        self.generate(node.enfant[0])
        self.generate(node.enfant[1])
        print("cmple")

    def gen_nd_ge(self, node):
        self.generate(node.enfant[0])
        self.generate(node.enfant[1])
        print("cmpge")

    def gen_nd_eq(self, node):
        self.generate(node.enfant[0])
        self.generate(node.enfant[1])
        print("cmpeq")

    def gen_nd_ne(self, node):
        self.generate(node.enfant[0])
        self.generate(node.enfant[1])
        print("cmpne")

    def gen_nd_ident(self, node):
        print("get", node.address)

    def gen_nd_debug(self, node):
        self.generate(node.enfant[0])
        print("send")

    def gen_nd_drop(self, node):
        self.generate(node.enfant[0])
        print("drop", 1)

    def gen_nd_decl(self, node):
        """Declarations don't generate code by themselves"""
        pass

    def gen_nd_assign(self, node):
        self.generate(node.enfant[1])  
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
        self.generate(node.enfant[0])  # condition
        L_else = new_label()
        L_end = new_label()
        print("jumpf", L_else)
        self.generate(node.enfant[1])  # bloc if
        print("jump", L_end)
        print(f".{L_else}")
        if len(node.enfant) > 2:       # bloc else
            self.generate(node.enfant[2])
        print(f".{L_end}")

    def gen_nd_for(self, node):
        L_start= new_label()
        L_end= new_label()
        self.generate(node.enfant[0]) # intialisation 
        print("."+L_start)

        self.generate(node.enfant[1]) #condition
        print("jumpf",L_end)

        self.generate(node.enfant[3]) #corps

        self.generate(node.enfant[2]) # incremen

        print("jump",L_start)

        print("."+L_end)

    def gen_nd_while(self, node):
        L_start = new_label()
        L_end = new_label()
        
        print("."+L_start)

        self.generate(node.enfant[0])  # Condition
        print("jumpf", L_end)
        self.generate(node.enfant[1])  # Body
        print("jump", L_start)
        print("."+L_end)

    def gen_nd_dowhile(self, node):
        L_start=new_label()
        L_condition=new_label()

        print(f".{L_start}")
        self.generate(node.enfant[0]) #on execute le corps 
        print(f".{L_condition}")
        self.generate(node.enfant[1]) #condition
        print("jumpt", L_start) #jump back if true
    
    def gen_nd_func_decl(self, node):
        func_name=node.chaine
        print(f".{func_name}")
        print("push BP")
        # paramètres déjà sur la pile → réserve variables locales
        body = node.enfant[-1]
        local_vars=sum(1 for c in body.enfant if c.type==ND_DECL)
        if local_vars > 0:
            print("resn",local_vars)

        #genere le corps
        self.generate(body)

        print("pop BP")
        print("ret")

    def gen_nd_func_call(self, node):
        func_name = node.chaine
        n_args= len(node.enfant)
        
        print(f"prep {func_name}")
        for arg in node.enfant:
            self.generate(arg)
        print(f"call {n_args}")

    def gen_nd_return(self,node):
        self.generate(node.enfant[0])
        print("pop BP")
        print("ret")

    def gen_nd_array_decl(self, node):
        """Array declarations reserve space during resn"""
        pass

    def gen_nd_array_access(self, node):
        """Generate code for array access: arr[index]"""
        print("push", node.enfant[0].address) #get base address of array
        self.generate(node.enfant[1])  # index
        print("add")
        print("read")

    def gen_nd_array_assign(self, node):
        """Generate code for array assignment: arr[index] = value;"""
        print("push", node.enfant[0].address)
        self.generate(node.enfant[1])  # index
        print("add")
        self.generate(node.enfant[2])
        print("write")
        
def compile_code(source_code, show_ast=False):
    """Complete compilation pipeline"""
    # Parse
    ast = parse(source_code)
    
    # Semantic analysis
    symbol_table = SymbolTable()
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

    print("\n--- Test 8: simple while ---")
    compile_code("{ int x; x=0; while (x<5) { debug x; x = x + 1; } }",show_ast=True)

    print("\n--- Test: Do-While ---")
    compile_code("{ int x; x = 0; do { debug x; x = x + 1;} while (x < 3);}", show_ast=True)

    print("\n--- Test 10: simple for ---")
    compile_code("{ int i; for (i = 0; i < 5; i = i + 1) { debug i; } }", show_ast=True)
    
    print("\n--- Test 11: fonction test  ---")
    compile_code("""{ 
    def carre(x) 
    { 
        return x * x; 
    }
        int y;
        y = carre(4);
        debug y;
    }""", show_ast=True)

    print("\n--- Test: Array with Loop ---")
    compile_code("""
    {
        int arr[5];
        int i;
        i = 0;
        while (i < 5) {
            arr[i] = i * 10;
            i = i + 1;
        }
        
        i = 0;
        while (i < 5) {
            debug arr[i];
            i = i + 1;
        }
    }
    """, show_ast=True)
