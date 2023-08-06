FROM python:3.12-rc-slim-bookworm
RUN apt-get update -y && apt-get upgrade -y

RUN apt-get install curl -y
RUN curl -L https://fly.io/install.sh | FLYCTL_INSTALL=/usr/local sh

RUN apt-get install postgresql-client -y

RUN mkdir /app
WORKDIR /app

# dependecies first
COPY requirements.txt ./
RUN pip install -r requirements.txt

# rest of the source code
COPY . .
RUN mkdir dump archive

CMD ["python3", "-u", "automate_backup.py"]
