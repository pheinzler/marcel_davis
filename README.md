# Marcel Davis - Mensa Bot

Marcel Davis ist der inoffizielle Mensabot der Hochschule Mannheim

## Setup

Before running the application, a few secrets need to be added in the form of an environment varible. For this an environment file (./src/.env) can be used.

```.env
API_KEY="api-key"
INFLUX_TOKEN="INFLUX DB TOKEN - if statistics shall be persitet"
INFLUX_URL="<IP>:<Port>"
```

### Statistics

It is possible to persist statistics like menue prices or how often a handler is called inside an influxdb. To persist data the following config keys need to be specified inside the ```config.yaml```:

```.yaml
statistics: true
influx:
  org: "influx-org"
  bucket: "influx-bucket"
```

## Startup

The application can be run either using a virtual environment or deploying as a docker container.

### Virtual environment

To use the bot without docker, the requirements.txt needs to be installed first. ```pip install -r requirements.txt```. After this the marcel_davis.py can be executed inside the src folder ```python3 marcel_davis.py```.

### Docker

To run the bot as a docker container you need to first build the Image. For this an additional src/.env file needs to be created first.

- ```docker build -t marcel_davis:<tag> .```

After this, with ```docker compose up -d``` the application can be started.
