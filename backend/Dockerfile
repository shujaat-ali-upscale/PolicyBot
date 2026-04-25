FROM python:3.11-slim

WORKDIR /app

# Install CPU-only torch before requirements.txt so pip won't pull the 2 GB CUDA wheel
# when sentence-transformers requests torch as a dependency.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
