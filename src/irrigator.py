#!/usr/bin/python


import thread
import yaml
import time
import MySQLdb
import sys
from time import strftime
import datetime
from daemon import runner
import signal
from flask import Flask, request, send_from_directory
import json
from valves import valvemanager


activeProgramSequences = []
allValvesList = []
verboseActive = False
config = None
valveManager = None


def log(message):
    global config

    logMessage = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " | " + str(message)
    print logMessage
    logfile = open(config.logFileName, 'a')
    logfile.write(logMessage + "\n")
    logfile.close()

def logger(message):
    log(message)

def verboseLog(message):
    global verboseActive
    if verboseActive: # only print to stdout and log file if verbose has been turned on
        log(message)

class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)

def loadConfig():

    if ('console' == sys.argv[1]) and (len(sys.argv) > 2):
        configFileName = sys.argv[2]
    else:
        configFileName = '/etc/irrigation-controller.yaml'


    configFile = open(configFileName)
    global config
    configDict = yaml.safe_load(configFile)
    configFile.close()
    config = Struct(**configDict)

    welcomeString = "Starting Irrigation Controller in "
    if 'console' == sys.argv[1]:
        welcomeString += "console mode"
    else:
        welcomeString += "forked service"
    log(welcomeString)

    log("Parsed the configuration in " + configFileName + " as " + str(configDict))

def openValvesList(valvesList):
    log('Opening valves ' + str(valvesList))
    global valveManager
    valveManager.openList(valvesList)

def closeValvesList(valvesList):
    log('Closing valves ' + str(valvesList))
    global valveManager
    valveManager.closeList(valvesList)

def commit():
    log("commit")
    global valveManager
    valveManager.commit()


def getDatabaseConnection():
    global config
    database = MySQLdb.connect(config.database['host'], config.database['username'], config.database['password'], "irrigation")
    return database


def getDependencyValves(valve,database):
    select = "SELECT dependonvalveid FROM irrigation.valvedependencies WHERE valveid=" + str(valve)
    cursor = database.cursor()
    cursor.execute(select)
    valveDependancyTuples = cursor.fetchall()
    valveDependancyList = []
    #add this valve to the list of it's dependencies to get a complete list of all the valves that needs to turn on
    valveDependancyList.append(valve)
    #add dependencies
    for dependency in valveDependancyTuples:
        valveDependancyList.append(dependency[0])
    return valveDependancyList


def getAllValves(database):
    select = "SELECT id, interface FROM irrigation.valves"
    cursor = database.cursor()
    cursor.execute(select)
    valveInfos = cursor.fetchall()
    valvesDict = dict()
    for valveInfo in valveInfos:
        valvesDict[valveInfo[0]] = valveInfo[1] #map id to interface
    return valvesDict

def getAllValvesList(database):
    select = "SELECT id FROM irrigation.valves"
    cursor = database.cursor()
    cursor.execute(select)
    valveTuples = cursor.fetchall()
    valvesList = []
    for valve in valveTuples:
        valvesList.append(valve[0])
    return valvesList


class ProgramSequence:

    description = "no-program-description"
    activeProgramSequence = False
    sequence = []
    currentValve = 0
    currentValveStopTime = 0
    runningValveList = []

    def findAndStartNextValidValveRun(self,indexToSearchFrom,database):
        index = indexToSearchFrom
        self.activeProgramSequence = False

        if indexToSearchFrom >= len(self.sequence):
            return #abort the search since we are already at the end of the sequence list

        for valveRun in self.sequence[index:]:
            #Check if the runtime of the current item is more than 0
            if valveRun[1] > 0:
                #Found the first valid line to run in the sequence.
                #Set the program sequence as active and break from the search for the first item.
                self.activeProgramSequence = True
                break;
            #move to the next item if this item is not valid
            index += 1

        #If we have a new valid line to run in the sequence, initiate it.
        if self.activeProgramSequence:            
            self.currentValve = index
            #Calculate and set the valve stop time on a minute boundary
            currentTimeToTheSecond = int(time.time())
            currentTimeToTheMinute = currentTimeToTheSecond - (currentTimeToTheSecond % 60)
            self.currentValveStopTime = currentTimeToTheMinute + (self.sequence[self.currentValve][1] * 60)
            #start the valve
            self.start(self.sequence[self.currentValve][0],database)
            

    def __init__(self,programid,database):
        #Populate the sequence from the database
        select = "SELECT valveid, runtime FROM programsequence WHERE programid=" + str(programid) + " ORDER BY sequenceorder ASC"
        cursor = database.cursor()
        cursor.execute(select)
        self.sequence = list(cursor.fetchall())

        #Find and set the program sequence description
        select = "SELECT description FROM programs WHERE id=" + str(programid)
        cursor = database.cursor()
        cursor.execute(select)
        descriptionQueryResult = list(cursor.fetchall())
        if len(descriptionQueryResult) > 0:
            self.description = descriptionQueryResult[0][0]
        log("Starting Program Sequence : " + self.description)

        #Find the first valid line to try and run
        self.findAndStartNextValidValveRun(0,database)
        commit()

    def active(self):
        return self.activeProgramSequence

    def everyMinuteHousekeeping(self,database):
        if self.active() and (self.currentValveStopTime <= int(time.time())):
            #the current line item has expired.  Time to move to the next
            self.stop(self.sequence[self.currentValve][0],database)
            self.findAndStartNextValidValveRun(self.currentValve+1,database)
            commit()

    def start(self,valve,database):
        valvesToStart = getDependencyValves(valve, database)
        openValvesList(valvesToStart)

    def stop(self,valve,database):
        valvesToClose = getDependencyValves(valve, database)
        closeValvesList(valvesToClose)

