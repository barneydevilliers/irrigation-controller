#!/usr/bin/python

import argparse
import time
import MySQLdb
from time import strftime


activeProgramSequences = []


def start(lineid):
    print "starting " + str(lineid)


def stop(lineid):
    print "stopping " + str(lineid)

def getDatabaseConnection():
    database = MySQLdb.connect("farmserver", "root", "root", "irrigation")
    return database

class ProgramSequence:

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

    overrideTime = "06:00"
    print "Detecting current time as " + currentTime + " but using " + overrideTime + " instead for debugging"
    currentTime = overrideTime

    selectStatement = "SELECT programid FROM starts WHERE starts.timeofday='" + currentTime + "'" + evenDaySearchString
    print selectStatement

    cursor = database.cursor()
    cursor.execute(selectStatement)
    results = cursor.fetchall()

    return results



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


