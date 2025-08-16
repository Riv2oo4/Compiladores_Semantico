# server/app.py
import os, sys, re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import traceback
# --- Rutas para importar tu proyecto (src/ y gen/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.driver import analyze_text
from src.error import SemanticError

app = FastAPI(title="Compiscript IDE API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True
)

class AnalyzeReq(BaseModel):
    code: str

RE_DIAG = re.compile(r"\[L(?P<line>\d+):C(?P<col>\d+)\]\s*(?P<msg>.+)")

def parse_diags(err_text: str):
    diags = []
    for ln in str(err_text).splitlines():
        m = RE_DIAG.search(ln)
        if m:
            diags.append({
                "line": int(m.group("line")),
                "column": int(m.group("col")),
                "message": m.group("msg"),
            })
    # Por si el analizador devolvió un único bloque de texto sin [L:C]:
    if not diags and err_text:
        diags.append({"line": 1, "column": 1, "message": str(err_text)})
    return diags

@app.post("/analyze")
def analyze(req: AnalyzeReq):
    """
    Retorna:
    {
      ok: bool,
      kind: "ok" | "syntax" | "semantic" | "internal",
      diagnostics: [{ line, column, message }]
    }
    """
    try:
        res = analyze_text(req.code)  # "OK" ó lanza excepción
        return {"ok": True, "kind": "ok", "diagnostics": []}
    except SyntaxError as e:
        return {"ok": False, "kind": "syntax", "diagnostics": parse_diags(str(e))}
    except SemanticError as e:
        return {"ok": False, "kind": "semantic", "diagnostics": parse_diags(str(e))}
    except Exception as e:
        # Error inesperado
        return {"ok": False, "kind": "internal", "diagnostics": parse_diags(str(e))}
# ... (todo igual arriba)
@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/analyze")
def analyze(req: AnalyzeReq):
    """
    Retorna:
    {
      ok: bool,
      kind: "ok" | "syntax" | "semantic" | "internal",
      diagnostics: [{ line, column, message }]
    }
    """
    try:
        res = analyze_text(req.code)  # "OK" ó lanza excepción
        return {"ok": True, "kind": "ok", "diagnostics": []}

    except SyntaxError as e:
        return {"ok": False, "kind": "syntax", "diagnostics": parse_diags(str(e))}

    except SemanticError as e:
        return {"ok": False, "kind": "semantic", "diagnostics": parse_diags(str(e))}

    except Exception as e:
        # Error inesperado -> log completo en server y mensaje claro al IDE
        tb = traceback.format_exc()
        print("Internal error on /analyze:\n", tb, file=sys.stderr)
        msg = f"{type(e).__name__}: {e}"
        return {
            "ok": False,
            "kind": "internal",
            "diagnostics": [{"line": 1, "column": 1, "message": msg}],
        }
