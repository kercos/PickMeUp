import logging
from google.appengine.ext import ndb
import itinerary
import time_util

import utility

class Person(ndb.Model):
    name = ndb.StringProperty()
    active = ndb.BooleanProperty(default=False) # if active driver, passenger
    last_name = ndb.StringProperty(default='-')
    username = ndb.StringProperty(default='-')
    last_mod = ndb.DateTimeProperty(auto_now=True)
    last_seen = ndb.DateTimeProperty()
    chat_id = ndb.IntegerProperty()
    state = ndb.IntegerProperty()
    ticket_id = ndb.StringProperty()
    last_type = ndb.StringProperty(default='-1')
    location = ndb.StringProperty(default='-')
    language = ndb.StringProperty(default='IT')
    enabled = ndb.BooleanProperty(default=True)
    agree_on_terms = ndb.BooleanProperty(default=False)
    notification_enabled = ndb.BooleanProperty(default=True)
    bus_stop_start = ndb.StringProperty()
    bus_stop_end = ndb.StringProperty()
    bus_stop_mid_going = ndb.StringProperty(repeated=True)
    bus_stop_mid_back = ndb.StringProperty(repeated=True)
    tmp = ndb.StringProperty(repeated=True)
    last_city = ndb.StringProperty()
    notified = ndb.BooleanProperty(default=False)
    prev_state = ndb.IntegerProperty()
    basic_route = ndb.StringProperty()

    def getFirstName(self, escapeMarkdown=True):
        if escapeMarkdown:
            return utility.escapeMarkdown(self.name.encode('utf-8'))
        return self.name.encode('utf-8')

    def getLastName(self, escapeMarkdown=True):
        if self.last_name == None:
            return None
        if escapeMarkdown:
            return utility.escapeMarkdown(self.last_name.encode('utf-8'))
        return self.last_name.encode('utf-8')

    def getUsername(self):
        return self.username.encode('utf-8') if self.username else None

    def getUserInfoString(self, escapeMarkdown=True):
        info = self.getFirstName(escapeMarkdown)
        if self.last_name:
            info += ' ' + self.getLastName(escapeMarkdown)
        if self.username:
            info += ' @' + self.getUsername()
        info += ' ({})'.format(self.chat_id)
        return info

    def getBusStartStr(self):
        return None if self.bus_stop_start is None else self.bus_stop_start.encode('utf-8')

    def getBusEndStr(self):
        return None if self.bus_stop_end is None else self.bus_stop_end.encode('utf-8')

    def getBusStopMidGoingStr(self):
        return ' '.join([x.encode('utf-8') for x in self.bus_stop_mid_going])

    def getBusStopMidBackStr(self):
        return ' '.join([x.encode('utf-8') for x in self.bus_stop_mid_back])

    def setEnabled(self, enabled, put=False):
        self.enabled = enabled
        if put:
            self.put()

    def getDestination(p):
        if p.location == p.bus_stop_start:
            return p.getBusEndStr()
        return p.getBusStartStr()

    def getDeparture(p):
        if p.location == p.bus_stop_start:
            return p.getBusStartStr()
        return p.getBusEndStr()


def addPerson(chat_id, name):
    p = Person(
        id=str(chat_id),
        name=name,
        chat_id=chat_id,
    )
    p.put()
    return p

def getPersonByChatId(chat_id):
    return Person.get_by_id(str(chat_id))

def updateUsername(p, username):
    if (p.username!=username):
        p.username = username
        p.put()

def getPerson(chat_id):
    return Person.query(Person.chat_id==chat_id).get()

def setActive(p, active):
    p.active = active
    p.put()

def setType(p, type):
    p.last_type = type
    p.put()

def setState(p, state):
    p.prev_state = p.state
    p.state = state
    p.put()

def setLastSeen(p, date):
    p.last_seen = date
    p.put()

def updateLastSeen(p):
    p.last_seen = time_util.now()
    p.put()

def setNotified(p, value):
    p.notified = value
    p.put()

def setLastCity(p, last_city):
    p.last_city = last_city
    p.put()

def getMidPoints(p):
    if p.location==p.bus_stop_start:
        return p.bus_stop_mid_going
    return p.bus_stop_mid_back

def getItineraryString(p, driver):
    start = p.getDeparture()
    end = p.getDestination()
    midPoints = []
    if driver:
        midPoints = getMidPoints(p)
    txt = start + " -> "
    for mp in midPoints:
        txt += mp + " -> "
    txt += end
    return txt

def getLocationCluster(p):
    return itinerary.getBusStop(p.last_city, p.location).cluster

def getDestinationCluster(p):
    return itinerary.getBusStop(p.last_city, p.getDestination()).cluster

def getBusStop(p):
    return itinerary.getBusStop(p.last_city, p.location)

def setLocation(p, loc):
    p.location = loc
    p.put()

def setStateLocation(p, state, loc):
    p.state = state
    p.location = loc
    p.put()

def setNotifications(p,value):
    p.notification_enabled = value
    p.put()

def setAgreeOnTerms(p):
    p.agree_on_terms = True
    p.put()

def clearTmp(p):
    p.tmp = []
    p.put()


def setTmp(p, value):
    p.tmp = value
    p.put()

def appendTmp(p, value):
    # value mus be a list
    for x in value:
        p.tmp.append(x)
    p.put()


def isItinerarySet(p):
    return p.bus_stop_start!=None and p.bus_stop_end!=None

