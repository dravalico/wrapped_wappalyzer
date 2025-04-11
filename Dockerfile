FROM sitespeedio/browsertime:latest

RUN wget https://storage.googleapis.com/chrome-for-testing-public/133.0.6943.53/linux64/chromedriver-linux64.zip && \
    unzip chromedriver-linux64.zip && \
    mv chromedriver-linux64/chromedriver /usr/local/bin/ && \
    rm -rf chromedriver-linux64.zip

RUN chmod +x /usr/local/bin/chromedriver

RUN mkdir /app
WORKDIR /app

COPY . /app

RUN apt-get update && apt-get install -y python3-pip
RUN pip3 install --upgrade pip
RUN pip3 install selenium

ENTRYPOINT ["python3", "main.py"]
