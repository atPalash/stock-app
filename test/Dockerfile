# Use the official Python base image
FROM python:3.10
ARG NGROK_AUTH_TOKEN

RUN apt-get update && apt-get install --no-install-recommends -y \
	git \
	ssh \
	sudo
# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null && echo "deb https://ngrok-agent.s3.amazonaws.com buster main" |   sudo tee /etc/apt/sources.list.d/ngrok.list &&   sudo apt update && sudo apt install ngrok
RUN ngrok config add-authtoken ${NGROK_AUTH_TOKEN}
# Copy your Flask app code into the container
COPY . .
RUN chmod +x runner.sh
# Set the entry point
ENTRYPOINT ["./runner.sh"]
