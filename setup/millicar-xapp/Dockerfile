##-----------------------------------
# BS Connector
#------------------------------------
ARG SCHEMA_PATH=schemas
ARG XAPP_DIR=millicar-xapp
# ARG IPSO_DIR=ipso-xapp
ARG CONNECTOR_DIR=xapp-sm-connector
ARG STAGE_DIR=/home/${CONNECTOR_DIR}
ARG DBAAS_SERVICE_HOST=10.0.3.12
ARG DBAAS_SERVICE_PORT="6379"

#==================================================================================
FROM xapp-base:latest as ricbuild
# Need to download from rayproject to have ray installed
# FROM rayproject/ray:latest as ricbuild


# to override repo base, pass in repo argument when running docker build:
# docker build --build-arg REPOBASE=http://abc.def.org . ....
ARG REPOBASE=https://gerrit.oran-osc.org/r
ARG SCHEMA_FILE
ARG SCHEMA_PATH
ARG XAPP_DIR
# ARG IPSO_DIR
ARG CONNECTOR_DIR
ARG STAGE_DIR

ARG MDC_VER=0.0.4-1
ARG RMR_VER=4.0.5
ARG RNIB_VER=1.0.0

ENV RMR_RTG_SVC="9999" \
  RMR_SEED_RT="/home/${CONNECTOR_DIR}/init/routes.txt" \
  LD_LIBRARY_PATH="/usr/local/lib:/usr/local/libexec" \
  VERBOSE=0 \
  CONFIG_FILE=/opt/ric/config/config-file.json \
  DBAAS_SERVICE_HOST=${DBAAS_SERVICE_HOST} \
  DBAAS_SERVICE_PORT=${DBAAS_SERVICE_PORT} \
  # Added to avoid stopping at time zone
  TZ=Europe/Rome \
  DEBIAN_FRONTEND=noninteractive

COPY ${CONNECTOR_DIR} ${STAGE_DIR}
COPY ${XAPP_DIR} /home/${XAPP_DIR}
# COPY ${IPSO_DIR} /home/${IPSO_DIR}

WORKDIR ${STAGE_DIR}

##-----------------------------------
# Now install the program
#------------------------------------
# build connector
RUN export CPATH=$CPATH:/usr/local/include \
  && cd src \
  && make clean \
  && make -j ${nproc} \
  && make install \
  && ldconfig \
  && sysctl -w net.ipv6.conf.lo.disable_ipv6=1 \
###-----------------------------------
## DRL Agent
##------------------------------------
## install packages and pip requirements
#  && pip3 --no-cache-dir install -U pip \
#  && pip3 --no-cache-dir install -r /home/${XAPP_DIR}/requirements.txt \
  && apt-get autoremove -y \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

