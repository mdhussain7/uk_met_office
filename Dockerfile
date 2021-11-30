FROM ubuntu:latest

# Creation of the workdir
RUN mkdir /uk_met_office
WORKDIR /uk_met_office
FROM python:3.9
ENV PYTHONUNBUFFERED 1
COPY . /copy/
# Add requirements.txt file to container
ADD requirements.txt /uk_met_office/

# Install requirements
RUN pip install --upgrade pip
RUN pip install -r /uk_met_office/requirements.txt
ADD . /uk_met_office/