def setBusStopStart(p, bs): #, swap_active=False
    swapped = False
    if bs == p.bus_stop_end:
        p.bus_stop_end = p.bus_stop_start
        tmp = p.bus_stop_mid_going
        p.bus_stop_mid_going = p.bus_stop_mid_back
        p.bus_stop_mid_back = tmp
        swapped = True
    p.bus_stop_start = bs
    #if swap_active:
    if bs in p.bus_stop_mid_going:
        index = p.bus_stop_mid_going.index(bs)
        p.bus_stop_mid_going = p.bus_stop_mid_going[index+1:]
        swapped = True
    if bs in p.bus_stop_mid_back:
        index = p.bus_stop_mid_back.index(bs)
        p.bus_stop_mid_back = p.bus_stop_mid_back[:index]
        swapped = True
    if not swapped:
        p.basic_route = None
    p.put()

def setBusStopEnd(p, bs): #, swap_active=False
    swapped = False
    if bs == p.bus_stop_start:
        p.bus_stop_start = p.bus_stop_end
        tmp = p.bus_stop_mid_going
        p.bus_stop_mid_going = p.bus_stop_mid_back
        p.bus_stop_mid_back = tmp
        swapped = True
    p.bus_stop_end = bs
    #if swap_active:
    if bs in p.bus_stop_mid_going:
        index = p.bus_stop_mid_going.index(bs)
        p.bus_stop_mid_going = p.bus_stop_mid_going[:index]
        swapped = True
    if bs in p.bus_stop_mid_back:
        index = p.bus_stop_mid_back.index(bs)
        p.bus_stop_mid_back = p.bus_stop_mid_back[index+1:]
        swapped = True
    if not swapped:
        p.basic_route = None
    p.put()

def appendBusStopMidGoing(p, bs):
    #if p.bus_stop_intermediate_going is None:
    #    p.bus_stop_intermediate_going = []
    p.bus_stop_mid_going.append(bs)
    p.basic_route = None
    p.put()

def appendBusStopMidBack(p, bs):
    #if p.bus_stop_intermediate_back is None:
    #    p.bus_stop_intermediate_back = []
    p.bus_stop_mid_back.append(bs)
    p.basic_route = None
    p.put()

def emptyBusStopMidGoing(p):
    p.bus_stop_mid_going = []
    p.basic_route = None
    p.put()

def emptyBusStopMidBack(p):
    p.bus_stop_mid_back = []
    p.basic_route = None
    p.put()

def resetTermsAndNotification():
    qry = Person.query()
    count = 0
    for p in qry:
        p.agree_on_terms = False
        p.notification_enabled = True
        p.put()
        count+=1
    return count

def resetBasicRoutes():
    qry = Person.query()
    count = 0
    for p in qry:
        p.basic_routes = None
        p.put()
        count+=1
    return count


def resetActive():
    qry = Person.query()
    count = 0
    for p in qry:
        p.active = False
        p.put()
        count+=1
    return count

def resetAllState(s):
    qry = Person.query()
    count = 0
    for p in qry:
        p.state = s
        p.put()
        count+=1
    logging.debug("Reset all states to " + str(s) + ": " + str(count))
    return count

def resetNullStatesUsers():
    qry = Person.query()
    count = 0
    for p in qry:
        if (p.state is None): # or p.state>-1
            setState(p,-1)
            count+=1
    return count

def resetLanguages():
    qry = Person.query()
    for p in qry:
        p.language = 'IT'
        p.put()

def resetEnabled():
    qry = Person.query()
    for p in qry:
        p.enabled = True
        p.put()

def isDriverOrPassenger(p):
    return p.state in [21, 22, 23, 30, 31, 32, 33]

def listAllDrivers():
    qry = Person.query().filter(Person.state.IN([30, 31, 32, 33]))
    if qry.get() is None:
        return "No drivers found"
    else:
        #qry = qry.order(-Person.last_mod)
        text = ""
        for d in qry:
            text = text + d.name.encode('utf-8') + _(' ') + d.location + _(" (") + str(d.state) + \
                   _(") ") + time_util.get_time_string(d.last_seen) + _("\n")
        return text


def listAllPassengers():
    qry = Person.query().filter(Person.state.IN([21, 22, 23]))
    if qry.get() is None:
        return _("No passangers found")
    else:
        #qry = qry.order(-Person.last_mod)
        text = ""
        for p in qry:
            text = text + p.name.encode('utf-8') + _(' ') + p.location + " (" + str(p.state) + ") " + time_util.get_time_string(p.last_seen) + _("\n")
        return text

"""
ACTIVE PERSON
"""
"""
class ActivePerson(ndb.Model):
    #person = ndb.StructuredProperty(Person)
    state = ndb.IntegerProperty()
    last_city = ndb.StringProperty()
    last_type = ndb.StringProperty()
    last_seen = ndb.DateTimeProperty()

def addActivePerson(p):
    #ap.key = ndb.Key(ActivePerson, str(person.chat_id))
    ap = ActivePerson(id=str(p.chat_id), state=p.state, last_city=p.last_city,
                      last_type=p.last_type, last_seen=p.last_seen)
    #person=p,
    ap.put()
    #return ap

def setStateActivePerson(person, state):
    ap = ndb.Key(ActivePerson, str(person.chat_id)).get()
    ap.state = state
    ap.put()
    person.state = state
    person.put()

def removeActivePerson(person):
    ndb.Key(ActivePerson, str(person.chat_id)).delete()

"""