# -*- coding: utf-8 -*-

from google.appengine.ext import ndb
from utility import convertToUtfIfNeeded
import logging

class RideSearch(ndb.Model): #ndb.Model
    person_id = ndb.StringProperty()
    person_name_lastname = ndb.StringProperty()
    person_username = ndb.StringProperty()

    percorso = ndb.StringProperty() # mapping to percorso entry key (percorso.py)

    timestamp = ndb.DateTimeProperty()

    number_results_programmati = ndb.IntegerProperty()
    number_results_abituali = ndb.IntegerProperty()    
    autisti_list_count = ndb.IntegerProperty()    

    def getPersonName(self):
        return convertToUtfIfNeeded(self.person_name_lastname)

    def getPercorso(self):
        return convertToUtfIfNeeded(self.percorso)

    def getRouteEntry(self):
        from route import Route
        result = Route.get_by_id(self.percorso)
        if result is None:
            logging.warning('None route with percorso {} for ride_offer: {}'.format(self.percorso, self))
        return result

def addRideSearch(person, timestamp, percorso, number_results_programmati, number_results_abituali, autisti_list_count):
    import date_time_util as dtu
    s = RideSearch(
        person_id = person.getId(),
        timestamp = timestamp,
        person_name_lastname = person.getFirstNameLastName(),
        person_username=person.getUsername(),
        percorso=percorso,        
        number_results_programmati = number_results_programmati,
        number_results_abituali = number_results_abituali,
        autisti_list_count = autisti_list_count
    )
    s.put()
    return s


def getRideSearchInsertedLastDaysQry(days):
    import date_time_util as dtu
    from datetime import timedelta
    return RideSearch.query(
        RideSearch.timestamp >= dtu.removeTimezone(dtu.nowCET()) - timedelta(days=days)
    )

