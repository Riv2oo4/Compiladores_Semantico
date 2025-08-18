# import os, sys, textwrap
# from antlr4 import InputStream, CommonTokenStream
# from antlr4.error.ErrorListener import ErrorListener

# # Make generated parser importable
# ROOT = os.path.dirname(os.path.dirname(__file__))
# sys.path.append(os.path.join(ROOT, "program"))
# sys.path.append(os.path.join(ROOT, "src"))

# from CompiscriptLexer import CompiscriptLexer
# from CompiscriptParser import CompiscriptParser
# from semantics.errors import SyntaxErrorListener
# from semantics.checker import SemanticChecker

# def compile_snippet(code: str):
#     input_stream = InputStream(code)
#     lexer = CompiscriptLexer(input_stream)
#     tokens = CommonTokenStream(lexer)
#     parser = CompiscriptParser(tokens)
#     syn = SyntaxErrorListener()
#     parser.removeErrorListeners()
#     parser.addErrorListener(syn)
#     tree = parser.program()
#     if syn.has_errors:
#         return syn.errors
#     checker = SemanticChecker()
#     checker.visit(tree)
#     return checker.errors

# def test_ok_simple_addition():
#     code = "let x: integer = 1 + 2;"
#     errs = compile_snippet(code)
#     assert errs == []

# def test_error_type_mismatch_assignment():
#     code = 'let x: integer = 1; x = "hola";'
#     errs = compile_snippet(code)
#     assert any("Asignación incompatible" in e for e in errs)

# def test_const_requires_init_type_check():
#     code = "const PI: integer = 3;"
#     errs = compile_snippet(code)
#     assert errs == []

# def test_if_requires_boolean():
#     code = "let x: integer = 1; if (x) {{ x = 2; }}"
#     errs = compile_snippet(code)
#     assert any("debe ser boolean" in e for e in errs)

# def test_break_only_in_loops():
#     code = "break;"
#     errs = compile_snippet(code)
#     assert any("solo se permite dentro de bucles" in e for e in errs)
# def test_string_into_int_should_fail():
#     code = 'let x: integer = "10";'
#     errs = compile_snippet(code)
#     assert any("Asignación incompatible" in e for e in errs)
    
# tests/test_semantics.py
# Ejecuta:  python tests/test_semantics.py
# Requiere: CompiscriptLexer/Parser en program/, checker+types+scope+symbols en src/semantics

from pathlib import Path
import sys, os

# === Localiza el proyecto (soporta ejecutarlo desde raíz o desde tests/) ===
HERE = Path(__file__).resolve().parent
ROOT = HERE if (HERE / "program").exists() else HERE.parent
sys.path.append(str(ROOT / "program"))
sys.path.append(str(ROOT / "src"))

from antlr4 import InputStream, CommonTokenStream
from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from semantics.errors import SyntaxErrorListener
from semantics.checker import SemanticChecker
from semantics.types import BooleanType, IntegerType, ArrayType  # para asserts internos si hiciera falta

# === Bandera por si clases/métodos aún no están listos en tu checker ===
SKIP_CLASSES = False   # pon True para saltar los tests de clases/métodos

def run_semantic(code: str):
    input_stream = InputStream(code)
    lexer = CompiscriptLexer(input_stream)
    tokens = CommonTokenStream(lexer)
    parser = CompiscriptParser(tokens)

    syn = SyntaxErrorListener()
    parser.removeErrorListeners()
    parser.addErrorListener(syn)
    tree = parser.program()

    if syn.has_errors:
        return ("syntax", syn.errors)

    checker = SemanticChecker()
    checker.visit(tree)
    errs = getattr(checker, "errors", [])
    return ("ok" if not errs else "semerr", errs)

# =========================
# 6 BLOQUES DE EJEMPLOS
# =========================

