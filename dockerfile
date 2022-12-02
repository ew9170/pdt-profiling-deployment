# syntax=docker/dockerfile:1

FROM python:3.8.15-alpine
COPY requirements.txt requirements.txt
RUN \
 apk add --no-cache librdkafka-dev && \
 apk add --no-cache python3 postgresql-libs && \
 apk add --no-cache --virtual .build-deps gcc python3-dev musl-dev postgresql-dev && \
 apk add --no-cache vim && \
 apk add --no-cache bash && \
 python3 -m pip install -r requirements.txt --no-cache-dir && \
 apk --purge del .build-deps
WORKDIR /app
COPY . .
CMD ["python", "pdt-profiling-deployment.py", "-v", "INFO"]