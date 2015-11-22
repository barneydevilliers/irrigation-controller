
class valvemanager:

    valvesInterfaceDict = dict()
    valvesStateDict   = dict()
    log = None   
 
    def __init__(self,valvesInterfaceDict,logger):
        self.log = logger
        self.log("valvemanager: init with " + str(valvesInterfaceDict))
        self.valvesInterfaceDict = valvesInterfaceDict
        for key in self.valvesInterfaceDict:
            self.valvesStateDict[self.valvesInterfaceDict[key]] = "closed"
        #commit the current state to hardware interface
        self.commit()

    def closeList(self,valveList):
        for valve in valveList:
            self.close(valve)

    def openList(self,valveList):
        for valve in valveList:
            self.open(valve)

    def close(self,valve):
        self.valvesStateDict[self.valvesInterfaceDict[valve]] = "closed"

    def open(self,valve):
        self.valvesStateDict[self.valvesInterfaceDict[valve]] = "open"

    def commit(self):
        for key in self.valvesStateDict:
            if "closed" == str(self.valvesStateDict[key]):
                self.log("valvemanager : commit : close " + str(key) + ": interface " + str(self.valvesInterfaceDict[int(key)]) + ": state " + str(self.valvesStateDict[key]))
            if "open" == str(self.valvesStateDict[key]):
                self.log("valvemanager : commit : open " + str(key) + ": interface " + str(self.valvesInterfaceDict[int(key)]) + ": state " + str(self.valvesStateDict[key]))
            


