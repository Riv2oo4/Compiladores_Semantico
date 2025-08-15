import sys
from antlr4 import *
from antlr4.error.ErrorListener import ErrorListener
from gen.CompiscriptLexer import CompiscriptLexer
from gen.CompiscriptParser import CompiscriptParser
from .semantics import SemanticAnalyzer        # <-- punto
from .error import SemanticError               # <-- punto


class ThrowingErrorListener(ErrorListener):
    def __init__(self): self.errors = []
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.errors.append(f"[L{line}:C{column}] {msg}")

def analyze_text(text: str) -> str:
    input_stream = InputStream(text)
    lexer = CompiscriptLexer(input_stream)
    token_stream = CommonTokenStream(lexer)

    parser = CompiscriptParser(token_stream)
    listener = ThrowingErrorListener()
    parser.removeErrorListeners()
    parser.addErrorListener(listener)

    tree = parser.program()

    if listener.errors:
        raise SyntaxError("\n".join(listener.errors))

    sem = SemanticAnalyzer()
    sem.visit(tree)
    sem.finish()
    return "OK"

if __name__ == "__main__":
    if len(sys.argv) < 1:
        print("Uso: python src/driver.py <archivo>", file=sys.stderr)
        sys.exit(64)

    path = sys.argv[1] if len(sys.argv) >= 2 else None
    try:
        code = open(path, encoding="utf8").read() if path else sys.stdin.read()
    except FileNotFoundError:
        print(f"Archivo no encontrado: {path}", file=sys.stderr)
        sys.exit(66)

    try:
        result = analyze_text(code)
        print(result)
        sys.exit(0)
    except SyntaxError as e:
        print("Errores de sintaxis:\n" + str(e), file=sys.stderr)
        sys.exit(2)
    except SemanticError as e:
        print("Errores semánticos:\n" + str(e), file=sys.stderr)
        sys.exit(3)
