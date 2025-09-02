import re

# --- Mots-clés ---

KEYWORDS = {
   "elif","int" ,"if", "else", "while", "def", "return", "True", "False", "None","int", "AND","default","OR","breaks","continue","void","do"
}
# --- Spécification (les opérateurs à 2 chars AVANT ceux à 1 char) ---
TOKEN_SPEC = [
    # --- 2 caractères d’abord ---
    ("tok_ge",       r">="),
    ("tok_le",       r"<="),
    ("tok_equalto",  r"=="),
    ("tok_notequal", r"!="),
    ("tok_AND",      r"&&"),
    ("tok_OR",       r"\|\|"),

    # --- 1 caractère ensuite ---
    ("tok_gt",       r">"),
    ("tok_lt",       r"<"),
    ("tok_plus",     r"\+"),
    ("tok_minus",    r"-"),
    ("tok_star",     r"\*"),
    ("tok_slash",    r"/"),
    ("tok_percent",  r"%"),
    ("tok_not",      r"!"),
    ("tok_egal",     r"="),
    ("tok_lparen",   r"\("),
    ("tok_rparen",   r"\)"),
    ("tok_lcurly",   r"\{"),
    ("tok_rcurly",   r"\}"),
    ("tok_lbrack",   r"\["),
    ("tok_rbrack",   r"\]"),
    ("tok_semicolon",r";"),
    ("tok_colon",    r":"),

    ("tok_chiffre",     r"\d+"),
    ("tok_identifiant", r"[A-Za-z_][A-Za-z0-9_]*"),

    ("tok_espace",   r"[ \t]+"),
    ("tok_NEWLINE",  r"\n"),
    ("tok_MISMATCH", r"."),
]


# Méga-regex avec groupes nommés
MASTER_RE = re.compile("|".join(f"(?P<{n}>{p})" for n, p in TOKEN_SPEC))

class Lexer: #analyseur lexical 
    """
    Lexer incrémental :
      - __init__(text) : prépare le scanner et lit le 1er token
      - peek()         : renvoie le token courant (type, valeur) sans avancer
      - next()         : avance et renvoie le nouveau token courant
      - check(t)       : True si le token courant est de type t
    """
    def __init__(self, text: str):
        self.text = text
        self.scanner = MASTER_RE.scanner(text)
        self.line = 1
        self.col = 1
        self.current = None  # (type, valeur)
        self._advance()      # lire le 1er token utile

    def _advance(self):
        # saute espaces et gère les retours à la ligne
        while True:
            m = self.scanner.match()
            if not m: 
                self.current = ("tok_EOF", None)
                return
            kind = m.lastgroup
            lex  = m.group()

            if kind == "tok_NEWLINE":
                self.line += 1
                self.col = 1
                continue
            if kind == "tok_espace":
                self.col += len(lex)
                continue
            if kind == "tok_MISMATCH":
                raise SyntaxError(f"Caractère inattendu {lex!r} à la ligne {self.line}")

            # mots-clés vs identifiants
            if kind == "tok_identifiant" and lex in KEYWORDS:
                kind = "tok_motscle"

            # conversion des chiffres
            if kind == "tok_chiffre":
                value = int(lex)
            else:
                value = lex

            self.col += len(lex)
            self.current = (kind, value)
            return

    def peek(self):
        """Token courant sans avancer."""
        return self.current

    def next(self):
        """Avance d’un token et retourne le nouveau courant."""
        self._advance()
        return self.current

    def check(self, expected_type: str) -> bool:
        """Vérifie si le token courant est du type attendu."""
        return self.current and self.current[0] == expected_type

if __name__ == "__main__":
    code = "def f(x){ a = 12 + 3*5; if(a==27) return True; }"
    lx = Lexer(code)
    print("Premier token :", lx.peek())          
    while not lx.check("tok_EOF"):
        print(lx.peek())                         
        lx.next()                                