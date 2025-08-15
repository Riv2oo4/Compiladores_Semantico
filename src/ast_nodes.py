from typing import Any, List, Optional

class Node: pass
class Stmt(Node): pass
class Expr(Node):
    inferred_type: Optional[str] = None

class Program(Node):
    def __init__(self, decls: List[Node]): self.decls = decls
