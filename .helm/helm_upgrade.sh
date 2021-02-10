#!/bin/sh
helm upgrade kafka-acl-graph ./kafka-acl-graph -f ./environments/nonprod.yaml -f ./environments/nonprod_app_secrets.yaml --install --wait --namespace kafka-acl-graph
