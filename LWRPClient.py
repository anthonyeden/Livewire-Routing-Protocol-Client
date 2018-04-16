"""LWRP Client. An Open-Source Python Client for the Axia Livewire Routing Protocol."""

import time

from LWRPClientComms import LWRPClientComms

__author__ = "Anthony Eden"
__copyright__ = "Copyright 2015-2018, Anthony Eden / Media Realm"
__credits__ = ["Anthony Eden"]
__license__ = "GPL"
__version__ = "0.4"


class LWRPClient():
    """Provides a friendly API for the Livewire Routing Protocol."""

    def __init__(self, host, port):
        """Init LWRP connection."""

        # This is our access to the LWRP
        self.LWRP = None

        # This variable gets given the callback data, ready to be processed by a waiting function
        self.waitingForCallback = False
        self.callbackData = None

        self.LWRP = LWRPClientComms(host, port)
        self.LWRP.start()

    def stop(self):
        """Close LWRP connection."""
        self.LWRP.stop()

    def waitForCallback(self, timeout=5):
        """Wait for data to be returned from the Comms class."""
        # The time we need to stop waiting for data and return it
        waitTimeout = time.time() + timeout

        while True:
            if self.waitingForCallback is False or waitTimeout <= time.time():
                returnData = self.callbackData
                self.callbackData = None
                return returnData

            else:
                time.sleep(0.1)

    def genericCallback(self, data):
        """Generic callback receiving function."""
        self.callbackData = data
        self.waitingForCallback = False

    def login(self, password=None):
        """Login to the device/server. Required for non-info commands."""
        if password is not None:
            self.LWRP.sendCommand("LOGIN " + password)
        else:
            self.LWRP.sendCommand("LOGIN")

    def errorSub(self, callback):
        """Subscribe to error messages."""
        self.LWRP.addSubscription("ERROR", callback, False)

    def deviceData(self):
        """Get core data about the device/server."""
        self.LWRP.addSubscription("DEVICE", self.genericCallback, 1)
        self.LWRP.sendCommand("VER")

        self.waitingForCallback = True
        return self.waitForCallback()

    def networkData(self):
        """Get networking data about the device/server."""
        self.LWRP.addSubscription("NETWORK", self.genericCallback, 1)
        self.LWRP.sendCommand("IP")

        self.waitingForCallback = True
        data1 = self.waitForCallback()

        # Some extra data is available via the 'SET' command. Find this and append it to the NETWORK data.
        self.LWRP.addSubscription("SET", self.genericCallback, 1)
        self.LWRP.sendCommand("SET")

        self.waitingForCallback = True
        data2 = self.waitForCallback()

        data1[0]['attributes'].update(data2[0]['attributes'])
        return data1


    def sourceData(self):
        """Get current audio source data."""
        self.LWRP.addSubscription("SOURCE", self.genericCallback, 1)
        self.LWRP.sendCommand("SRC")

        self.waitingForCallback = True
        return self.waitForCallback()

    def sourceDataSub(self, callback):
        """Subscribe to audio source data updates."""
        self.LWRP.addSubscription("SOURCE", callback, False)
        self.LWRP.sendCommand("SRC")

    def destinationData(self):
        """Get current audio destination data."""
        self.LWRP.addSubscription("DESTINATION", self.genericCallback, 1)
        self.LWRP.sendCommand("DST")

        self.waitingForCallback = True
        return self.waitForCallback()

    def destinationDataSub(self, callback):
        """Subscribe to audio destination data updates."""
        self.LWRP.addSubscription("DESTINATION", callback, False)
        self.LWRP.sendCommand("DST")

    def meterData(self):
        """Get the current audio level meter data."""
        self.LWRP.addSubscription("METER", self.genericCallback, 1)
        self.LWRP.sendCommand("MTR")

        self.waitingForCallback = True
        return self.waitForCallback()

    def setSource(self, chnum, multicast_addr): 
        """Set the source address for a specified channel"""
        self.LWRP.sendCommand("SRC " + str(chnum) + " RTPA:" + str(multicast_addr))
    
    def setDestination(self, chnum, multicast_addr): 
        """Set the output address for a specified channel"""
        self.LWRP.sendCommand("DST " + str(chnum) + " ADDR:" + str(multicast_addr))

    def setSilenceThreshold(self, io, chnum, threshold, timems):
        """Set a silence threshold and time for a specific I/O channel."""
        if io == "in":
            ioch = "ICH"
        elif io == "out":
            ioch = "OCH"
        else:
            raise ValueError("IO Direction set incorrectly. Use 'in' or 'out'.")

        chnum = str(int(chnum))
        threshold = str(int(threshold))
        timems = str(int(timems))

        self.LWRP.addSubscription("LEVEL_ALERT", self.genericCallback, 1)
        self.LWRP.sendCommand("LVL " + ioch + " " + chnum + " LOW.LEVEL:" + threshold + " LOW.TIME:" + timems)

        self.waitingForCallback = True
        return self.waitForCallback()

    def setClippingThreshold(self, io, chnum, threshold, timems):
        """Set a clipping threshold and time for a specific I/O channel."""
        if io == "in":
            ioch = "ICH"
        elif io == "out":
            ioch = "OCH"
        else:
            raise ValueError("IO Direction set incorrectly. Use 'in' or 'out'.")

        chnum = str(int(chnum))
        threshold = str(int(threshold))
        timems = str(int(timems))

        self.LWRP.addSubscription("LEVEL_ALERT", self.genericCallback, 1)
        self.LWRP.sendCommand("LVL " + ioch + " " + chnum + " CLIP.LEVEL:" + threshold + " CLIP.TIME:" + timems)

        self.waitingForCallback = True
        return self.waitForCallback()


    def levelAlertSub(self, callback):
        """Subscribe to Level Alerts (Silence & Clipping detection)."""
        self.LWRP.addSubscription("LEVEL_ALERT", callback, False)

    def GPIData(self):
        """Get current GPI state data."""
        self.LWRP.addSubscription("GPI", self.genericCallback, 1)
        self.LWRP.sendCommand("ADD GPI")

        self.waitingForCallback = True
        return self.waitForCallback()

    def GPIDataSub(self, callback):
        """Subscribe to GPI data updates."""
        self.LWRP.addSubscription("GPI", callback, False)
        self.LWRP.sendCommand("ADD GPI")

    def GPOData(self):
        """Get current GPO state data."""
        self.LWRP.addSubscription("GPO", self.genericCallback, 1)
        self.LWRP.sendCommand("ADD GPO")

        self.waitingForCallback = True
        return self.waitForCallback()

    def GPODataSub(self, callback):
        """Subscribe to GPO data updates."""
        self.LWRP.addSubscription("GPO", callback, False)
        self.LWRP.sendCommand("ADD GPO")

    def setGPO(self, chnum, pin, state, type = "GPO"):
        """Set the GPO pin state for a specific channel."""
        chnum = str(int(chnum))
        pinstr = ""

        if state == "low":
            state = "l"
        elif state == "high":
            state = "h"
        else:
            raise ValueError("Incorrect pin state specified")

        # Build the pin state string (e.g. xxlxx will make pin 3 low)
        for i in range(1, 6):
            if i == pin:
                pinstr += state
            else:
                pinstr += "x"

        self.LWRP.sendCommand(type + " " + chnum + " " + pinstr)
    
    def setGPI(self, chnum, pin, state):
        """Set the GPI pin state for a specific channel."""
        self.setGPO(chnum, pin, state, "GPI")

    def setGPIText(self, chnum, commandText):
        """Set the GPI text command for a specific channel."""
        chnum = str(chnum)
        commandText = str(commandText).replace('"', '\"')[:128]

        self.LWRP.sendCommand("GPI " + chnum + " CMD:\"" + commandText + "\"")

    def setGPOText(self, chnum, commandText):
        """Set the GPO text command for a specific channel."""
        chnum = str(chnum)
        commandText = str(commandText).replace('"', '\"')[:128]

        self.LWRP.sendCommand("GPO " + chnum + " CMD:\"" + commandText + "\"")
