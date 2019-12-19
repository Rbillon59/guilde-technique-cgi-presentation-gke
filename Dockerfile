FROM python:3.8.0-alpine

WORKDIR /opt/myApp
ENTRYPOINT ["python"]
CMD ["main.py"]

RUN apk add curl
RUN pip install  --no-cache-dir flask
ENV myEnvironmentVariable="Hello world"

COPY ./main.py /opt/myApp/main.py