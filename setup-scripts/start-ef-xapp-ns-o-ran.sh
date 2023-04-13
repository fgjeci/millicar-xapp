#!/bin/bash
docker kill ef-xapp-24
docker rm ef-xapp-24
docker rmi ef-xapp:latest
./setup-ef-xapp.sh ns-o-ran

docker exec -it ef-xapp-24 bash

# docker kill ef-xapp
# docker rm ef-xapp
# docker rmi ef-xapp:latest
# ./setup-ef-xapp.sh ns-o-ran

# docker exec -it ef-xapp bash
