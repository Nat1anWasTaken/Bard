FROM python:3.11.4-slim

COPY . .
RUN pip install -r requirements.txt

CMD ["python", "main.py"]