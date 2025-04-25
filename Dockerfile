# Use Python 3.11 slim base
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application
COPY . .

# Expose Flask app port
EXPOSE 5000

# Use Gunicorn and reference the app from run.py
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]
