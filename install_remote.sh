#!/bin/bash

docker build -t lachatak/kafka-acl-graph:latest .
docker push lachatak/kafka-acl-graph:latest

cd .helm
helm delete kafka-acl-graph --purge
./helm_upgrade.sh

cd ..