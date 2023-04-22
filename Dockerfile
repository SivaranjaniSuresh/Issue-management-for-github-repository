FROM python:3.10.6
RUN pip install --upgrade pip

WORKDIR /app

ADD userinterface.py requirements.txt /app/

RUN pip install -r requirements.txt

ADD navigation /app/navigation/
ADD navigation/issuesearch.py /app/navigation/
ADD navigation/errorsearch.py /app/navigation/
ADD navigation/analytics.py /app/navigation/
ADD navigation/adminworkarea.py /app/navigation/

ADD backend /app/backend/
ADD backend/database.py /app/backend/

ADD utils /app/utils/
ADD utils/core_helpers.py /app/utils/

EXPOSE 8080

CMD ["streamlit", "run", "userinterface.py", "--server.port", "8080"]

