FROM ubuntu:22.04

# Install package dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libatlas-base-dev \
    python3-dev \ 
    libpq-dev \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    ca-certificates \ 
    python3.10 \
    pip \
    curl \ 
    net-tools \ 
    iputils-ping \ 
    iproute2 \ 
    wget \
    && apt-get clean 

RUN DEBIAN_FRONTEND=noninteractive TZ=Europe/Helsinki apt-get -y install tzdata

RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz \
    && tar -xzf ta-lib-0.4.0-src.tar.gz \
    && cd ta-lib \
    && ./configure --prefix=/usr \
    && make \
    && make install

ENV LD_LIBRARY_PATH /usr/lib

WORKDIR /src/stock-app
COPY ./mirror/StockAppApi ./StockAppApi

RUN pip install --no-cache-dir --upgrade pip && \
    pip install -r StockAppApi/requirements.txt
RUN mkdir -p /usr/share/fonts/truetype/dejavu && cp StockAppApi/processes/python/scheduler/DejaVuSansMono.ttf /usr/share/fonts/truetype/dejavu

CMD ["/bin/bash", "-c", "export PYTHONPATH=$PWD:$PYTHONPATH && python3 StockAppApi/processes/python/scheduler/main.py"]
