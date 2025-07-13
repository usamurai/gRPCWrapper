from concurrent import futures
import grpc
import time
import rfcontrol_pb2_grpc
import rfcontrol_pb2
import argparse
import sys
import logging

## Enable grpc_invoke
from grpc_invoke.grpc_client import GrpcClient
from grpc_reflection.v1alpha import reflection
from grpc_invoke import GrpcInvoker

from mock_device import MockDevice
from visa_wrapper import VisaWrapper
try:
    import uhd
    uhd_driver = True
except ImportError:
    uhd_driver = False

class RFControllerServicer(rfcontrol_pb2_grpc.RFControllerServicer):
    def __init__(self):
        self.devices = {}
        try:
            _devices = uhd.find_devices()
            for device in _devices:
                usrp = uhd.usrp.MultiUSRP(device)
                device_id = usrp.get_mboard_name()
                self.devices[device_id] = usrp
                print(f"Found USRP device: {device_id}")
        except Exception as e:
            print("No hardware is connected or driver not installed, use 'mock' as device_id")

        self.devices["mock"] = MockDevice()

    def _get_device(self, device_id, context):
        if device_id not in self.devices:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("No hardware connected, please use 'mock' as device_id")
            return None
        return self.devices[device_id]

    def setRFSettings(self, request, context):
        print(f"Config: device_id={request.device_id}, frequency={request.frequency}, gain={request.gain}")

        device = self._get_device(request.device_id, context)
        if device is None:
            return rfcontrol_pb2.RFResponse(success=False, message=context.details())

        freq_s, freq_m = True, "Unchanged"
        gain_s, gain_m = True, "Unchanged"

        if request.frequency != -9999:
            freq_s, freq_m = device.set_center_frequency(request.frequency)
        if request.gain != -9999:
            gain_s, gain_m = device.set_gain(request.gain)

        if not (freq_s and gain_s):
            return rfcontrol_pb2.RFResponse(success=False, message=f"Frequency: {freq_m}\nGain: {gain_m}")

        return rfcontrol_pb2.RFResponse(success=True, message=f"Configs updated successfully\nFrequency: {freq_m}\nGain: {gain_m}")

    ### VISA Commands Starts ###
    def GetDeviceInformation(self, request, context):
        visaWrp = VisaWrapper()
        error_queue_populate = request.error_queue_populate
        response = visaWrp.GetDeviceInformation()
        commandName = request.device_id
        #result = self.invoke_server_b(commandName,context)
        result = self.callFlexSDR(commandName,context)
        return rfcontrol_pb2.DeviceInformationResponse(
                reply_information=response["reply_information"],
                manufacturer=response["manufacturer"],
                model=result, #response["model"],
                serial_number=response["serial_number"],
                firmware_revision=response["firmware_revision"]
        )
    
    ### VISA Commands Ends ###

    def getDeviceStatus(self, request, context):
        print(f"getDeviceStatus: device_id={request.device_id}")

        device = self._get_device(request.device_id, context)
        if device is None:
            return rfcontrol_pb2.DeviceStatusResponse()

        status = device.get_status()
        return rfcontrol_pb2.DeviceStatusResponse(
                device_id=status["device_id"],
                frequency=status["frequency"],
                gain=status["gain"],
                ref_locked=status["ref_locked"],
                lo_locked=status["lo_locked"],
        )

    def getPPString(self, request, context):
        print(f"getPPString: device_id={request.device_id}")

        device = self._get_device(request.device_id, context)
        if device is None:
            return rfcontrol_pb2.PPStringResponse(pp_string="")

        pp_string = device.get_pp_string()
        return rfcontrol_pb2.PPStringResponse(pp_string=pp_string)

    def getGainRange(self, request, context):
        print(f"getGainRange: device_id={request.device_id}")

        device = self._get_device(request.device_id, context)
        if device is None:
            return rfcontrol_pb2.RangeResponse()

        min_gain, max_gain = device.get_rx_gain_range()
        return rfcontrol_pb2.RangeResponse(
            min_value=min_gain,
            max_value=max_gain,
        )
    
    def Greet(self, request, context):
        greeting='Hello %s!' % request.name
        return rfcontrol_pb2.GreetingResponse(
            geeting=greeting
        )

    def Chat(self, request_iterator , context):
        for request in request_iterator:
            yield rfcontrol_pb2.GreetingResponse(greeting=f"Welcome, {request.name}!")
    
    def getFrequencyRange(self, request, context):
        print(f"getFrequencyRange: device_id={request.device_id}")

        device = self._get_device(request.device_id, context)
        if device is None:
            return rfcontrol_pb2.RangeResponse()

        min_freq, max_freq = device.get_rx_freq_range()
        return rfcontrol_pb2.RangeResponse(
            min_value=min_freq,
            max_value=max_freq,
        )
    
    def SendFFTCoefficients(self, request, context):
        # Extract real and imaginary coefficients
        real_coeffs = request.real
        imag_coeffs = request.imag
        
        # Example: Print received coefficients
        print(f"Received FFT coefficients: {len(real_coeffs)} real, {len(imag_coeffs)} imaginary")
        
        # Process coefficients as needed (e.g., store, analyze)
        # For demo, just return a success status
        return rfcontrol_pb2.FFTCoefficientsResponse(status="Success")
    

    def StreamFFTCoefficients(self, request_iterator, context):
        """
        Handle bidirectional streaming of FFT coefficients.
        Receive chunks and send back status for each chunk.
        """
        for request in request_iterator:
            chunk_id = request.chunk_id
            real_coeffs = request.real
            imag_coeffs = request.imag
            is_last_chunk = request.is_last_chunk
            
            # Process chunk (e.g., store, analyze)
            print(f"Received chunk {chunk_id}: {len(real_coeffs)} real, {len(imag_coeffs)} imag coefficients")
            
            # Send response for this chunk
            status = f"Processed chunk {chunk_id}" + (" (last)" if is_last_chunk else "")
            yield rfcontrol_pb2.FFTCoefficientsStreamResponse(
                status=status,
                chunk_id=chunk_id
            )
    
    def TransferData(self, request_iterator, context):
        # Process incoming data chunks and send back processed chunks
        chunk_count = 0
        for chunk in request_iterator:
            chunk_count += 1
            # Simulate processing: just echo back with modified data
            processed_data = chunk.data + b"_processed"
            logging.info(f"{chunk.data} ==Chunk: {chunk_count}==  \n\n\n\n")
            yield rfcontrol_pb2.DataChunk(
                data=processed_data,
                chunk_id=chunk.chunk_id,
                is_last=chunk.is_last
            )
            if chunk.is_last:
                logging.info(f"Processed {chunk_count} chunks")
                break
    
    # Function to invoke Server B's SayHello method
    def invoke_server_b(self, name, context):
        ##flexSDRGRPCServer = "192.168.137.232:5555"
        flexSDRGRPCServer = "localhost:2222"
        
        with GrpcClient(flexSDRGRPCServer, "RFController", "rfcontrol.RFController.runCustomCmd") as client:
            resp = client.invoke(data={"CustomRequest": "pwd"}, header={"auth": "testcall"})
            print(resp)
            exit()

        ##with grpc.insecure_channel(flexSDRGRPCServer) as channel:
        ##    stub = rfcontrol_pb2_grpc.RFControllerStub(channel)
        ##    response = stub.runCustomCmd(rfcontrol_pb2.CustomRequest(name))
        ##    print(f"RT Server requested to flex DR: {name}")
        ##    print(f"RT Server received from Flex SDR: {response.message}")
        ##    ##return response.message

    # Function to invoke Server B's method
    def callFlexSDR(self, name, context):
        
        ## Server's FQDN Need to take later from the Config file 
        flexSDRGRPCServer = "192.168.137.232:5555"

        # Initialize GrpcInvoker
        invoker = GrpcInvoker(flexSDRGRPCServer)
    
        # Invoke runCustomCmd method
        #request = rfcontrol_pb2.CustomRequest(customCmdName=device_id)
        flexsdr_response = invoker.invoke(
            service='rfcontrol.RFController',
            method='runCustomCmd',
            request={'customCmdName': 'pwd'}
        )
        print(f"Greet response: {flexsdr_response['message']}")

    
def serve(port=5555):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    rfcontrol_pb2_grpc.add_RFControllerServicer_to_server(RFControllerServicer(), server)
 
    ## gRPC Server Reflection Start ##
    ## Replace with your actual service name
    SERVICE_NAMES = (
        reflection.SERVICE_NAME,
        rfcontrol_pb2.DESCRIPTOR.services_by_name['RFController'].full_name
    )

    reflection.enable_server_reflection(SERVICE_NAMES, server)
    ## Refelction Done ##

    server.add_insecure_port(f'[::]:{port}')
    server.start()
    print(f"Server started on port {port}")
    logging.basicConfig(level=logging.INFO)
    logging.info(f"Server starting on port: {port}")

    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='RF Control gRPC Server')
    parser.add_argument('-p', '--port', type=int, default=5555, help='Port to run the gRPC server on')
    args = parser.parse_args()
    serve(port=args.port)
