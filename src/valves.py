
class valvemanager:

    valveToInterfaceDict = dict()
    interfaceStateDict   = dict()
    
    def __init__(self,valveToInterfaceDict):
        print "valvemanager: init with " + str(valveToInterfaceDict)
        self.valveToInterfaceDict = valveToInterfaceDict
        for key in self.valveToInterfaceDict:
            print str(key) + ":" + str(valveToInterfaceDict[key])
            self.interfaceStateDict[self.valveToInterfaceDict[key]] = "close"

    def closeList(self,valveList):
        print "valvemanager: close list"
        for valve in valveList:
            self.close(valve)

    def openList(self,valveList):
        print "valvemanager: open list"
        for valve in valveList:
            self.open(valve)

    def close(self,valve):
        print "valvemanager: close valve no " + valve + " at interface no " + self.valveToInterfaceDict[valve]
        self.interfaceStateDict[self.valveToInterfaceDict[valve]] = "close"

    def open(self,valve):
        print "valvemanager: open valve no " + valve + " at interface no " + self.valveToInterfaceDict[valve]
        self.interfaceStateDict[self.valveToInterfaceDict[valve]] = "open"

    def commit(self):
        print "valvemanager: commit valves state"
        for key in self.interfaceStateDict:
            print "valvemanager : commit : " + key + ":" + self.interfaceStateDict[key]

