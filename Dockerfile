FROM python:3.12-slim

WORKDIR .

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN ["chmod", "+x", "./docker-entrypoint.sh"]
ENTRYPOINT ["bash", "-c"]
CMD ["./docker-entrypoint.sh"]