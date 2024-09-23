FROM python:3.12-alpine


RUN apk update
RUN apk add socat

WORKDIR /app
COPY chall.py chall.py
COPY flag.txt flag.txt


ENTRYPOINT ["socat", "-t", "900", "-T", "120", "TCP4-LISTEN:5555,reuseaddr,fork", "EXEC:env PYTHONUNBUFFERED=1 python3 /app/chall.py"]
