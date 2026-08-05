FROM python:3.14.7-slim

COPY . .
RUN pip install -r requirements.txt

CMD ["python", "main.py"]