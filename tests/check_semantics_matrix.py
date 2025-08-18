# tests/check_semantics_matrix.py
import os, sys, re
from antlr4 import InputStream, CommonTokenStream

ROOT = os.path.dirname(os.path.abspath(__file__))
# Ajusta si tu árbol de carpetas difiere
sys.path.append(os.path.join(ROOT, "program"))
sys.path.append(os.path.join(ROOT, "src"))

from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from semantics.errors import SyntaxErrorListener
from semantics.checker import SemanticChecker

def run_semantic(code: str):
    input_stream = InputStream(code)
    lexer = CompiscriptLexer(input_stream)
    tokens = CommonTokenStream(lexer)
    parser = CompiscriptParser(tokens)
    syn = SyntaxErrorListener()
    parser.removeErrorListeners()
    parser.addErrorListener(syn)
    tree = parser.program()
    if getattr(syn, "has_errors", False):
        return ("syntax", syn.errors)

    checker = SemanticChecker()
    checker.visit(tree)
    errs = getattr(checker, "errors", [])
    return ("ok" if not errs else "semerr", errs)

def assert_expect(name, code, expect_ok: bool):
    status, errs = run_semantic(code)
    ok_now = (status == "ok")
    if ok_now != expect_ok:
        print(f"FAIL: {name} (esperado={'OK' if expect_ok else 'ERR'}, obtuvo={'OK' if ok_now else status})")
        for e in errs or []:
            print("   ->", e)
        return False
    print(f"PASS: {name}")
    return True

# --- Metamorphic: renombrar identificadores y esperar mismo resultado
def rename_idents(src: str, mapping: dict):
    def repl(m):
        w = m.group(0)
        return mapping.get(w, w)
    # \b evita renombrar subcadenas
    pattern = re.compile(r"\b(" + "|".join(map(re.escape, mapping.keys())) + r")\b")
    return pattern.sub(repl, src)

def expect_same_result_under_rename(name, code, mapping):
    st1 = run_semantic(code)[0]
    mutated = rename_idents(code, mapping)
    st2 = run_semantic(mutated)[0]
    same = (st1 == st2)
    if not same:
        print(f"FAIL: metamorphic {name} (antes={st1}, después={st2})")
        return False
    print(f"PASS: metamorphic {name}")
    return True

