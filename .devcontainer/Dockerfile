ARG AA_DOCKER_TAG
FROM $AA_DOCKER_TAG

USER root
RUN apt-get update && apt-get install make gnupg2 -y
USER ${AUTH_USER}

RUN cd /home/allianceauth
COPY .devcontainer/requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . /workspace
RUN pip install -e /workspace

RUN allianceauth update myauth