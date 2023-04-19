FROM python:3.10.6

RUN pip install --upgrade pip

WORKDIR /app

ADD userinterface.py requirements.txt /app/

RUN pip install -r requirements.txt

# Install the latest compatible PyTorch CPU version
RUN pip install torch -f https://download.pytorch.org/whl/cpu/torch_stable.html

ADD navigation /app/navigation/
ADD navigation/issuesearch.py /app/navigation/

ADD backend /app/backend/
ADD backend/database.py /app/backend/

ADD utils /app/utils/
ADD utils/core_helpers.py /app/utils/

COPY ./bert-base-uncased /app/bert-base-uncased
COPY ./bert-base-uncased-tokenizer /app/bert-base-uncased-tokenizer

EXPOSE 8080

CMD ["streamlit", "run", "userinterface.py", "--server.port", "8080"]