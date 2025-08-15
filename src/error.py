class SemanticError(Exception):
    """Se lanza cuando hay errores semánticos acumulados."""
    pass

def format_ctx(ctx, msg: str) -> str:
    """Intenta formatear [L: C] si el ctx trae token .start"""
    tok = getattr(ctx, "start", None)
    if tok is not None:
        return f"[L{tok.line}:C{tok.column}] {msg}"
    return msg
