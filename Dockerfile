FROM python:3.11-slim

WORKDIR /app

# Install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY app/       ./app/
COPY sql_env_client.py .
COPY inference.py .
COPY openenv.yaml .

# HuggingFace Spaces runs as non-root on port 7860
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Environment variables (set as Space secrets in HF)
ENV API_BASE_URL=${API_BASE_URL}
ENV MODEL_NAME=${MODEL_NAME}
ENV HF_TOKEN=${HF_TOKEN}
ENV SERVER_URL=http://localhost:7860

EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]