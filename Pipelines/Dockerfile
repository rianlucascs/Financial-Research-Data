# Use Python 3.10 slim image como base
FROM python:3.10-slim

# Define diretório de trabalho
WORKDIR /app

# Instala dependências do sistema necessárias para Selenium e Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instala Chrome (método moderno sem apt-key)
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# Copia requirements.txt
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia o projeto inteiro
COPY Pipelines ./Pipelines

# Define variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/Pipelines
ENV PIPELINE_NAME=b3_indices_segmentos_setoriais
ENV PIPELINE_ENV=dev

# Cria script de entrada flexível
RUN echo '#!/bin/bash\n\
python -c "\n\
import os\n\
pipeline_name = os.getenv(\"PIPELINE_NAME\", \"b3_indices_segmentos_setoriais\")\n\
pipeline_env = os.getenv(\"PIPELINE_ENV\", \"dev\")\n\
import importlib\n\
module = importlib.import_module(f\"src.pipelines.{pipeline_name}.pipeline\")\n\
module.main(env=pipeline_env)\n\
"' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# Define o comando padrão
CMD ["/app/entrypoint.sh"]
