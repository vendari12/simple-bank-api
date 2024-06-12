FROM python:3.12-slim-buster

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y gcc musl-dev && apt clean

RUN apt clean

WORKDIR /src

ENV PYTHONIOENCODING=UTF-8


COPY . /src/

RUN python -m pip install --upgrade setuptools
RUN pip install --no-cache -r ./server/requirements.txt
# Create a new user and switch to that user
RUN addgroup --system banking  && \
    adduser --system banking --gid 101  && \
    chown -R banking:banking /src 

USER banking
# Expose the Flask app port

EXPOSE 8000

CMD python manage.py runserver