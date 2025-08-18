# Compiscript – Laboratorio de Análisis Semántico (Plantilla lista para usar)

## 1) Requisitos previos
- **Python 3.10+**
- **Java JDK 17+** (para ANTLR y opcionalmente `grun`)
- **Graphviz** instalado en el sistema (necesario para renderizar el árbol)  
  - Windows: https://graphviz.org/download/ (agregar `dot.exe` al PATH)
  - macOS: `brew install graphviz`
  - Linux: `sudo apt-get install graphviz`

## 2) Crear entorno y dependencias
```bash
cd /mnt/data/compiscript_lab
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
```

## 3) Instalar ANTLR 4.13.1 (si aún no lo tienes)
Descarga el jar: https://www.antlr.org/download/antlr-4.13.1-complete.jar  
Colócalo por ejemplo en `C:\antlr\antlr-4.13.1-complete.jar` (Windows) o `~/lib/antlr-4.13.1-complete.jar` (Unix).

Aliases útiles:
- PowerShell (Windows):
  ```powershell
  setx ANTLR_JAR "C:\antlr\antlr-4.13.1-complete.jar"
  setx CLASSPATH ".;%%ANTLR_JAR%%;"
  function antlr4 { java -Xmx500M -cp "$env:ANTLR_JAR" org.antlr.v4.Tool @Args }
  function grun   { java -Xmx500M -cp "$env:ANTLR_JAR" org.antlr.v4.gui.TestRig @Args }
  ```
- Bash (macOS/Linux), agrega a `~/.bashrc` o `~/.zshrc`:
  ```bash
  export ANTLR_JAR=~/lib/antlr-4.13.1-complete.jar
  export CLASSPATH=".:$ANTLR_JAR:$CLASSPATH"
  alias antlr4='java -Xmx500M -cp "$ANTLR_JAR" org.antlr.v4.Tool'
  alias grun='java -Xmx500M -cp "$ANTLR_JAR" org.antlr.v4.gui.TestRig'
  ```

## 4) Generar Lexer/Parser (Python target)
```bash
cd program
antlr4 -Dlanguage=Python3 Compiscript.g4
```

## 5) Ejecutar el parser + chequeo semántico por CLI
```bash
# desde la carpeta program
python Driver.py program.cps
```

- Si hay errores sintácticos o semánticos se listarán con línea/columna.
- Si todo está OK verás: `Semantic OK`.

## 6) Ejecutar el IDE bonito (web) con Streamlit
```bash
streamlit run ide/app.py
```
Abre el navegador en la URL mostrada. Podrás escribir Compiscript, compilar y ver el árbol/símbolos/errores.

## 7) Correr pruebas
```bash
pytest -q
```
