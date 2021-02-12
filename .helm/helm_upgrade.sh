#!/bin/sh
helm upgrade kafka-acl-graph ./kafka-acl-graph -f ./app_secrets.yaml --install --wait --namespace kafka-acl-graph
