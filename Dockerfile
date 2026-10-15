FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY ui ./ui
COPY evaluation ./evaluation
COPY README.md .
COPY start-space.sh .
EXPOSE 7860
CMD ["sh", "start-space.sh"]
