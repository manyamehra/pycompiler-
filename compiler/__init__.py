from lexer import Lexer
from dataclasses import dataclass, field
from typing import List, Optional, Any

K_BLOCK      = "block"
K_ASSIGN     = "assign"
K_RETURN     = "return"
K_IF         = "if"
K_BINOP      = "binop"
K_NUMBER     = "number"
K_IDENTIFIER = "identifier"
K_FOR = "for"

@dataclass
class Node:
    kind: str                      
    value: Any = None              
    children: List["Node"] = field(default_factory=list) 

    def add(self, child: "Node") -> "Node":
        self.children.append(child)
        return self

    def add2(self, left: "Node", right: "Node") -> "Node":
        self.children.extend([left, right])
        return self

    @staticmethod
    def leaf(kind: str, value: Any = None) -> "Node":
        return Node(kind=kind, value=value)

    @staticmethod
    def unary(kind: str, value: Any, child: "Node") -> "Node":
        return Node(kind=kind, value=value, children=[child])

    @staticmethod
    def binary(kind: str, value: Any, left: "Node", right: "Node") -> "Node":
        return Node(kind=kind, value=value, children=[left, right])

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        head = f"{self.kind}" + (f"({self.value})" if self.value is not None else "")
        if not self.children:
            return pad + head
        return pad + head + "\n" + "\n".join(ch.pretty(indent + 1) for ch in self.children)

class Parser:
    def __init__(self, lexer):
        self.lx = lexer

    def _t(self): return self.lx.peek()[0]
    def _v(self): return self.lx.peek()[1]

    def accept(self, token_type: str) -> bool:
        if self._t() == token_type:
            self.lx.next()
            return True
        return False

    def expect(self, token_type: str, msg: Optional[str] = None):
        if not self.accept(token_type):
            got_t, got_v = self.lx.peek()
            raise SyntaxError(msg or f"Attendu {token_type}, trouvé {got_t} ({got_v!r})")

    def parse_program(self) -> Node:
        items: List[Node] = []
        while self._t() != "tok_EOF":
            items.append(self.parse_stmt())
        return Node(kind=K_BLOCK, children=items)

    def parse_block(self) -> Node:
        self.expect("tok_lcurly", "‘{’ attendu")
        items: List[Node] = []
        while self._t() != "tok_rcurly":
            if self._t() == "tok_EOF":
                raise SyntaxError("‘}’ manquant")
            items.append(self.parse_stmt())
        self.expect("tok_rcurly")
        return Node(kind=K_BLOCK, children=items)

    def parse_stmt(self) -> Node:
        if self._t() == "tok_lcurly":
            return self.parse_block()

        if self._t() == "tok_motscle" and self._v() == "if":
            self.lx.next()
            self.expect("tok_lparen", "‘(’ attendu")
            cond = self.parse_expr()
            self.expect("tok_rparen", "‘)’ attendu")
            then_node = self.parse_stmt() if self._t() != "tok_lcurly" else self.parse_block()
            else_node = None
            if self._t() == "tok_motscle" and self._v() == "else":
                self.lx.next()
                else_node = self.parse_stmt() if self._t() != "tok_lcurly" else self.parse_block()
            n = Node(kind=K_IF, children=[cond, then_node])
            if else_node is not None:
                n.add(else_node)
            return n
        if self._t() == "tok_motscle" and self._v() == "for":
            self.lx.next() 
            self.expect("tok_lparen", "‘(’ attendu après for")

            init = None
            if self._t() != "tok_semicolon":
                init = self.parse_stmt()
            self.expect("tok_semicolon")

            cond = None
            if self._t() != "tok_semicolon":
                cond = self.parse_expr()
            self.expect("tok_semicolon")

            incr = None
            if self._t() != "tok_rparen":
                incr = self.parse_expr()
            self.expect("tok_rparen")

            body = self.parse_stmt() if self._t() != "tok_lcurly" else self.parse_block()

            return Node(kind=K_FOR, children=[init, cond, incr, body])

        # return
        if self._t() == "tok_motscle" and self._v() == "return":
            self.lx.next()
            val = self.parse_expr()
            self.expect("tok_semicolon", "‘;’ manquant après return")
            return Node(kind=K_RETURN, children=[val])

        # assign
        if self._t() == "tok_identifiant":
            name = self._v()
            self.lx.next()
            self.expect("tok_egal", "‘=’ attendu")
            expr = self.parse_expr()
            self.expect("tok_semicolon", "‘;’ manquant en fin d’instruction")
            # affectation = nœud avec 2 enfants: ident (feuille) + valeur
            return Node(kind=K_ASSIGN).add(Node.leaf(K_IDENTIFIER, name)).add(expr)

        got_t, got_v = self.lx.peek()
        raise SyntaxError(f"Début d’instruction invalide: {got_t} ({got_v!r})")

    def parse_expr(self) -> Node:
        node = self.parse_sum()
        while self._t() in ("tok_equalto", "tok_notequal", "tok_lt", "tok_le", "tok_gt", "tok_ge"):
            op = self._v()
            self.lx.next()
            right = self.parse_sum()
            node = Node.binary(K_BINOP, op, node, right)
        return node

    def parse_sum(self) -> Node:
        node = self.parse_term()
        while self._t() in ("tok_plus", "tok_minus"):
            op = self._v()
            self.lx.next()
            right = self.parse_term()
            node = Node.binary(K_BINOP, op, node, right)
        return node

    def parse_term(self) -> Node:
        node = self.parse_factor()
        while self._t() in ("tok_star", "tok_slash"):
            op = self._v()
            self.lx.next()
            right = self.parse_factor()
            node = Node.binary(K_BINOP, op, node, right)
        return node

    def parse_factor(self) -> Node:
        t, v = self.lx.peek()
        if t == "tok_chiffre":
            self.lx.next()
            return Node.leaf(K_NUMBER, v)
        if t == "tok_identifiant":
            self.lx.next()
            return Node.leaf(K_IDENTIFIER, v)
        if self.accept("tok_lparen"):
            node = self.parse_expr()
            self.expect("tok_rparen", "‘)’ manquante")
            return node
        raise SyntaxError(f"Facteur invalide: {t} ({v!r})")

def afficher_arbre(racine: Node):
    print(racine.pretty())

if __name__ == "__main__":
    code = " a = 12 + 3*5 ;"
    lx = Lexer(code)       
    p  = Parser(lx)
    ast = p.parse_program()
    afficher_arbre(ast)
