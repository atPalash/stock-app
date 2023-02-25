FROM ubuntu:22.04

# Install package dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    iputils-ping \ 
    iproute2 \ 
    curl

WORKDIR /src/stock-app
COPY dockerfiles ./
ENV LD_LIBRARY_PATH /src/stock-app/libs:$LD_LIBRARY_PATH
CMD ["/bin/sh", "-c", "cd exec && ./DiscordConnector"]

#ip route | awk 'NR==1 {print $3}'