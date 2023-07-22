FROM python:3.10.12-alpine3.18

WORKDIR /laboratory

COPY . .
RUN pip install -e .

CMD ["pserve", "production.ini", "--reload"]