def checkForStarts(database):

    #Get current time
    currentTime = strftime("%H:%M", time.localtime())
    #Get even/odd/all day
    dayOfMonth = time.localtime(time.time())[2]
    if (dayOfMonth%2 == 1):
        evenDaySearchString = " AND ( (starts.days = 'odd') OR (starts.days = 'all') )"
    else:
        evenDaySearchString = " AND ( (starts.days = 'even') OR (starts.days = 'all') )"
    selectStatement = "SELECT programid FROM starts WHERE starts.timeofday='" + currentTime + "'" + evenDaySearchString
    cursor = database.cursor()
    cursor.execute(selectStatement)
    return cursor.fetchall()


def handleSignal(signum, stack):
    global allValvesList
    global valveManager
    log('SIGTERM received. closing all valves : ' + str(allValvesList))
    valveManager.closeList(allValvesList)
    exit(0)



restWebApp = Flask(__name__, static_url_path='')

@restWebApp.route("/")
def route():
    print "main page static"
    return restWebApp.send_static_file('index.html')



@restWebApp.route("/api/open/<int:valveid>/<int:opentime>")
def openValve(valveid,opentime):
    log("Manual request to open valve id " + str(valveid) + " for " + str(opentime) + " minutes (WARNING!!! NO auto closing after said minutes yet!!!")
    database = getDatabaseConnection()
    valves = getDependencyValves(valveid,database)
    openValvesList(valves)
    commit()
    return "Manual request to open valve id " + str(valves) + " for " + str(opentime) + " minutes (WARNING!!! NO auto closing after said minutes yet!!!"

@restWebApp.route("/api/closeall")
@restWebApp.route("/api/close/<int:valveid>")
def closeValve(valveid=None):
    database = getDatabaseConnection()
    
    valves = []
    if valveid==None:
        valves = getAllValvesList(database)
        log("Manual request to close all valves" + str(valves))
    else:
        valves = getDependencyValves(valveid,database)
        log("Manual request to close valve ids" + str(valves))
    
    closeValvesList(valves)
    commit()
    return "Closing valves " + str(valves)

@restWebApp.route("/api/info/valves")
def getAllValvesInfo():
    database = getDatabaseConnection()
    
    select = "SELECT id, description FROM irrigation.valves"
    cursor = database.cursor()
    cursor.execute(select)
    valveTuples = cursor.fetchall()
    valvesDict = {}
    for valve in valveTuples:
        if valve[1] != "Unused":
            valvesDict[valve[1]] = valve[0]
    return json.dumps(valvesDict)

def threadWebApp():
    log("Starting the Web Application Thread")
    restWebApp.run(debug=True, host='0.0.0.0')

def threadJobScheduler():
    log("Starting the Job Scheduler Thread")
    while True:
        #sleep until the next minute boundary
        checkInterval = 60.0 #in seconds
        time.sleep(checkInterval - ((int(time.time()) % checkInterval)))
    
        #Get a new database connection we will use for this interval
        database = getDatabaseConnection()

        #At each interval we iterate through any active program sequence and allow it to do housekeeping
        for programSequence in activeProgramSequences:
            programSequence.everyMinuteHousekeeping(database)

        #Remove any program sequence that is not active anymore from the list (finished the sequence)
        activeProgramSequences[:] = [item for item in activeProgramSequences if item.active()]

        #At each interval we also check if there are new program sequences we need to start
        database = getDatabaseConnection()
        for programsequenceinfo in checkForStarts(database):
            log ("Starting Program sequence : " + str(programsequenceinfo))
            activeProgramSequences.append(ProgramSequence(programsequenceinfo[0], database))

        database.close()

class ServiceDaemon():
    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/tty'
        self.stderr_path = '/dev/tty'
        self.pidfile_path =  '/tmp/irrigator.pid'
        self.pidfile_timeout = 5

    def run(self):
        main()


def main():
    initialize()
    
    #Start the job scheduler in the main parent thread
    thread.start_new_thread(threadJobScheduler,())

    threadWebApp()

def initialize():
    #load config from etc
    loadConfig()

    #install signal handler for SIGTERM
    signal.signal(signal.SIGTERM, handleSignal)

    #get and initialize the valvemanager to reset/close all valves on startup
    database = getDatabaseConnection()
    global allValvesList
    allValvesList = getAllValves(database)
    global valveManager
    valveManager = valvemanager(allValvesList,logger)
    database.close()



if __name__ == '__main__':
    if (len(sys.argv) > 1):
        if 'console' == sys.argv[1]:
            main()
        else:
            daemon = ServiceDaemon()
            daemon_runner = runner.DaemonRunner(daemon)
            daemon_runner.do_action()
    else:
        print "Need an argument"
        exit(1)
