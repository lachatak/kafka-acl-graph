# Build
```bash
docker login 
docker build -t lachatak/kafka-acl-graph:latest . 
docker push lachatak/kafka-acl-graph:latest
```

# Run 

## Locally
- make local copy from `run-web-template.sh` to `run-web.sh`
- fill variables in the new file
- run
```bash 
run-web.sh
```

## Remote GCP cluster

### Provide secrets
- create `app_secrets.yaml` into `./helm` with the following values:
```
aiven:
  project: ??
  service: ??
  api_token: ??
hostName: ??
```

### Install
```bash
cd .helm
./helm_upgrade.sh
```

### Remove
```bash
cd .helm
helm delete kafka-acl-graph --purge
```




