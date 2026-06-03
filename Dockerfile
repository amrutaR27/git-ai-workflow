FROM python:3.11-slim

WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Docker runs pip inside its own isolated environment here
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]