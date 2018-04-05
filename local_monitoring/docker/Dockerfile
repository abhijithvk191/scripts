FROM ubuntu:16.04

MAINTAINER ABHIJITH VIJAYAN <abhijith@hifx.co.in>

RUN apt-get -y update && apt-get install -y python python-pip



# Update the Dotdeb package repository and install applications
RUN apt-get -y update && apt-get install -y net-tools build-essential unzip wget software-properties-common supervisor pkg-config
RUN pip install  Flask

# Supervisord Config
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

ADD start.sh /opt/start.sh
RUN chmod 755 /opt/start.sh

# private expose
EXPOSE 80
ENTRYPOINT ["/opt/start.sh"]
