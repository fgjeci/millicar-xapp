#!/bin/bash
docker kill millicar-xapp-24
docker rm millicar-xapp-24
# docker rmi millicar-xapp:latest
./setup-millicar-xapp.sh ns-o-ran

# docker exec -it millicar-xapp-24 bash

# docker kill ef-xapp
# docker rm ef-xapp
# docker rmi ef-xapp:latest
# ./setup-ef-xapp.sh ns-o-ran

# docker exec -it ef-xapp bash
