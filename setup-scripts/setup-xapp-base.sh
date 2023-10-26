SETUP_DIR=../setup
MODEL_DIR=millicar-xapp
MODEL_DIR_EF=ef-xapp
CONNECTOR_DIR=xapp-sm-connector
IMAGE_NAME=xapp-base
DOCKER_FILE=Dockerfile_build_xapp_base

# Build docker image
$SUDO docker image inspect ${IMAGE_NAME}:latest >/dev/null 2>&1
if [ ! $? -eq 0 ]; then
    cd ${SETUP_DIR}
    cp ${MODEL_DIR}/${DOCKER_FILE} ./${DOCKER_FILE}_${IMAGE_NAME}
    $SUDO docker build  \
            -f ${DOCKER_FILE}_${IMAGE_NAME} -t ${IMAGE_NAME}:latest .

fi