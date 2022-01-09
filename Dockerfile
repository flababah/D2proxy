FROM python:3.10-alpine
COPY d2proxy.py /d2proxy.py
EXPOSE 6112
EXPOSE 6113
EXPOSE 4000
ENTRYPOINT ["python", "-u", "/d2proxy.py"]
