FROM python:3.10.6

RUN pip install --upgrade pip

WORKDIR /app

ADD main.py requirements.txt database.py hashing.py models.py schema.py /app/

RUN pip install -r requirements.txt

EXPOSE 8000
# Expose a port inside the container on which services run

CMD ["gunicorn" ,"-w", "4", "-k", "uvicorn.workers.UvicornWorker" , "--bind", "0.0.0.0:8000", "main:app"]