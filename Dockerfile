FROM ubuntu:20.04

MAINTAINER Krisztian Lachata "krisztian.lachata@gmail.com"

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update -y && \
    apt-get install -y python3-pip python3-dev graphviz

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip3 install -r requirements.txt

COPY *.py /app/
COPY static/ /app/static/

ENTRYPOINT [ "python3" ]

CMD [ "kafka-acl-graph-web.py" ]