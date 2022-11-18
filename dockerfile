# syntax=docker/dockerfile:1

FROM python:3.8.15-slim-buster
RUN pip install -r requirements.txt
WORKDIR /app
COPY . .
CMD ['python', "pdt-profiling-deployment.py"]