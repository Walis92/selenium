FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    chromium-driver chromium wget unzip curl gnupg \
    && pip install flask selenium \
    && apt-get clean

ENV PATH="/usr/lib/chromium/:$PATH"
ENV CHROME_BIN="/usr/bin/chromium"

COPY . /app
WORKDIR /app

CMD ["python", "app.py"]
