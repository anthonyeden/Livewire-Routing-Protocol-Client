"""LWRP Client (Communication Class). An Open-Source Python Client for the Axia Livewire Routing Protocol."""

import socket
import time
import threading

__author__ = "Anthony Eden"
__copyright__ = "Copyright 2015, Anthony Eden / Media Realm"
__credits__ = ["Anthony Eden"]
__license__ = "GPL"
__version__ = "0.1"


class LWRPClientComms(threading.Thread):
    """This class handles all the communications with the LWRP server."""

    # The handle for the socket connection to the LWRP server
    sock = None

    # A list of all commands to send to the LWRP server
    sendQueue = []

    # A list of data types to subscribe to (with callbacks)
    dataSubscriptions = []

    # Should we be shutting down this thread? Set via self.stop()
    _stop = False

    def __init__(self, host, port):
        """Create a socket connection to the LWRP server."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.sock.connect((host, port))
        self.sock.setblocking(0)

        # Start the thread
        threading.Thread.__init__(self)

    def stop(self):
        """Attempt to close this thread."""
        self._stop = True

    def run(self):
        """Method keeps running forever, and handles all the communication with the open LWRP socket."""
        while True:

            # Try and receive data from the LWRP server
            recvData = self.recvUntilNewline()

            if recvData is not None:
                self.processReceivedData(recvData)

            # Check if we've got data to send back to the LWRP server
            if len(self.sendQueue) > 0:
                dataToSend = self.sendQueue[0]

                while dataToSend:
                    sent = self.sock.send(dataToSend)
                    dataToSend = dataToSend[sent:]

                # Once the message has been sent, take it out of the queue
                self.sendQueue.pop(0)

            if self._stop is True:
                # End the thread
                self.sock.close()
                break

            # Lower this number to receive data quicker
            time.sleep(0.1)

    def recvUntilNewline(self):
        """Receive data until we get to the end of a message (also accounts for BEGIN/END blocks)."""
        totalData = ""
        inBlock = False

        while True:
            try:
                totalData += self.sock.recv(1024)
            except:
                pass

            # Check if we're in a data block
            if totalData[:5] == "BEGIN":
                inBlock = True

            # Check if the datablock is over
            if "END" in totalData[-5:]:
                return totalData

            # If we're not in a datablock and a newline is found, return the data
            if "\n" in totalData and inBlock is False:
                return totalData

            # We return 'None' if there's no data to return
            if totalData == "":
                return None

    def processReceivedData(self, recvData):
        """Process the received data from the LWRP server. Attempts to parse it and trigger all the subscribed callbacks."""
        # A dict with all the different message types we've received
        messageTypes = {}

        # Parse the data so it's in a usable format
        # We receive a list in return (one per message - for blocks of data)
        parsedData = self.parseMessage(recvData)

        # Enumerate over all the messages
        for dataIndex, data in enumerate(parsedData):

            # Check if messageTypes already contains a list for this type.
            # If not, create one
            if parsedData[dataIndex]['type'] not in messageTypes:
                messageTypes[parsedData[dataIndex]['type']] = []

            # Add this message to the appropriate messageTypes list
            messageTypes[parsedData[dataIndex]['type']].append(parsedData[dataIndex])

        # Loop over every subscription
        for subI, subX in enumerate(self.dataSubscriptions):

            # If the subscribed command type matches the message's command type
            if subX['commandType'] in messageTypes:

                # Execute the callback!
                subX['callback'](messageTypes[subX['commandType']])

            # Check if we need to decrement the limit
            if self.dataSubscriptions[subI]['limit'] is not False:
                self.dataSubscriptions[subI]['limit'] = self.dataSubscriptions[subI]['limit'] - 1

            # Check if we need to remove this subscription
            if self.dataSubscriptions[subI]['limit'] <= 0 and self.dataSubscriptions[subI]['limit'] is not False:
                self.dataSubscriptions.pop(subI)

    def sendCommand(self, msg):
        """Buffer a command to send."""
        self.sendQueue.append(msg + "\n")

    def addSubscription(self, subType, callbackObj, limit=False, filters={}):
        """Add a subscription to the list of data subscriptions."""
        self.dataSubscriptions.append({
            "commandType": subType,
            "callback": callbackObj,
            "limit": limit
        })

    def splitSegments(self, string):
        """Attempt to parse all the segments provided in return data."""
        segments = []
        currentText = ""
        inSubStr = False
        string += " "

        for char in string:

            if char == " " and inSubStr is False:
                # Finish the segment
                segments.append(currentText)
                currentText = ""

            else:
                # Continue the segment
                if char == '"' and inSubStr is False:
                    inSubStr = True

                elif char == '"' and inSubStr is True:
                    inSubStr = False

                else:
                    currentText += char

        return segments

    def parseMessage(self, data):
        """Parse the messages and put them into a list of dictionaries."""
        allData = []

        for x in data.splitlines():
            data = {}

            if x[:3] == "VER":
                segments = self.splitSegments(x[4:])
                data['type'] = "DEVICE"
                data["attributes"] = self.parseAttributes(segments)

            elif x[:2] == "IP":
                segments = self.splitSegments(x[3:])
                data['type'] = "NETWORK"
                data["attributes"] = self.parseAttributes(segments)

            elif x[:3] == "SET":
                segments = self.splitSegments(x[4:])
                data['type'] = "SET"
                data["attributes"] = self.parseAttributes(segments)

            elif x[:3] == "SRC":
                segments = self.splitSegments(x[4:])
                data['type'] = "SOURCE"
                data["num"] = segments[0]
                data["attributes"] = self.parseAttributes(segments[1:])

            elif x[:3] == "DST":
                segments = self.splitSegments(x[4:])
                data['type'] = "DESTINATION"
                data["num"] = segments[0]
                data["attributes"] = self.parseAttributes(segments[1:])

            elif x[:3] == "MTR":
                segments = self.splitSegments(x[4:])

                data["type"] = "METER"

                if segments[0] == "ICH":
                    data["io"] = "in"
                elif segments[0] == "OCH":
                    data["io"] = "out"
                else:
                    data["io"] = "unknown"

                data["num"] = segments[1]
                data["attributes"] = self.parseAttributes(segments[2:])

            elif x[:3] == "LVL":
                segments = self.splitSegments(x[4:])

                data["type"] = "LEVEL_ALERT"

                if segments[0] == "ICH":
                    data["io"] = "in"
                elif segments[0] == "OCH":
                    data["io"] = "out"
                else:
                    data["io"] = "unknown"

                data["num"] = segments[1].split(".")[0]
                data["side"] = segments[1].split(".")[1]
                data["attributes"] = self.parseAttributes(segments[2:])

            elif x[:3] == "GPI":
                segments = self.splitSegments(x[4:])

                data["type"] = "GPI"
                data["num"] = segments[0]

                if "CMD:" in x:
                    # We have a text command
                    data["attributes"] = self.parseAttributes(segments[1:])
                else:
                    data["pin_states"] = self.parseGPIOStates(segments[1])

            elif x[:3] == "GPO":
                segments = self.splitSegments(x[4:])

                data["type"] = "GPO"
                data["num"] = segments[0]

                if "CMD:" in x:
                    # We have a text command
                    data["attributes"] = self.parseAttributes(segments[1:])
                else:
                    data["pin_states"] = self.parseGPIOStates(segments[1])

            if x[:5] == "ERROR":
                data['type'] = "ERROR"
                data["message"] = x[6:]

            elif x[:5] == "BEGIN":
                pass

            elif x[:3] == "END":
                pass

            if data != {}:
                allData.append(data)

        return allData

    def parseAttributes(self, sections):
        """Parse all known attributes for a command and return in a dictionary."""
        attrs = {}

        for i, x in enumerate(sections):
            if x[:4] == "PEEK":
                # Peak level meters
                # TODO: Convert to a proper format
                attrs["PEAK_L"] = x[5:].split(":")[0]
                attrs["PEAK_R"] = x[5:].split(":")[1]
            elif x[:3] == "RMS":
                # RMS level meters
                # TODO: Convert to a proper format
                attrs["RMS_L"] = x[4:].split(":")[0]
                attrs["RMS_R"] = x[4:].split(":")[1]

            elif x[:4] == "LWRP":
                attrs["protocol_version"] = x[5:]
            elif x[:4] == "DEVN":
                attrs["device_name"] = x[5:]
            elif x[:4] == "SYSV":
                attrs["system_version"] = x[5:]
            elif x[:4] == "NSRC":
                # only parse source type if available
                if '/' in x[5:]:
                    attrs["source_count"] = x[5:].split("/")[0]
                    attrs["source_type"] = x[5:].split("/")[1]
                else:
                    attrs["source_count"] = x[5:]
                    attrs["source_type"] = ''
            elif x[:4] == "NDST":
                attrs["destination_count"] = x[5:]
            elif x[:4] == "NGPI":
                attrs["GPI_count"] = x[5:]
            elif x[:4] == "NGPO":
                attrs["GPO_count"] = x[5:]
            elif x[:7] == "address":
                attrs["ip_address"] = sections[i + 1]
            elif x[:7] == "netmask":
                attrs["ip_netmask"] = sections[i + 1]
            elif x[:7] == "gateway":
                attrs["ip_gateway"] = sections[i + 1]
            elif x[:8] == "hostname":
                attrs["ip_hostname"] = sections[i + 1]
            elif x[:4] == "ADIP":
                attrs["advertisment_ipaddress"] = x[5:]
            elif x[:10] == "IPCLK_ADDR":
                attrs["clock_ipaddress"] = x[11:]
            elif x[:10] == "NIC_IPADDR":
                attrs["nic_ipaddress"] = x[11:]
            elif x[:8] == "NIC_NAME":
                attrs["nic_name"] = x[9:]
            elif x[:4] == "PSNM":
                attrs["name"] = x[5:]
            elif x[:4] == "LWSE":
                if x[5:] == "1":
                    attrs["livestream"] = True
                else:
                    attrs["livestream"] = False
            elif x[:4] == "LWSA":
                attrs["livestream_destination"] = x[5:]
            elif x[:4] == "RTPE":
                if x[5:] == "1":
                    attrs["rtp"] = True
                else:
                    attrs["rtp"] = False
            elif x[:4] == "RTPA":
                attrs["rtp_destination"] = x[6:]
            elif x[:4] == "PSNM":
                # Unknown attribute
                attrs["_PSNM"] = x[5:]
            elif x[:4] == "SHAB":
                # Unknown attribute
                attrs["_SHAB"] = x[5:]
            elif x[:4] == "FASM":
                # Unknown attribute
                attrs["_FASM"] = x[5:]
            elif x[:4] == "BSID":
                # Unknown attribute
                attrs["_BSID"] = x[5:]
            elif x[:4] == "LPID":
                # Unknown attribute
                attrs["_LPID"] = x[5:]
            elif x[:4] == "INGN":
                # Unknown attribute
                attrs["_INGN"] = x[5:]
            elif x[:4] == "ADDR":
                if x[5:12] == "0.0.0.0" or x[5:] == "":
                    attrs["address"] = None
                else:
                    attrs["address"] = x[5:]
            elif x[:4] == "NAME":
                attrs["name"] = x[5:]
            elif x[:4] == "CLIP":
                attrs["clip"] = True
            elif x[:7] == "NO-CLIP":
                attrs["clip"] = False
            elif x[:3] == "LOW":
                attrs["silence"] = True
            elif x[:6] == "NO-LOW":
                attrs["silence"] = False
            elif x[:3] == "CMD":
                attrs["command_text"] = x[4:]

        return attrs

    def parseGPIOStates(self, states):
        """Turn the 'hlHLh' GPIO state strings into a dictionary."""
        attrs = []

        for x in states:
            if x == "h":
                data = {"state": "high", "changing": False}
            elif x == "H":
                data = {"state": "high", "changing": True}
            elif x == "l":
                data = {"state": "low", "changing": False}
            elif x == "L":
                data = {"state": "low", "changing": True}
            else:
                data = {}

            attrs.append(data)

        return attrs
