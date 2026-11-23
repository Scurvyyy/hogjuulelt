FROM python:3.12-slim

WORKDIR /app

# Copy dependency list first so this layer is cached until requirements change
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code last (changes most often)
COPY app.py .

EXPOSE 3000

CMD ["gunicorn", "--bind", "0.0.0.0:3000", "app:app"]
