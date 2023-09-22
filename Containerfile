FROM fedora:37

RUN dnf install python3 python3-devel easy-rsa -y && dnf clean all

WORKDIR /opt/
RUN python3 -m venv fastapi && ./fastapi/bin/pip install fastapi uvicorn

ADD app.py /opt/app.py

EXPOSE 8000
ENTRYPOINT ["/opt/fastapi/bin/uvicorn", "--host=0.0.0.0", "app:app"] 
