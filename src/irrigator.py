#!/usr/bin/python

import yaml
import time
import MySQLdb
import sys
from time import strftime
import datetime
from daemon import runner
import signal


activeProgramSequences = []

verboseActive = False
config = None



class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)

def log(message):
    global config

    logMessage = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " | " + str(message)
    print logMessage
    logfile = open(config.logFileName, 'a')
    logfile.write(logMessage + "\n")
    logfile.close()


def verboseLog(message):
    global verboseActive
    if verboseActive: # only print to stdout and log file if verbose has been turned on
        log(message)


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

def start(valveid):
    log("starting " + str(valveid))


def stop(valveid):
    log("stopping " + str(valveid))

def commit():
    log("commit")

def getDatabaseConnection():
    global config
    database = MySQLdb.connect(config.database['host'], config.database['username'], config.database['password'], "irrigation")
    return database

class ProgramSequence:

    description = "no-program-description"
    activeProgramSequence = False
    sequence = []
    currentValve = 0
    currentValveStopTime = 0
    runningValveList = []

    def findAndStartNextValidValveRun(self,searchFromCurrentValveRun):
        listStartOfSearchIndex = searchFromCurrentValveRun + 1
        self.activeProgramSequence = False
        for valveRun in self.sequence[listStartOfSearchIndex:]:
            #Check if the runtime of the current item is more than 0
            if valveRun[1] > 0:
                #Found the first valid line to run in the sequence.
                #Set the program sequence as active and break from the search for the first item.
                self.activeProgramSequence = True
                break;
            else:
                #else move to the next item
                self.currentValve += 1

        #If we have a new valid line to run in the sequence, initiate it.
        if self.activeProgramSequence:            
            #Calculate and set the valve stop time on a minute boundary
            currentTimeToTheSecond = int(time.time())
            currentTimeToTheMinute = currentTimeToTheSecond - (currentTimeToTheSecond % 60)
            self.currentValveStopTime = currentTimeToTheMinute + (self.sequence[self.currentValve][1] * 60)
            #start the valve
            start(self.sequence[self.currentValve][0])

    def __init__(self,programid,database):
        #Populate the sequence from the database
        select = "SELECT valveid, runtime FROM programsequence WHERE programid=" + str(programid) + " ORDER BY sequenceorder ASC"
        cursor = database.cursor()
        cursor.execute(select)
        self.sequence = cursor.fetchall()

        #Find and set the program sequence description
        select = "SELECT description FROM programs WHERE id=" + str(programid)
        cursor = database.cursor()
        cursor.execute(select)
        descriptionQueryResult = cursor.fetchall()

        if len(descriptionQueryResult) > 0:
            self.description = descriptionQueryResult[0][0]

        log("Starting " + self.description)
        
        #Find the first valid line to try and run
        self.findAndStartNextValidValveRun(-1) #Minus 1 means we need to traverse the whole list.
        commit()

    def active(self):
        return self.activeProgramSequence

    def everyMinuteHousekeeping(self):
        print "timeNow=" + str(int(time.time()))
        print "active=" + str(self.active())
        print "self.currentValveStopTime=" + str(self.currentValveStopTime)
        print "self.currentValve=" + str(self.currentValve)
        if self.active() and (self.currentValveStopTime <= int(time.time())):
            #the current line item has expired.  Time to move to the next
            stop(self.sequence[self.currentValve][0])
            self.findAndStartNextValidValveRun(self.currentValve)
            commit()

    def start(valve):
        #first we need to find any valves this valve is dependent on
        select = "SELECT dependonvalveid FROM irrigation.valvedependencies WHERE valveid=" + str(valve)
        cursor = database.cursor()
        cursor.execute(select)
        runningValveList = cursor.fetchall()
        
        #add this valve to the list of it's dependencies to get a complete list of all the valves that needs to turn on
        runningValveList.append(valve)

        log('Starting valves ' + str(valvesToStart))

    def stop(valve):
        log('stopping')


def checkforstarts(database):

    #Get current time
    currentTime = strftime("%H:%M", time.localtime())

    #Get even/odd day
    dayOfMonth = time.localtime(time.time())[2]
    if (dayOfMonth%2 == 1):
        evenDaySearchString = " AND ( (starts.days = 'odd') OR (starts.days = 'all') )"
    else:
        evenDaySearchString = " AND ( (starts.days = 'even') OR (starts.days = 'all') )"

    selectStatement = "SELECT programid FROM starts WHERE starts.timeofday='" + currentTime + "'" + evenDaySearchString

    cursor = database.cursor()
    cursor.execute(selectStatement)
    results = cursor.fetchall()

    return results




def handleSigTERM(signum, stack):
    log('SIGTERM received. TODO Stopping all valves')
    exit(0)

def main():

    loadConfig()


    #install signal handler for SIGTERM
    signal.signal(signal.SIGTERM, handleSigTERM)

    while True:
        #sleep until the next minute boundary
        checkInterval = 60.0 #in seconds
        time.sleep(checkInterval - ((int(time.time()) % checkInterval)))
    
        #Get a new database connection we will use for this interval
        database = getDatabaseConnection()

        #At each interval we iterate through any active program sequence and allow it to do housekeeping
        for programSequence in activeProgramSequences:
            programSequence.everyMinuteHousekeeping()

        #Remove any program sequence that is not active anymore from the list (finished the sequence)
        activeProgramSequences[:] = [item for item in activeProgramSequences if item.active()]

        #At each interval we also check if there are new program sequences we need to start
        database = getDatabaseConnection()
        for programsequenceinfo in checkforstarts(database):
            log ("Starting Program sequence : " + str(programsequenceinfo))
            activeProgramSequences.append(ProgramSequence(programsequenceinfo[0], database))




class ServiceDaemon():
    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/tty'
        self.stderr_path = '/dev/tty'
        self.pidfile_path =  '/tmp/irrigator.pid'
        self.pidfile_timeout = 5

    def run(self):
        main()



if __name__ == '__main__':

    if 'console' == sys.argv[1]:
        main()
    else:
	daemon = ServiceDaemon()
        daemon_runner = runner.DaemonRunner(daemon)
        daemon_runner.do_action()


