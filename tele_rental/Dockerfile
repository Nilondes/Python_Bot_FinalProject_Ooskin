FROM python:3.12-slim

WORKDIR tele_rental/

RUN pip install Django
RUN pip install psycopg2-binary
RUN pip install python-dotenv

COPY . .

RUN ["chmod", "+x", "./docker-entrypoint.sh"]
ENTRYPOINT ["bash", "-c"]
CMD ["./docker-entrypoint.sh"]