def main():
    passed, failed = 0, 0

    def check(name, code, ok):
        nonlocal passed, failed
        if assert_expect(name, code, ok): passed += 1
        else: failed += 1

    # ========= TIPOS: Aritmética (solo integer en tu gramática) =========
    arith_ops = ["+", "-", "*", "/", "%"]
    for op in arith_ops:
        check(f"arith_ok_{op}",
        f"""
        let a: integer = 4;
        let b: integer = 2;
        let r: integer = a {op} b;
        """, True)

        check(f"arith_err_{op}_with_string",
        f"""
        let a: integer = 4;
        let s: string = "x";
        let r: integer = a {op} s;  // debe fallar
        """, False)

    # ========= Lógicas =========
    for op in ["&&", "||"]:
        check(f"logic_ok_{op}", f"""
        let p: boolean = true;
        let q: boolean = false;
        let r: boolean = p {op} q;
        """, True)
        check(f"logic_err_{op}_int", f"""
        let x: integer = 1;
        let r: boolean = x {op} true;
        """, False)

    check("logic_ok_not", """
    let p: boolean = false;
    let q: boolean = !p;
    """, True)

    check("logic_err_not_int", """
    let x: integer = 0;
    let q: boolean = !x;   // debe fallar
    """, False)

    # ========= Comparaciones =========
    for op in ["==", "!="]:
        check(f"eq_ok_{op}_same_type", f"""
        let a: string = "hi";
        let b: string = "yo";
        let c: boolean = (a {op} b);
        """, True)
        check(f"eq_err_{op}_mixed", f"""
        let a: integer = 1;
        let b: boolean = true;
        let c: boolean = (a {op} b);
        """, False)

    for op in ["<", "<=", ">", ">="]:
        check(f"rel_ok_{op}", f"""
        let x: integer = 3;
        let y: integer = 5;
        let b: boolean = (x {op} y);
        """, True)
        check(f"rel_err_{op}_string", f"""
        let a: string = "a";
        let b: string = "b";
        let c: boolean = (a {op} b);  // relacional no numérico
        """, False)

    # ========= Asignaciones =========
    check("assign_ok_same_type", """
    let n: integer = 3;
    n = 7;
    """, True)

    check("assign_err_type_mismatch", """
    let n: integer = 3;
    n = "hola";  // mismatch
    """, False)

    # ========= Constantes =========
    check("const_ok_type", """
    const LIM: integer = 10;
    """, True)

    check("const_err_type", """
    const K: integer = true;  // mismatch
    """, False)

    # ========= Listas =========
    check("array_ok", """
    let xs: integer[] = [1,2,3];
    let v: integer = xs[1];
    """, True)

    check("array_err_mixed", """
    let xs: integer[] = [1,true,3];
    """, False)

    check("array_err_index_type", """
    let xs: integer[] = [1,2,3];
    let v: integer = xs[false];
    """, False)

    # ========= Ámbitos =========
    check("undeclared_var", "y = 3;", False)

    check("redeclare_same_scope", """
    let x: integer = 1;
    let x: integer = 2;
    """, False)

    check("shadowing_ok", """
    let x: integer = 1;
    { let x: integer = 2; }
    """, True)

    check("access_out_of_block", """
    { let t: integer = 7; }
    let z: integer = t;
    """, False)

    check("nested_envs", """
    function f(a: integer): integer {
        let x: integer = a + 1;
        { let x: integer = 100; }
        return x;
    }
    let r: integer = f(2);
    """, True)

    # ========= Funciones =========
    check("call_ok", """
    function suma(a: integer, b: integer): integer { return a + b; }
    let r: integer = suma(3,4);
    """, True)

    check("call_err_arity_type", """
    function suma(a: integer, b: integer): integer { return a + b; }
    let r1: integer = suma(3);
    let r2: integer = suma(3, true);
    """, False)

    check("ret_ok", """
    function esPos(n: integer): boolean { return n > 0; }
    """, True)

    check("ret_err", """
    function esPos(n: integer): boolean { return n + 1; }
    """, False)

    check("return_outside", "return 5;", False)

    check("recursion_ok", """
    function fact(n: integer): integer {
        if (n <= 1) { return 1; }
        else { return n * fact(n - 1); }
    }
    let f3: integer = fact(3);
    """, True)

    check("dup_functions", """
    function foo(a: integer): integer { return a; }
    function foo(a: integer): integer { return a + 1; }
    """, False)

    check("dup_params", """
    function f(a: integer, a: integer): integer { return a; }
    """, False)

    check("nested_closure_ok", """
    function outer(a: integer): integer {
        function inner(b: integer): integer { return a + b; }
        return inner(5);
    }
    let r: integer = outer(3);
    """, True)

    # ========= Control de flujo =========
    check("if_bool_ok", """
    let y: integer = 10;
    if (y > 5) { let ok: boolean = true; }
    """, True)

    check("if_nonbool_err", """
    let y: integer = 10;
    if (y) { let ok: boolean = true; }
    """, False)

    check("while_ok", """
    let i: integer = 0;
    while (i < 2) { i = i + 1; }
    """, True)

    check("while_nonbool_err", """
    let i: integer = 0;
    while (i) { i = i + 1; }
    """, False)

    check("do_while_ok", """
    let i: integer = 0;
    do { i = i + 1; } while (i < 3);
    """, True)

    check("for_ok", """
    for (let i: integer = 0; i < 3; i = i + 1) { }
    """, True)

    check("for_nonbool_err", """
    for (let i: integer = 0; i + 1; i = i + 1) { }
    """, False)

    check("break_continue_in_loop_ok", """
    let i: integer = 0;
    while (i < 2) {
        i = i + 1;
        if (i == 1) { continue; }
        if (i == 2) { break; }
    }
    """, True)

    check("break_outside_err", "break;", False)
    check("continue_outside_err", "continue;", False)

    check("dead_code_after_return_err", """
    function g(): integer {
        return 1;
        let z: integer = 2;
    }
    """, False)

    # ========= Clases / objetos =========
    check("class_attr_and_this_ok", """
    class Punto {
        let x: integer;
        function setX(v: integer) { this.x = v; }
        function getX(): integer { return this.x; }
    }
    let p: Punto = new Punto();
    p.setX(5);
    let n: integer = p.getX();
    """, True)

    check("class_unknown_attr_err", """
    class Punto { let x: integer; }
    let p: Punto = new Punto();
    let y: integer = p.y;
    """, False)

    # ========= Expresiones sin sentido =========
    check("multiply_function_err", """
    function f(): integer { return 2; }
    let x: integer = f * 3;
    """, False)

    # ===== Metamórficas: renombrar identifers y esperar mismo resultado =====
    expect_same_result_under_rename(
        "rename_simple",
        """
        function suma(a: integer, b: integer): integer { return a + b; }
        let r: integer = suma(3,4);
        """,
        {"suma":"add1", "a":"aa", "b":"bb", "r":"res"}
    )

    print("\nResumen: PASSED =", passed, "FAILED =", failed)
    if failed: sys.exit(1)

if __name__ == "__main__":
    main()
