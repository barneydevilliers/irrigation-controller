#!/usr/bin/python

import time
import MySQLdb
from time import strftime


activeProgramSequences = []


def start(lineid):
    print "starting " + str(lineid)


def stop(lineid):
    print "stopping " + str(lineid)

class ProgramSequence:

    activeProgramSequence = False
    sequence = []
    currentItem = 0

    def __init__(self,programid,cursor):
        select = "SELECT lineid, duration FROM programsequence WHERE programid=" + str(programid) + " ORDER BY seqorder ASC"
        cursor.execute(select)
        self.sequence = cursor.fetchall()

        #Find the first valid line to try and run
        for line in self.sequence:
            print line

            #Check that the duration of the current item is more than 0
            if line[1] > 0:
                self.activeProgramSequence = True
                break;
            else:
                #else move to the next item
                self.currentItem += 1

        #If we have a valid line to run in the sequence, initiate it.
        if self.activeProgramSequence:
            start(self.sequence[self.currentItem])




    def active(self):
        return self.activeProgramSequence



def checkforstarts():

    #Get current time
    currentTime = strftime("%H:%M", time.localtime())
    print currentTime

    #Get even/odd day
    dayOfMonth = time.localtime(time.time())[2]
    if (dayOfMonth%2 == 1):
        evenDaySearchString = " AND ( (starts.days = 'odd') OR (starts.days = 'all') )"
    else:
        evenDaySearchString = " AND ( (starts.days = 'even') OR (starts.days = 'all') )"

    currentTime = "12:00"
    selectStatement = "SELECT programid FROM starts WHERE starts.timeofday='" + currentTime + "'" + evenDaySearchString
    print selectStatement

    database = MySQLdb.connect("farmserver", "root", "root", "irrigation")
    cursor = database.cursor()
    cursor.execute(selectStatement)
    results = cursor.fetchall()


    for result in results:
        print result[0]
        activeProgramSequences.append(ProgramSequence(result[0], cursor))


    print "checking"


while False:

    #sleep until the next minute interval
    time.sleep(60.0 - ((int(time.time()) % 60.0)))

    checkforstarts()

checkforstarts()

for programSequence in activeProgramSequences:
    print programSequence



