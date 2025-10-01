FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# If your main Flask entrypoint is main.py, use:
CMD ["python", "main.py"]
# Or if you use gunicorn with the app object in dashboard.py, use:
# CMD ["gunicorn", "dashboard:app", "--bind", "0.0.0.0:10000"]
