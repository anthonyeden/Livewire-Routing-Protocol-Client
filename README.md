# Axia Livewire Routing Protocol (LWRP) Client
Python class that behaves as a client of the Axia Livewire Routing Protocol (LWRP).

This is my attempt to implement a LWRP Client as a well-behaved Python class. It heavily utilises threading and callbacks, making it a good candidate to use in a modern event-loop driven web app.

## What is the LWRP?

The Livewire Routing Protocol is the protocol that allows Axia Livewire hardware and software to communicate. Notably, it is used particularly by PathfinderPC and Automation System integrations with the IP Driver. All Livewire devices should implement this protocol.

## What can I do with this class?

Some of the currently implemented functionality:

* Login to a device
* View system/network data about a Livewire device
* View source setup details
* View destination setup details
* View audio levels
* Detect silence & clipping
* View GPI & GPO pin states
* Set GPO pin states
* Set GPI & GPO command text
* Subscribe to changes in source/destination configuration
* Subscribe to changes to GPIO pin states
* Subscribe to silence/clipping alerts
* Subscribe to error notifications

Currently you cannot:

* Update source/destination setup details
* Set system parameters

## How reliable is this? How much testing have you done?

Not much. We've mainly been testing against the IP Driver, although shortly we'll test against a variety of other Axia Livewire devices. Implementations vary between devices, so your milage may vary.

## How to use this script

To import the method, copy "LWRPClient.py" and "LWRPClientComms.py" to your project directory, then:

    import LWRPClient

Note: LWRPClient is what you should always use. It exposes nice APIs for most functionality. LWRPClientComms is the lower-level communication code - best not to use it directly.

To connect and login to a device (LWRP is always port 93):

    from LWRPClient import LWRPClient
    LWRP = LWRPClient("127.0.0.1", 93)
    LWRP.login()

You can view a variety of pieces of information about a device:

    print LWRP.deviceData()
    print LWRP.networkData()
    print LWRP.sourceData()
    print LWRP.destinationData()
    print LWRP.GPIData()
    print LWRP.GPOData()

To get the current audio levels:

    print LWRP.meterData()

To setup a callback for all error messages:

    def errorCallback(data):
        print "--- ERROR CALLBACK ---"
        print data

    LWRP.errorSub(errorCallback)

To set level alert thresholds on input/source #1 and setup the callback for those alerts:

    def levelsCallback(data):
        print "--- LEVELS CALLBACK ---"
        print data

    LWRP.setSilenceThreshold("in", "1", "-100", "2000")
    LWRP.setClippingThreshold("in", "1", "-1", "500")
    LWRP.levelAlertSub(levelsCallback)

You can also subscribe to callbacks for a few other things:

    LWRP.sourceDataSub(myCallback)
    LWRP.destinationDataSub(myCallback)
    LWRP.GPIDataSub(myCallback)
    LWRP.GPODataSub(myCallback)

Set channel 1 GPO pin 2 to low:

    LWRP.setGPO(1, 2, "low")

Set channel 1 GPO to a text string:

    LWRP.setGPOText(1, "ENABLE AUTO MODE")

When you're ready to close the connection, do this:

    LWRP.stop()

##Careful!

This hasn't been tested extensively in production. If you make too many connections, your devices will misbehave. Additionally, there may be unknown bugs. Please test all this on a non-critical network before going anywhere near your air-chain.

No liability will be accepted by the developer of this software.

## More info on the Axia Livewire Protocol

* [What is Livewire+?](http://www.telosalliance.com/Axia/Livewire-AoIP-Networking) (Axia Website)
* [Axia Livewire Channel Numbering](http://www.telosalliance.com/images/Axia%20Products/Support%20Documents/Tech%20Tips/AxiaLivewireChannelNumbering.pdf) (Axia Website - PDF)
* [A Look At Livewire](https://github.com/kylophone/a-look-at-livewire) (Github)
* ["Audio Over IP: Building Pro AoIP Systems with Livewire" by Steve Church & Skip Pizzi](http://www.amazon.com/Audio-Over-IP-Building-Livewire-ebook/dp/B009OYSVV8) (2010 Book)

## Contributing

Contributions are welcomed. Feel free to submit a pull request to fix bugs or add additional functionality to this script.
