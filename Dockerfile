FROM python:3.10-slim-bullseye
WORKDIR /laboratory
COPY . .
RUN pip install --upgrade pip setuptools
RUN pip install -e .
CMD ["pserve", "production.ini", "--reload"]
