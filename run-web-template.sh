#!/bin/bash
pip3 install -r requirements.txt

export FLASK_APP=kafka-acl-graph.py
export FLASK_DEBUG=1

export AIVEN_PROJECT=?
export AIVEN_SERVICE=?
export AIVEN_API_TOKEN=?
export SERVER_NAME=https://127.0.0.1:5000

flask run --cert=adhoc