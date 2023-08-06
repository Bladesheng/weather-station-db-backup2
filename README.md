# weather-station-db-backup2

## About this repository

Once a day, this repo runs Github action, which connects to my [weather station database](https://github.com/Bladesheng/weather-station-backend), creates dump of the db, zips it and uploads it to my google drive. Everything runs in docker and is completely automated.

## Running locally

- Clone the repo
- Create `docker-compose.yml` file with your own credentials and stuff - see `docker-compose.example.yml`.
- Run Docker:

```sh
docker compose up --build
```

## Running from your own Github repo

- Set all Github secrets, same as in `docker-compose.example.yml`
