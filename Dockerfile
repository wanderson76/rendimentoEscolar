FROM python:3.11-slim

# Evita que o Python grave ficheiros .pyc no disco
ENV PYTHONDONTWRITEBYTECODE 1
# Garante que as saídas dos logs apareçam imediatamente no terminal
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Instala dependências de sistema para comunicação com o PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instala as dependências do projeto
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código do projeto para dentro do container
COPY . /app/