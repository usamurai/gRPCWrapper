# gRPC RF Control Server & Client

Implements a gRPC-vased client - server system for RF devices. Provides interface to manage RF devices via UHD API or mock devices via standard RPC calls

## Features
* gRPC Server
* Supports multiple read USRP devices
* Supports mock USRP device
* RPCs to set and query:
  * frequency
  * gain
  * status
  * frequency range
  * gain range
* Client GUI using tkinter
* Dockerfile for Dockerized server

## Project Structure
```
.
├── client.py
├── server.py
├── rfcontrol.proto
├── requirements.txt
├── Dockerfile
└── README.md

```

## Requirements
* Python 3.8 or higher
* grpcio and grpcio-tools python packages (listed in `requirements.txt`)
* Optional: UHD drivers for real hardware control
* Optional: Docker for dockerizing the server
* Optional: tkinter python package for GUI client

## Installation
1. Clone the repository
```
git clone https://github.com/SymonSaroar/gRPC.git
cd gRPC
```
2. Install python dependencies
   ```
   python -m pip install -r requirements.txt
   ```
3. Compile the protobuf definitions
   ```
   python -m grpc_tools.protoc -I . --python_out=. --grpc_python_out=. rfcontrol.proto
   ```
## Running the Server
To run the server locally:
```
python server.py
```
By default the server listens on port 5555
to run on different port
```
python server.py -p 12345
```

## Running the Client

To run the client example
```
python client.py
```
The client will use GUI if tkinter module is available, else it will present an CLI. to force the CLI use:
```
python client.py --cli
```
Default server and port for the Client is localhost:5555
To specify server and port use the following format
```
python client.py --host 192.168.0.101 -p 12345
```

## Docker Deployment
Build the Docker image:
```
docker build -t rfcontrol-server
```
Run the container:
```
docker run -p 5555:5555 rfcontrol-server
```
This exposes port 5555 on the host machine

## RPC Overview
the gRPC service exposes the following RPC methods (defined in rfcontrol.proto):
* setRFSettings - Conigure parameters like frequency and gain
* getDeviceStatus - Fetch current device status
* getPPString - Get a printable string of device info
* getGainRange - Get gain range
* getFrequencyRange - Get Frequency range
