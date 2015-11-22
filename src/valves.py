import os

class valvemanager:

    valvesInterfaceDict = dict()
    valvesStateDict   = dict()
    log = None   

    def exportGpio(self,gpio):
        os.system("echo " + str(gpio) + " > /sys/class/gpio/export")

    def setOutputDirections(self, gpio):
        os.system("echo out > /sys/class/gpio/gpio" + str(gpio) + "/direction")
 
    def setValue(self, gpio, value):
        os.system("echo " + str(value) + " > /sys/class/gpio/gpio" + str(gpio) + "/value")

    def __init__(self,valvesInterfaceDict,logger):
        self.log = logger
        self.log("valvemanager: init with " + str(valvesInterfaceDict))
        self.valvesInterfaceDict = valvesInterfaceDict
        #initialize and set the initial logical state of the interface
        for valve, interface in self.valvesInterfaceDict.iteritems():
            print str(valve) + ":" + str(interface)
            self.valvesStateDict[valve] = "closed"
        #export the gpios to make them accessible in userspace
        for valve, interface in self.valvesInterfaceDict.iteritems():
            print interface
            self.exportGpio(interface)
        #set the output and initial value of each interface
        for valve, interface in self.valvesInterfaceDict.iteritems():
            print interface
            self.setOutputDirections(interface)
            self.setValue(interface, 0)
        #commit the current state to hardware interface
        self.commit()

    def closeList(self,valveList):
        for valve in valveList:
            self.close(valve)

    def openList(self,valveList):
        for valve in valveList:
            self.open(valve)

    def close(self,valve):
        self.valvesStateDict[valve] = "closed"

    def open(self,valve):
        self.valvesStateDict[valve] = "open"

    def commit(self):
        for key, value in self.valvesStateDict.iteritems():
            if "closed" == str(self.valvesStateDict[key]):
                self.log("valvemanager : commit : close " + str(key) + ": interface " + str(self.valvesInterfaceDict[key]) + ": state " + str(self.valvesStateDict[key]))
                self.setValue(self.valvesInterfaceDict[key],"0")
            if "open" == str(self.valvesStateDict[key]):
                self.log("valvemanager : commit : open " + str(key) + ": interface " + str(self.valvesInterfaceDict[key]) + ": state " + str(self.valvesStateDict[key]))
                self.setValue(self.valvesInterfaceDict[key],"1")


