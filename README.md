# Marcel Davis - Mensa Bot

Marcel Davis ist der inoffizielle Mensabot der Hochschule Mannheim

## Setup

Before running the application, the api token needs to be added to the environment. For this an environtment file can to be created.

```.env
API_KEY="api-key"
```

The application can be run either using a virtual environment or deploying as a docker container. 

### Virtual environment

To use the bot without docker, the requirements.txt needs to be installed first. ```pip install -r requirements.txt```. After this the marcel_davis.py can be executed ```python3 marcel_davis.py```

### Docker

To run the bot as a docker container you need to first build the Image. For this an additional env file need to be created first.

- ```docker build -t marcel_davis:<tag> .```

After this, with ```docker compose up -d``` the application can be started.

## Open Tasks

- fix abo method
- add option for menue of next week
- when current (not older than X mins) cache exists at startup do not cache
