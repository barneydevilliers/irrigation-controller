#!/usr/bin/python

import argparse
import yaml
import time
import MySQLdb
import sys
from time import strftime


activeProgramSequences = []

verboseActive = False
config = []


def log(message):
    logMessage = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " | " + str(message)
    print logMessage
    logfile = open(logfilename, 'a')
    logfile.write(logMessage + "\n")
    logfile.close()


def verboseLog(message):
    global verboseActive
    if verboseActive:
        # only print to stdout and log file if verbose has been turned on
        log(message)


def parseArgumentsAndLoadConfig():
    parser = argparse.ArgumentParser(description='Irrigation Controller Service')

    parser.add_argument('--configfile', nargs=1,        help='configuration file to use', default=['/etc/irrigation-controller.yaml'])
    parser.add_argument('--console',    action='count', help='run service in console instead of forked service')
    parser.add_argument('--verbose',    action='count', help='provide verbose debugging')

    args = parser.parse_args()

    configFileName = args.configfile[0]

    global consoleMode
    if (args.verbose > 0):
        consoleMode = True
    else:
        consoleMode = False

    global verboseActive
    if (args.verbose > 0):
        verboseActive = True
    else:
        verboseActive = False

    configFile = open(configFileName)
    global config
    config = yaml.safe_load(configFile)
    configFile.close()



def start(lineid):
    print "starting " + str(lineid)


def stop(lineid):
    print "stopping " + str(lineid)

def getDatabaseConnection():
    database = MySQLdb.connect("farmserver", "root", "root", "irrigation")
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

        #If we have a valid line to run in the sequence, initiate it.
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

    def active(self):
        return self.activeProgramSequence

    def everyMinuteHousekeeping(self):
        print "housekeeping to check if we should keep on with this line or move to the next or exit"
        if self.active() and ((self.currentItemStartTime + self.sequence[self.currentItem][1]) > int(time.time())):
            #the current line item has expired.  Time to move to the next
            self.findAndStartNextValidLine(self.currentItem)
            
            



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
    parseArgumentsAndLoadConfig()

    while True:
        #sleep until the next interval (in seconds)
        checkInterval = 5.0
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
            print "Starting Program sequence : " + str(programsequenceinfo)
            activeProgramSequences.append(ProgramSequence(programsequenceinfo[0], database))




if __name__ == '__main__':
    main()

