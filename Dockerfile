FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python -m grpc_tools.protoc -I . --python_out=. --grpc_python_out=. rfcontrol.proto

EXPOSE 5555

CMD ["python", "server.py"]
