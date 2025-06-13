import grpc
import rfcontrol_pb2_grpc
import rfcontrol_pb2
from datetime import datetime
import sys
import argparse

try:
    from tkinter import *
    from tkinter import ttk
    gui = True
except ImportError:
    gui = False
    print("Tkinter is not available. Running in CLI mode.\nTo enable GUI, please install Tkinter.\n python -m pip install tk\n\n")

method_options = ["setRFSettings", "getDeviceStatus", "getDevicePPString", "getGainRange", "getFrequencyRange"]
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

        return response

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
    main()
