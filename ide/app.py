import os, sys, io, tempfile
import streamlit as st
from streamlit_ace import st_ace
from antlr4 import InputStream, CommonTokenStream
from antlr4.error.ErrorListener import ErrorListener

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(ROOT, "program"))
sys.path.append(os.path.join(ROOT, "src"))

from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from semantics.errors import SyntaxErrorListener
from semantics.checker import SemanticChecker
from semantics.treeviz import render_parse_tree_svg

st.set_page_config(page_title="Compiscript IDE", page_icon="🧪", layout="wide")
st.title("🧪 Compiscript IDE – Análisis Sintáctico y Semántico")

code = st_ace(
    language="text",
    theme="dracula",
    auto_update=True,
    value='''    let x: integer = 10;
const PI: integer = 314;
function suma(a: integer, b: integer): integer {
  return a + b;
}
let y: integer;
y = suma(x, 5);
if (y > 10) {
  print("Mayor a 10");
} else {
  print("Menor o igual");
}''',
    min_lines=20, max_lines=40, font_size=14, show_gutter=True
)

col1, col2 = st.columns([1,1])
run = col1.button("🧩 Analizar")
if run:
    input_stream = InputStream(code)
    lexer = CompiscriptLexer(input_stream)
    tokens = CommonTokenStream(lexer)
    parser = CompiscriptParser(tokens)

    syn = SyntaxErrorListener()
    parser.removeErrorListeners()
    parser.addErrorListener(syn)

    tree = parser.program()

    if syn.has_errors:
        st.error("Errores sintácticos:")
        for e in syn.errors:
            st.write(e)
    else:
        checker = SemanticChecker()
        checker.visit(tree)
        if checker.errors:
            st.error("Errores semánticos:")
            for e in checker.errors:
                st.write(e)
        else:
            st.success("Semantic OK ✅")

        try:
            svg = render_parse_tree_svg(tree, parser.ruleNames)
            st.subheader("Árbol (Parse Tree)")
            st.image(svg)
        except Exception as ex:
            st.info("No se pudo renderizar el árbol (¿instalaste Graphviz?).")
