# stock-app
C++ python stock-app

# podman commands
podman run -dit -v /home/palash/stock-app/configuration:/home/palash/app/configuration --network=host --name stock-app-pyserver stock-app-pyserver:latest