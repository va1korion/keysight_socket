"""
This snippet implements simple requests to Keysight N9020a
It should use pyvisa to communicate with the device, but the task specifies not using any side libraries.
Alternatively, could use telnet which is mentioned in docs. Though it also requires side libraries since telnet is deprecated in 3.11. 
"""
import socket



class Device:
    """
    implemetns simple SCPI requests to Keysight N9020a
    for reference see: https://www.manualslib.com/manual/2957161/Keysight-X-Series.html 
    it doesn't cover N9020a, but the syntax is the same and commands should be common
    """
    # todo: add logging
    def __init__(self, ip, port=5025, timeout=10):
        """
        Initialize the device with the given IP address and port. Connects to the device socket.
        """
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.ip, self.port))
        self.socket.settimeout(timeout)
        self.available_modes: set[str] | None = None

    def _send(self, message):
        """
        Sends a message to the device. Adds a newline character to the end of the message.
        """
        self.socket.send(message.encode() + b"\n")

    def _receive(self) -> str | None:
        """
        Receives a message from the device.
        
        Returns:
            str | None: The decoded message received from the device, or None if timeout occurs
        """
        try:
            return self.socket.recv(1024).decode()
        except socket.timeout:
            return None

    def get_device_info(self) -> list[str]:
        """
        Gets device identification information.
        
        Returns:
            list[str]: Device info as [manufacturer, model, serial number, firmware version]
        """
        self._send("*IDN?")
        return self._receive().strip().split(",")

    def get_frequency(self) -> str | None:
        """
        Gets the current center frequency.
        
        Returns:
            str | None: The current center frequency value
        """
        self._send(":FREQ:RF:CENT?")
        return self._receive()
    
    def set_frequency(self, frequency: float) -> str | None:
        """
        Sets the center frequency.
        
        Args:
            frequency (float): The frequency value to set in Hz
            
        Returns:
            str | None: Response from the device
            
        Raises:
            ValueError: If frequency is outside valid range (-80 MHz to 5 GHz)
        """
        if frequency < -80_000_000 or frequency > 5:
            raise ValueError("Frequency must be between -80 MHz and 5 GHz")
        self._send(f":FREQ:RF:CENT {frequency}")
        return self._receive()

    def reset(self) -> str | None:
        """
        Resets the device to default settings.
        
        Returns:
            str | None: Response from the device
        """
        self._send("*RST")
        return self._receive()

    def continuous_measurement(self) -> str | None:
        """
        Sets the device to continuous measurement mode.
        
        Returns:
            str | None: Response from the device
        """
        self._send(":INIT:CONT 1")
        return self._receive()

    def single_measurement(self) -> str | None:
        """
        Sets the device to single measurement mode.
        
        Returns:
            str | None: Response from the device
        """
        self._send(":INIT:CONT 0")
        return self._receive()
    
    def set_marker(self, frequency: float, marker_number: int = 1) -> str | None:
        """
        Sets a marker at the specified frequency.
        
        Args:
            marker_number (int): The marker number to set (default: 1)
            frequency (float): The frequency to set the marker at
            
        Returns:
            str | None: Response from the device
        """
        self._send(f":CALC:MARK{marker_number}:X {frequency}")
        return self._receive()

    def set_marker_max(self, marker_number: int = 1) -> None:
        """
        Sets the specified marker to the peak.
        
        Args:
            marker_number (int): The marker number to set (default: 1)
            
        Raises:
            ValueError: If no peaks are found
        """
        self._send(f":CALC:MARK{marker_number}:MAX")
        self._send(f":SYST:ERR?")
        result = self._receive()
        if result == -200 or result == "Execution error; No peak found":
            raise ValueError("No peaks found")
    
    def get_marker_Xaxis(self, marker_number: int = 1) -> str | None:
        """
        Gets the X-axis (frequency) value of the specified marker.
        
        Args:
            marker_number (int): The marker number to query (default: 1)
            
        Returns:
            str | None: The X-axis value of the marker
        """
        self._send(f":CALC:MARK{marker_number}:X?")
        return self._receive()
    
    def get_marker_Yaxis(self, marker_number: int = 1) -> str | None:
        """
        Gets the Y-axis (amplitude) value of the specified marker.
        
        Args:
            marker_number (int): The marker number to query (default: 1)
            
        Returns:
            str | None: The Y-axis value of the marker
        """
        self._send(f":CALC:MARK{marker_number}:Y?")
        return self._receive()

    def get_available_modes(self) -> set[str]:
        """
        Gets the available measurement modes from the device.
        
        Returns:
            set[str]: Set of available mode names
        """
        self._send(":INST:CAT?")
        self.available_modes = set(self._receive().strip().split(","))
        return self.available_modes

    def set_mode(self, mode: str) -> None:
        """
        Sets the measurement mode of the device.
        
        Args:
            mode (str): The mode name to set
            
        Raises:
            ValueError: If the specified mode is not available
        """
        if self.available_modes is None:
            self.get_available_modes()
        if mode not in self.available_modes:
            raise ValueError(f"Mode {mode} is not available")
        self._send(f":INST:SEL {mode}")

    def close(self) -> None:
        """
        Closes the connection to the device.
        """
        self.socket.close()

