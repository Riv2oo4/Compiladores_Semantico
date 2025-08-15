from gen.CompiscriptVisitor import CompiscriptVisitor
from gen.CompiscriptParser import CompiscriptParser  # solo para tipos ctx si deseas
from .symbols import SymbolTable, VarSymbol, FuncSymbol
from .typesys import *
from .error import SemanticError, format_ctx

class SemanticAnalyzer(CompiscriptVisitor):
    def __init__(self):
        super().__init__()
        self.syms = SymbolTable()
        self.errors = []
        self.loop_depth = 0
        self.current_func: FuncSymbol | None = None

        # Funciones nativas opcionales
        self.syms.define(FuncSymbol("print", "func", [("x", ANY)], returns=VOID))

    # Helpers
    def note(self, ctx, msg: str):
        self.errors.append(format_ctx(ctx, msg))

    def finish(self):
        if self.errors:
            raise SemanticError("\n".join(self.errors))

    # ----- Programa y bloques -----
    def visitProgram(self, ctx):
        # visita todo
        return self.visitChildren(ctx)

    def visitBlock(self, ctx):
        self.syms.push()
        self.visitChildren(ctx)
        self.syms.pop()
        return None

    # ----- Declaración de variable -----
    # Regla esperada (ejemplo):
    # varDecl : (CONST)? type ID ('=' expr)? ';' ;
    def visitVarDecl(self, ctx):
        is_const = getattr(ctx, "CONST", lambda: None)()
        is_const = is_const is not None
        tname = ctx.type_().getText()
        name = ctx.ID().getText()
        init = getattr(ctx, "expr", lambda: None)()

        try:
            self.syms.define(VarSymbol(name, tname, is_const=is_const))
        except RuntimeError as e:
            self.note(ctx, str(e))

        if is_const and init is None:
            self.note(ctx, f"Constante '{name}' debe inicializarse")

        if init is not None:
            rhs_t = self.visit(ctx.expr())
            if not can_assign(tname, rhs_t):
                self.note(ctx, f"Incompatibilidad en inicialización de '{name}': {tname} = {rhs_t}")

        return None

    # ----- Asignación -----
    # assignStmt : ID '=' expr ';' ;
    def visitAssignStmt(self, ctx):
        name = ctx.ID().getText()
        sym = self.syms.resolve(name)
        if not sym:
            self.note(ctx, f"Variable no declarada: {name}")
            return None
        if isinstance(sym, VarSymbol) and sym.is_const:
            self.note(ctx, f"No se puede asignar a const '{name}'")

        rhs_t = self.visit(ctx.expr())
        if not can_assign(sym.type, rhs_t):
            self.note(ctx, f"Tipos incompatibles en asignación a '{name}': {sym.type} = {rhs_t}")
        return None

    # ----- Expresiones -----
    # Arith: left op right  (+ - * /)
    def visitArith(self, ctx):
        lt = self.visit(ctx.left)
        rt = self.visit(ctx.right)
        if not (is_num(lt) and is_num(rt)):
            self.note(ctx, f"Operación aritmética requiere numéricos, obtuve {lt} y {rt}")
            return VOID
        return PROMO[(lt, rt)]

    # Lógica binaria: && ||
    def visitLogicBin(self, ctx):
        lt = self.visit(ctx.left)
        rt = self.visit(ctx.right)
        if lt != BOOL or rt != BOOL:
            self.note(ctx, f"Operación lógica requiere booleanos, obtuve {lt} y {rt}")
        return BOOL

    # Lógica unaria: ! expr
    def visitLogicNot(self, ctx):
        t = self.visit(ctx.expr())
        if t != BOOL:
            self.note(ctx, f"'!' requiere booleano, obtuve {t}")
        return BOOL

    # Comparaciones: == != < <= > >=
    def visitCompare(self, ctx):
        lt = self.visit(ctx.left)
        rt = self.visit(ctx.right)
        if lt == rt:
            return BOOL
        if lt in NUMS and rt in NUMS:
            return BOOL
        self.note(ctx, f"Comparación entre tipos incompatibles: {lt} vs {rt}")
        return BOOL

    # Literales
    def visitNumberLit(self, ctx):
        text = ctx.getText()
        return FLOAT if ('.' in text or 'e' in text.lower()) else INT

    def visitBoolLit(self, ctx): return BOOL
    def visitStringLit(self, ctx): return STRING

    # Identificadores
    def visitIdExpr(self, ctx):
        name = ctx.ID().getText()
        sym = self.syms.resolve(name)
        if not sym:
            self.note(ctx, f"Identificador no declarado: {name}")
            return VOID
        return sym.type

    # ----- Control de flujo -----
    # ifStmt : 'if' '(' expr ')' block ('else' block)? ;
    def visitIfStmt(self, ctx):
        t = self.visit(ctx.expr())
        if t != BOOL:
            self.note(ctx, "La condición de if debe ser bool")
        self.visit(ctx.block(0))
        if ctx.block().__len__() > 1:
            self.visit(ctx.block(1))
        return None

    # whileStmt : 'while' '(' expr ')' block ;
    def visitWhileStmt(self, ctx):
        t = self.visit(ctx.expr())
        if t != BOOL:
            self.note(ctx, "La condición de while debe ser bool")
        self.loop_depth += 1
        self.visit(ctx.block())
        self.loop_depth -= 1
        return None

    # breakStmt : 'break' ';'
    def visitBreakStmt(self, ctx):
        if self.loop_depth == 0:
            self.note(ctx, "break solo puede usarse dentro de bucles")
        return None

    # continueStmt : 'continue' ';'
    def visitContinueStmt(self, ctx):
        if self.loop_depth == 0:
            self.note(ctx, "continue solo puede usarse dentro de bucles")
        return None

    # ----- Funciones -----
    # funcDecl : 'func' ID '(' params? ')' (':' type)? block ;
    def visitFuncDecl(self, ctx):
        name = ctx.ID().getText()
        ret = ctx.type_().getText() if ctx.type_() else VOID
        params = []
        if ctx.params():
            for p in ctx.params().param():
                params.append((p.ID().getText(), p.type_().getText()))
        # registrar firma
        try:
            self.syms.define(FuncSymbol(name, "func", params, returns=ret))
        except RuntimeError as e:
            self.note(ctx, str(e))
            return None

        fn = self.syms.resolve(name)
        self.syms.push()
        prev_fn = self.current_func
        self.current_func = fn
        # parámetros como const
        for pname, ptype in params:
            try:
                self.syms.define(VarSymbol(pname, ptype, is_const=True))
            except RuntimeError as e:
                self.note(ctx, str(e))
        self.visit(ctx.block())
        self.current_func = prev_fn
        self.syms.pop()
        return None

    # returnStmt : 'return' expr? ';'
    def visitReturnStmt(self, ctx):
        if not self.current_func:
            self.note(ctx, "return fuera del cuerpo de una función")
            return VOID
        rv = VOID if ctx.expr() is None else self.visit(ctx.expr())
        if not can_assign(self.current_func.returns, rv):
            self.note(ctx, f"Tipo de return incompatible: se declaró {self.current_func.returns}, se devuelve {rv}")
        return self.current_func.returns

    # callExpr : ID '(' args? ')' ;
    def visitCallExpr(self, ctx):
        name = ctx.ID().getText()
        sym = self.syms.resolve(name)
        if not isinstance(sym, FuncSymbol):
            self.note(ctx, f"Llamada a símbolo no-función: {name}")
            return VOID
        args = []
        if ctx.args():
            args = [self.visit(e) for e in ctx.args().expr()]
        if len(args) != len(sym.params):
            self.note(ctx, f"Número de argumentos inválido: se esperaban {len(sym.params)}, recibí {len(args)}")
        else:
            for i, (_, at) in enumerate(sym.params):
                if not can_assign(at, args[i]):
                    self.note(ctx, f"Argumento {i+1} incompatible: {at} <- {args[i]}")
        return sym.returns

    # ----- Listas (si aplica en tu gramática) -----
    # listLit : '[' (expr (',' expr)*)? ']'
    def visitListLit(self, ctx):
        es = [self.visit(e) for e in ctx.expr()]
        if not es:
            return "list<void>"
        t0 = es[0]
        for t in es[1:]:
            if t != t0:
                self.note(ctx, f"Lista heterogénea: {t0} vs {t}")
        return f"list<{t0}>"

    # indexExpr : expr '[' expr ']'
    def visitIndexExpr(self, ctx):
        at = self.visit(ctx.expr(0))
        it = self.visit(ctx.expr(1))
        if it != INT:
            self.note(ctx, f"Índice de lista debe ser int, obtuve {it}")
        if isinstance(at, str) and at.startswith("list<") and at.endswith(">"):
            return at[5:-1]
        self.note(ctx, f"Indexación sobre no-lista: {at}")
        return VOID
