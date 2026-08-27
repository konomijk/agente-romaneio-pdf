FROM python:3.11-slim

WORKDIR /app

# Instala dependências primeiro (aproveita cache do Docker)
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copia o resto da aplicação
COPY backend/ ./backend/
COPY frontend/ ./frontend/

WORKDIR /app/backend

# Cloud Run e Render injetam a variável PORT automaticamente.
# Se não vier definida (ex: rodando local), usa 8080 como padrão.
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
