class VisaWrapper:
    def __init__(self, device_id="mock", frequency=1e6, gain=10):
        self.device_id = device_id
        self.frequency = frequency
        self.gain = gain
        self.ref_locked = True
        self.lo_locked = True

    
    ### VISA Commands Wrapper Starts ### 
    
    def GetDeviceInformation(error_queue_populate=True):
        ##error_queue_populate = request.error_queue_populate
        response = {
            "manufacturer"      : "XRComm",
            "model"             : "FlexSDR S8010-01",
            "serial_number"     : 123456,
            "firmware_revision" : "Alpha 1",
            "reply_information" : "Error Code"
            ##"reply_information" : {"status" : 101,
            ##                        "message": "Device could not be found"
            ##                      }
        }
        return response

    ### VISA Commands Wrapper Ends ###


    def set_center_frequency(self, frequency):
        if frequency <= 0:
            return False, "Frequency must be greater than zero"
        self.frequency = frequency
        return True, "Frequency set successfully"

    def get_center_frequency(self):
        return self.frequency

    def set_gain(self, gain):
        if gain <= 0:
            return False, "Gain must be greater than zero"
        self.gain = gain
        return True, "Gain set successfully"

    def get_usrp_rx_info(self):
        return {
            "product": "Mock UHD",
            "serial": "123456789",
            "firmware_version": "1.0.0",
            "hardware_version": "1.0",
            "device_id": self.device_id,
            "rx_id": "rx0",
            "manufacturer": "Mock Manufacturer",
        }

    def get_pp_string(self):
        return (
            f"Mock Device\n"
            f"Device ID: {self.device_id}\n"
            f"Frequency: {self.frequency} Hz\n"
            f"Gain: {self.gain} dB\n"
            f"Reference Locked: {self.ref_locked}\n"
            f"LO Locked: {self.lo_locked}"
        )

    def get_status(self):
        return {
            "device_id": self.device_id,
            "frequency": self.frequency,
            "gain": self.gain,
            "ref_locked": self.ref_locked,
            "lo_locked": self.lo_locked
        }
    def get_rx_gain_range(self):
        return (1, 30)
    def get_rx_freq_range(self):
        return (1e3, 2e9)
