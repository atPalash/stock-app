FROM ubuntu:22.04

# Install package dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \ 
    python3.10 \
    pip

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir flask requests pyyaml

WORKDIR /src/stock-app
COPY . ./
CMD ["/bin/sh", "-c", "python3.10 main.py"]