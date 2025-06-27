import grpc
import rfcontrol_pb2_grpc
import rfcontrol_pb2
from datetime import datetime
import sys
import argparse
import numpy as np
from fft_calculator import calculate_fft, chunk_fft_data
import logging
import time


try:
    from tkinter import *
    from tkinter import ttk
    gui = True
except ImportError:
    gui = False
    print("Tkinter is not available. Running in CLI mode.\nTo enable GUI, please install Tkinter.\n python -m pip install tk\n\n")

method_options = ["setRFSettings", "getDeviceStatus", "getDevicePPString", "getGainRange", 
                  "getFrequencyRange", "Chat", "FFTCoefficients", "StreamFFTCoefficients",
                  "TransferData"
                 ]

class Client:
    def __init__(self, root, host='localhost', port=5555):
        self.root = root
        self.root.title("RF Controller")

        self.channel = grpc.insecure_channel(f'{host}:{port}')
        self.stub = rfcontrol_pb2_grpc.RFControllerStub(self.channel)

        self.method = StringVar()
        self.method.set("setRFSettings")


        Label(root, text="Select Method:").pack()
        self.method_menu = ttk.Combobox(root, textvariable=self.method, values=method_options, state="readonly")
        self.method_menu.current(0)
        self.method_menu.bind("<<ComboboxSelected>>", lambda e: self.update_form(self.method.get()))
        self.method_menu.pack()

        self.device_id = StringVar()
        self.frequency = StringVar()
        self.gain = StringVar()

        self.form_frame = Frame(root)
        self.form_frame.pack()

        Button(root, text="Send", command=self.send_request).pack()

        self.result = Text(root, height=15, width=60, padx=10, pady=10)
        self.result.pack(pady=10, padx=10)

        self.update_form("setRFSettings")

    ## Generate Sample Sine Wave Signal
    def generate_sample_signal(n_samples=2048, freq=20.0, sampling_rate=1500.0):
        """Generate a sample signal (e.g., sine wave)."""
        t = np.linspace(0, n_samples/sampling_rate, n_samples, endpoint=False)
        return np.sin(2 * np.pi * freq * t)
    
    def send_fft_coefficients(stub):
        # Generate sample signal
        signal = Client.generate_sample_signal()
    
        # Calculate FFT
        frequencies, real_coeffs, imag_coeffs = calculate_fft(signal)
    
        # Create request
        request = rfcontrol_pb2.FFTCoefficientsRequest(
            real=real_coeffs.tolist(),
            imag=imag_coeffs.tolist()
        )
        
        # Send request
        try:
            response = stub.SendFFTCoefficients(request)
            print(f"Server response: {response.status}")
            return response
        except grpc.RpcError as e:
            print(f"Error sending FFT coefficients: {e}")

    ## Generate Large Signal - Sine Waves
    def generate_large_signal(n_samples=100000, freq=10.0, sampling_rate=1000.0):
        """Generate a large sample signal (e.g., sine wave)."""
        t = np.linspace(0, n_samples/sampling_rate, n_samples, endpoint=False)
        return np.sin(2 * np.pi * freq * t)

    def stream_fft_coefficients(stub):
        # Generate large signal
        signal = Client.generate_large_signal()
    
        # Calculate FFT
        frequencies, real_coeffs, imag_coeffs = calculate_fft(signal)
        print(f"Generated FFT with {len(real_coeffs)} coefficients")
    
        # Connect to gRPC server
        ##with grpc.insecure_channel('localhost:50051') as channel:
            ##stub = fft_stream_service_pb2_grpc.FFTStreamServiceStub(channel)
        
        def make_requests():
            # Stream chunks of FFT coefficients
            for chunk_id, real_chunk, imag_chunk, is_last_chunk in chunk_fft_data(real_coeffs, imag_coeffs):
                yield rfcontrol_pb2.FFTCoefficientsStreamRequest(
                    real=real_chunk.tolist(),
                    imag=imag_chunk.tolist(),
                    chunk_id=chunk_id,
                    is_last_chunk=is_last_chunk
                )
        
        # Send and receive streams
        try:
            responses = stub.StreamFFTCoefficients(make_requests())
            ##print( responses )
            for response in responses:
                print(f"Server response for chunk {response.chunk_id}: {response.status}")
            #return responses
        except grpc.RpcError as e:
            print(f"Error streaming FFT coefficients: {e}")

    
    def generate_chunks(file_data, chunk_size=1024*1024):  # 1MB chunks
        chunk_id = 0
        for i in range(0, len(file_data), chunk_size):
            chunk_id += 1
            is_last = i + chunk_size >= len(file_data)
            yield rfcontrol_pb2.DataChunk(
                data=file_data[i:i + chunk_size],
                chunk_id=chunk_id,
                is_last=is_last
            )

    def transfer_data(stub, data):
        # Send data chunks and receive processed chunks
        logging.info("Starting data transfer...")
        start_time = time.time()
        logging.info(f"Start Time: {start_time} ")
        # Send chunks to server and receive responses
        responses = stub.TransferData(Client.generate_chunks(data))
    
        received_data = b""
        for response in responses:
            logging.info(f"Received chunk {response.chunk_id}")
            received_data += response.data
            if response.is_last:
                break
    
        end_time = time.time()
        logging.info(f"Transfer completed in {end_time - start_time:.2f} seconds")
        return received_data

    def update_form(self, method):
        for widget in self.form_frame.winfo_children():
            widget.destroy()

        self.result.tag_configure("grayed", foreground="gray")
        self.result.tag_add("grayed", "1.0", END)

        Label(self.form_frame, text="Device ID:").grid(row=0, column=0)
        Entry(self.form_frame, textvariable=self.device_id).grid(row=0, column=1)

        if method == "setRFSettings":
            Label(self.form_frame, text="Frequency (Hz):").grid(row=1, column=0)
            Entry(self.form_frame, textvariable=self.frequency).grid(row=1, column=1)
            Label(self.form_frame, text="Gain (dB):").grid(row=2, column=0)
            Entry(self.form_frame, textvariable=self.gain).grid(row=2, column=1)

    def send_request(self):
        method = self.method.get()
        device_id = self.device_id.get()

        try:
            response = send_grpc(self.stub, method, device_id, self.frequency.get(), self.gain.get())
            self.result.delete(1.0, END)
            self.result.insert(END, parse_response(response))
        except grpc.RpcError as e:
            self.result.delete(1.0, END)
            self.result.insert(END, f"RPC Error: {e.code()} - {e.details()}")

