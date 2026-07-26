# 1. Base Image com UV integrado (Ultra rápido)
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Evita arquivos .pyc e força stdout imediato
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1

WORKDIR /app

# Copia os arquivos de definição de dependência e README para cachear o build
COPY pyproject.toml uv.lock README.md ./

# Instala apenas as dependências de terceiros para máximo aproveitamento de cache
RUN uv sync --frozen --no-cache --no-install-project

# Copia o código-fonte da aplicação
COPY . .

# Finaliza a instalação incluindo a própria aplicação
RUN uv sync --frozen --no-cache

EXPOSE 8000

# Executa o servidor FastAPI via uvicorn gerenciado pelo uv
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
