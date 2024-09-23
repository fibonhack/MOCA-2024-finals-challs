# python:3.11.3-bullseye
FROM python@sha256:13927a8172d13b6cdc87f50bf0a38ff4eceef05262f83870c9f6474d16117687

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y cron

WORKDIR /app

COPY ./requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .
COPY ./flag.txt /flag.txt

EXPOSE 5000

ENTRYPOINT service cron start && uwsgi wsgi.ini