FROM python:3.12-rc-slim-bookworm
RUN apt-get update && apt-get upgrade -y
RUN apt-get install cron postgresql-client -y

WORKDIR /app

# dependecies first
COPY requirements.txt ./
RUN pip install -r requirements.txt

# rest of the source code
COPY . .
RUN mkdir dump archive

# create log file to be able to run tail
RUN touch /app/cron.log

# install crontab
ENV TZ="Europe/Prague"
ENV CRON_TZ="Europe/Prague"
RUN crontab crontab.txt

# copy env variables somewhere, where cron can access them
# https://stackoverflow.com/questions/65884276
CMD printenv > /etc/environment && cron && tail -f /app/cron.log
