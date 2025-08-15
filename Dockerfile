FROM python:3.12-slim

# ---- SO y Java/Utils ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless \
    curl \
    bash-completion \
    fontconfig \
    fonts-dejavu-core \
    graphviz \
 && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:/opt/venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1

# ---- (Opcional) venv dedicado ----
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --upgrade pip

# ---- ANTLR y wrappers ----
# Asegúrate de tener el jar en esa ruta en tu proyecto
COPY antlr-4.13.1-complete.jar /usr/local/lib/antlr-4.13.1-complete.jar
COPY ./commands/antlr /usr/local/bin/antlr
COPY ./commands/grun  /usr/local/bin/grun
RUN chmod +x /usr/local/bin/antlr /usr/local/bin/grun

# ---- Dependencias Python ----
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# ---- Usuario no-root ----
ARG USER=appuser
ARG UID=1001
RUN useradd -m -u ${UID} ${USER}
USER ${USER}

# ---- Workspace ----
WORKDIR /program

# Si quieres generar el parser en build (descomenta y ajusta la ruta de tu .g4):
# RUN antlr -Dlanguage=Python3 -visitor -no-listener program/Compiscript.g4 -o gen

# Por defecto abre shell; cámbialo si ya quieres ejecutar tu driver
CMD ["/bin/bash"]