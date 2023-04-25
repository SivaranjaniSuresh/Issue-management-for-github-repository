FROM python:3.10.6

RUN pip install --upgrade pip

WORKDIR /app

ADD main.py requirements.txt database.py hashing.py models.py schema.py /app/

RUN pip install -r requirements.txt

# Install the latest compatible PyTorch CPU version
RUN pip install torch -f https://download.pytorch.org/whl/cpu/torch_stable.html

COPY ./bert-base-uncased /app/bert-base-uncased
COPY ./bert-base-uncased-tokenizer /app/bert-base-uncased-tokenizer

EXPOSE 8000
# Expose a port inside the container on which services run

CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--timeout", "200", "--bind", "0.0.0.0:8000", "main:app"]

