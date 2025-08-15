import pytest
from src.driver import analyze_text, SemanticError

def ok(code: str):
    assert analyze_text(code) == "OK"

def bad(code: str, frag: str):
    with pytest.raises(SemanticError) as ex:
        analyze_text(code)
    assert frag in str(ex.value)

def test_arith_ok():
    ok("int a = 1; float b = 2.0; float c = a + b;")

def test_assign_bad():
    bad("int a = 0; a = 1.5;", "int = float")

def test_if_bool():
    bad("int a = 1; if (a) { a = 2; }", "condición de if")

def test_const_init():
    bad("const int x;", "debe inicializarse")

def test_func_args():
    bad("func f(int x) { } f(true);", "Argumento 1 incompatible")