CASES = [
    # 1) Clases: atributos y métodos
    dict(
        group="01_clases_miembros",
        skip=SKIP_CLASSES,
        ok="""
            class Punto {
              let x: integer;
              function setX(v: integer) { this.x = v; }
              function getX(): integer { return this.x; }
            }
            let p: Punto = new Punto();
            p.setX(5);
            let n: integer = p.getX();
        """,
        err="""
            class Punto { let x: integer; }
            let p: Punto = new Punto();
            let y: integer = p.y;     // no existe y (o tipo incompatible)
            // p.setX("hola");        // si ya soportas métodos, descomenta y también debe fallar
        """,
    ),

    # 2) Control de flujo: if / while / for deben ser boolean
    dict(
        group="02_control_tipos",
        skip=False,
        ok="""
            let a: integer = 3;
            if (a > 1) { let ok: boolean = true; }
            while (a > 0) { a = a - 1; }
            for (let i: integer = 0; i < 2; i = i + 1) { }
        """,
        err="""
            let a: integer = 2;
            if (a) { }                      // condición no booleana
            while (a) { a = a - 1; }        // no booleana
            for (let i: integer = 0; i + 1; i = i + 1) { }  // no booleana
        """,
    ),

    # 3) Llamadas (funciones / métodos de objeto)
    dict(
        group="03_llamadas",
        skip=SKIP_CLASSES,   # funciones sí, métodos requieren soporte en checker
        ok="""
            function suma(a: integer, b: integer): integer { return a + b; }
            let r: integer = suma(2, 3);

            class Calc {
              function sum(a: integer, b: integer): integer { return a + b; }
            }
            let c: Calc = new Calc();
            let r2: integer = c.sum(2, 3);     // si aún no soportas métodos, activa SKIP_CLASSES
        """,
        err="""
            function suma(a: integer, b: integer): integer { return a + b; }
            let r1: integer = suma(3);         // aridad inválida
            let r2: integer = suma(3, true);   // tipo inválido

            class Calc {
              function sum(a: integer, b: integer): integer { return a + b; }
            }
            let c: Calc = new Calc();
            // let r3: integer = c.sum(2, true);   // descomenta si ya soportas métodos: debe fallar
        """,
    ),

    # 4) Ámbitos: shadowing y duplicidad
    dict(
        group="04_ambitos",
        skip=False,
        ok="""
            let x: integer = 1;
            { let x: integer = 2; }          // shadow válido
            function f(a: integer): integer {
                { let a: integer = 5; }      // parámetro sombreado en bloque: permitido si tu semántica lo permite
                return a;
            }
            let r: integer = f(2);
        """,
        err="""
            let x: integer = 1;
            let x: integer = 2;              // redeclaración mismo ámbito

            function g(a: integer, a: integer): integer { // parámetro duplicado
                return a;
            }
        """,
    ),

    # 5) Expresiones aritméticas y comparaciones
    dict(
        group="05_expr_aritmeticas",
        skip=False,
        ok="""
            let a: integer = 4;
            let b: integer = 2;
            let c: integer = a * b + 6;
            let cmp: boolean = (a < b) || (a != b);
        """,
        err="""
            let a: integer = 4;
            let s: string = "hola";
            let x: integer = a + s;      // int + string
            let bad: boolean = ("a" < "b"); // relacional no numérica
        """,
    ),

    # 6) Arrays: tipo de elementos e índice
    dict(
        group="06_arrays",
        skip=False,
        ok="""
            let xs: integer[] = [1,2,3];
            let v: integer = xs[1];
        """,
        err="""
            let xs: integer[] = [1,true,3];   // mezcla de tipos
            let w: integer = xs[false];       // índice no integer
        """,
    ),
]

# -------------------------------------------------------------

def write_samples():
    """Genera archivos .cps en /samples para usarlos en la presentación."""
    outdir = ROOT / "samples"
    outdir.mkdir(exist_ok=True)
    for block in CASES:
        (outdir / f"{block['group']}_OK.cps").write_text(block["ok"].strip() + "\n", encoding="utf-8")
        (outdir / f"{block['group']}_ERR.cps").write_text(block["err"].strip() + "\n", encoding="utf-8")
    print(f"Se generaron ejemplos en: {outdir}")

def run_case(name: str, code: str, expect_ok: bool):
    status, errs = run_semantic(code)
    ok_now = (status == "ok")
    if ok_now == expect_ok:
        print(f"PASS: {name}")
        return True
    print(f"FAIL: {name} (esperado={'OK' if expect_ok else 'ERR'}, obtuvo={'OK' if ok_now else status})")
    for e in errs or []:
        print("   ->", e)
    return False

def main():
    write_samples()
    passed = failed = 0

    for block in CASES:
        if block.get("skip", False):
            print(f"SKIP bloque {block['group']} (desactivado por bandera)")
            continue

        if run_case(block["group"] + " / OK", block["ok"], True): passed += 1
        else: failed += 1

        if run_case(block["group"] + " / ERR", block["err"], False): passed += 1
        else: failed += 1

    print("\nResumen:", f"{passed} PASS,", f"{failed} FAIL")
    if failed:
        sys.exit(1)

if __name__ == "__main__":
    main()
