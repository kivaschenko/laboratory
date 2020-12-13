FROM python:3.7
RUN mkdir -p /usr/src/laboratory
WORKDIR /usr/src/laboratory
COPY . /usr/src/laboratory
CMD ["env/bin/pserve", "development.ini"]