def parse_response(response):
    result_txt = ""
    if isinstance(response, rfcontrol_pb2.RFResponse):
        if response.success:
            result_txt = f"{response.message}"
        else:
            result_txt = f"Error:\n{response.message}"
    elif isinstance(response, rfcontrol_pb2.PPStringResponse):
        result_txt = f"{response.pp_string}"
    else:
        result_txt = str(response)
        print(response)

    result_txt = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n{result_txt}\n"
    return result_txt

def send_grpc(stub, method, device_id, frequency_in, gain_in):
        if method == "setRFSettings":
            frequency = float(frequency_in) if frequency_in else -9999
            gain = float(gain_in) if gain_in else -9999
            config = rfcontrol_pb2.RFRequest(device_id=device_id, frequency=frequency, gain=gain)
            response = stub.setRFSettings(config)
        elif method == "getDeviceStatus":
            request = rfcontrol_pb2.DeviceRequest(device_id=device_id)
            response = stub.getDeviceStatus(request)
        elif method == "getDevicePPString":
            request = rfcontrol_pb2.DeviceRequest(device_id=device_id)
            response = stub.getPPString(request)
        elif method == "getGainRange":
            request = rfcontrol_pb2.DeviceRequest(device_id=device_id)
            response = stub.getGainRange(request)
        elif method == "getFrequencyRange":
            request = rfcontrol_pb2.DeviceRequest(device_id=device_id)
            response = stub.getFrequencyRange(request)
        elif method == "chat":
            request = rfcontrol_pb2.GreetingRequest(name="Murshed")
            response = stub.Chat(request)
        elif method == "FFTCoefficients":
            ##request = rfcontrol_pb2.FFTCoefficients(self, stub)
            response = Client.send_fft_coefficients(stub)
            ##response = stub.Chat(request)
        elif method == "StreamFFTCoefficients":
            response = Client.stream_fft_coefficients(stub)
        elif method == "TransferData":
            # Simulate large data (10MB)
            large_data = b"ABC XYZ " * (10 * 1024 * 1024)
            # Transfer data and get response
            response = Client.transfer_data(stub, large_data)
            logging.info(f"Received data size: {len(response)} bytes")
            ##print(response)

        return response

        ##greeter_stub = GreeterStub(intercept_channel)
        ##request_data = GreetingRequest(name=name)
        ##response = greeter_stub.Greet(request_data)
        ##print(response.greeting)

def Chat():
    ##with grpc.insecure_channel('localhost:50051') as channel:
        greeter_stub = rfcontrol_pb2.GreeterStub()

        request_iterator = iter(
            [
                rfcontrol_pb2.GreetingRequest(name="Alice"), 
                rfcontrol_pb2.GreetingRequest(name="Bob")
            ]
        )
        response_iterator = greeter_stub.Chat(request_iterator)
        for response in response_iterator:
            print(response.greeting)

def run_cli(host='localhost', port=5555):
    channel = grpc.insecure_channel(f'{host}:{port}')
    stub = rfcontrol_pb2_grpc.RFControllerStub(channel)

    print("Client Started ...")
    print(f"Connected to server at {host}:{port}")
    print("Available methods:")
    for idx, m in enumerate(method_options, 1):
        print(f"{idx}. {m}")

    while True:
        try:
            choice = input("\nEnter method number (or 'q' to quit, 'h' to see the methods again): ").strip()
            if choice.lower() == 'q':
                print("Exiting...")
                break
            if choice.lower() == 'h':
                print("Available methods:")
                for idx, m in enumerate(method_options, 1):
                    print(f"{idx}. {m}")
                continue
            if( int(choice) < 1 or int(choice) > len(method_options)):
                print("Invalid choice. Please try again.")
                continue
            method = method_options[int(choice) - 1]
            device_id = input("Enter device_id (default: mock): ") or "mock"
            frequency = None
            gain = None
            if method == "setRFSettings":
                frequency = input("Enter frequency (Hz, default: None): ") or "-9999"
                gain = input("Enter gain (dB, default: None): ") or "-9999"

            response = send_grpc(stub, method, device_id, frequency, gain)
            print(parse_response(response))
        except Exception as e:
            print(f"Error: {e}")
        except KeyboardInterrupt:
            print("\nInterrupted by user. Exiting...")
            break

def main():
    parser = argparse.ArgumentParser(description='RF Control Client')
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode")
    parser.add_argument("--host", default="localhost", help="Host to connect to (default: localhost)")
    parser.add_argument("-p", "--port", default="5555", help="Port to connect to (default: 5555)")
    args = parser.parse_args()
    use_cli = args.cli or not gui
    host = args.host
    port = args.port

    if use_cli:
        run_cli(host=host, port=port)
    else:
        root = Tk()
        app = Client(root, host=host, port=port)
        app.root.mainloop()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
