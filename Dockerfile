FROM rackspacedot/python37

RUN  pip install --upgrade pip setuptools

WORKDIR /laboratory

COPY . .
RUN pip install -e .

CMD ["pserve", "production.ini"]
