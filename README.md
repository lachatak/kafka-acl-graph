# Build
```bash
docker login 
docker build -t lachatak/kafka-acl-graph:latest . 
docker push lachatak/kafka-acl-graph:latest
```

# Install
```bash
cd .helm
./helm_upgrade.sh
```

# Remove
```bash
helm delete kafka-acl-graph --purge
```


