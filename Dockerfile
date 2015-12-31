FROM centos:centos7

RUN yum -y update \
    && yum install -y \
        python-devel \
        epel-release \
    && yum clean all

RUN yum -y install python-pip && yum clean all

COPY src/requirements.txt /pip/
RUN pip install --upgrade pip
RUN cd /pip && pip install -r requirements.txt
