#!/usr/bin/python

import argparse
import yaml
import time
import MySQLdb
import sys
from time import strftime
import datetime
from daemon import runner

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

def start(lineid):
    log("starting " + str(lineid))


def stop(lineid):
    log("stopping " + str(lineid))

def commit():
    log("commit")

def getDatabaseConnection():
    global config
    database = MySQLdb.connect(config.database['host'], config.database['username'], config.database['password'], "irrigation")
    return database

class ProgramSequence:

    description = ""
    activeProgramSequence = False
    sequence = []
    currentItem = 0
    currentItemStartTime = 0

    def findAndStartNextValidLine(self,searchFromCurrentItem):
        listStartOfSearchIndex = searchFromCurrentItem + 1
        self.activeProgramSequence = False
        for line in self.sequence[listStartOfSearchIndex:]:
            #Check if the runtime of the current item is more than 0
            if line[1] > 0:
                #Found the first valid line to run in the sequence.
                #Set the program sequence as active and break from the search for the first item.
                self.activeProgramSequence = True
                break;
            else:
                #else move to the next item
                self.currentItem += 1

        #If we have a new valid line to run in the sequence, initiate it.
        if self.activeProgramSequence:
            start(self.sequence[self.currentItem][0])
            self.currentItemStartTime = int(time.time())

    def __init__(self,programid,database):
        #Populate the sequence from the database
        select = "SELECT lineid, runtime FROM programsequence WHERE programid=" + str(programid) + " ORDER BY sequenceorder ASC"
        cursor = database.cursor()
        cursor.execute(select)
        self.sequence = cursor.fetchall()

        #Find and set the program sequence description
        select = "SELECT description FROM programs WHERE id=" + str(programid)
        cursor = database.cursor()
        cursor.execute(select)
        self.description = cursor.fetchall()[0]

        #Find the first valid line to try and run
        self.findAndStartNextValidLine(-1) #Minus 1 means we need to traverse the whole list.
        commit()

    def active(self):
        return self.activeProgramSequence

    def everyMinuteHousekeeping(self):
        if self.active() and ((self.currentItemStartTime + self.sequence[self.currentItem][1]) > int(time.time())):
            #the current line item has expired.  Time to move to the next
            stop(self.sequence[self.currentItem][0])
            self.findAndStartNextValidLine(self.currentItem)
            commit()
            



def checkforstarts(database):

    #Get current time
    currentTime = strftime("%H:%M", time.localtime())
    print currentTime

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






def main():

    loadConfig()

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


