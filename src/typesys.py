# Sistema de tipos simple
INT, FLOAT, BOOL, STRING, VOID, ANY = "int", "float", "bool", "string", "void", "<any>"
NUMS = {INT, FLOAT}

PROMO = {
    (INT, INT): INT, (INT, FLOAT): FLOAT,
    (FLOAT, INT): FLOAT, (FLOAT, FLOAT): FLOAT,
}

def is_num(t: str) -> bool:
    return t in NUMS

def same(a: str, b: str) -> bool:
    return a == b

def can_assign(lhs: str, rhs: str) -> bool:
    """¿Se puede asignar rhs a lhs? Permite int->float."""
    if lhs == rhs:
        return True
    if lhs in NUMS and rhs in NUMS:
        # p.ej. float = int ✓; int = float ✗
        return PROMO.get((lhs, rhs)) == lhs
    return False
