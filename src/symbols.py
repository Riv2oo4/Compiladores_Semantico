from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

@dataclass
class Symbol:
    name: str
    type: str

@dataclass
class VarSymbol(Symbol):
    is_const: bool = False

@dataclass
class FuncSymbol(Symbol):
    params: List[Tuple[str, str]] = field(default_factory=list)
    returns: str = "void"

@dataclass
class ClassSymbol(Symbol):
    fields: Dict[str, Symbol] = field(default_factory=dict)
    methods: Dict[str, FuncSymbol] = field(default_factory=dict)

class SymbolTable:
    """Pila de scopes: cada scope es un dict nombre->símbolo."""
    def __init__(self):
        self.scopes: List[Dict[str, Symbol]] = [ {} ]

    def push(self):
        self.scopes.append({})

    def pop(self):
        if len(self.scopes) == 1:
            raise RuntimeError("No se puede hacer pop del scope global")
        self.scopes.pop()

    def define(self, sym: Symbol):
        cur = self.scopes[-1]
        if sym.name in cur:
            raise RuntimeError(f"Redeclaración de identificador: {sym.name}")
        cur[sym.name] = sym

    def resolve(self, name: str) -> Optional[Symbol]:
        for s in reversed(self.scopes):
            if name in s:
                return s[name]
        return None
