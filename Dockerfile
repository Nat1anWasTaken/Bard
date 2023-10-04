FROM python:3.12.0-slim

COPY . .
RUN pip install -r requirements.txt

CMD ["python", "main.py"]