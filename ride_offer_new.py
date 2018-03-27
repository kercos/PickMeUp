# -*- coding: utf-8 -*-

from google.appengine.ext import ndb
from utility import convertToUtfIfNeeded

class RideOfferNew(ndb.Model): #ndb.Model
    driver_id = ndb.StringProperty()
    driver_name_lastname = ndb.StringProperty()
    driver_username = ndb.StringProperty()

    percorso = ndb.StringProperty() # mapping to percorso entry key (percorso.py)

    registration_datetime = ndb.DateTimeProperty()  # for programmati only time applies
    start_datetime = ndb.DateTimeProperty()  # for programmati only time applies
    
    active = ndb.BooleanProperty(default=True) # when a ride is removed it remains in the db a disactivated
    disactivation_datetime = ndb.DateTimeProperty()

    time_mode = ndb.StringProperty()  # BOTTONE_ADESSO, BOTTONE_OGGI, BOTTONE_PROX_GIORNI, BOTTONE_PROGRAMMATO

    # only for multi rides (periodico o abiuale)
    programmato = ndb.BooleanProperty(default=False)

    programmato_giorni = ndb.IntegerProperty(repeated=True) # Monday is 0 and Sunday is 6
    # also used for prox. ggiorni mode
    # for time start_datetime is used

    average_distance = ndb.StringProperty()
    average_duration = ndb.StringProperty()

    distanza = ndb.IntegerProperty(repeated=True)

    def getDriverName(self):
        return convertToUtfIfNeeded(self.driver_name_lastname)

    def getPercorso(self):
        return convertToUtfIfNeeded(self.percorso)

    def getRouteEntry(self):
        from route import Route
        return Route.get_by_id(self.percorso)

    def getDepartingTimeStr(self):
        import date_time_util as dtu
        #return dtu.formatTime(self.programmato_time)
        return dtu.formatTime(self.start_datetime.time())

    def getProgrammato_giorni_str(self):
        if self.programmato_giorni:
            return ', '.join([str(x) for x in self.programmato_giorni])
        return None

    def getDepartingDateStr(self):
        import date_time_util as dtu
        import params
        date_str = dtu.formatDate(self.start_datetime)
        if date_str == dtu.formatDate(dtu.nowCET()):
            date_str += ' (OGGI)'
        elif date_str == dtu.formatDate(dtu.tomorrow()):
            date_str += ' (DOMANI)'
        elif self.programmato_giorni:  # PROX_GIORNI
            giorno_index = self.programmato_giorni[0]
            date_str += ' ({})'.format(params.GIORNI_SETTIMANA[giorno_index])
        return date_str

    def getTimeMode(self):
        return convertToUtfIfNeeded(self.time_mode)

    def disactivate(self,  put=True):
        import date_time_util as dtu
        self.active = False
        self.disactivation_datetime = dtu.removeTimezone(dtu.nowCET())
        if put:
            self.put()

    def getAvgDistanceDuration(self):
        if self.average_distance is None:
            # initializing it the first time
            route = self.getRouteEntry()
            self.average_distance = route.average_distance
            self.average_duration = route.average_duration
            self.put()
        return self.average_distance, self.average_duration

    def getDescription(self, driver_info=True):
        import routing_util
        import params
        import date_time_util as dtu
        import person
        msg = []
        percorso = self.getPercorso()
        start_stop, end_stop = routing_util.decodePercorsoShort(percorso)

        msg.append('*Partenza*: {}'.format(start_stop))
        msg.append('*Arrivo*: {}'.format(end_stop))

        if self.programmato:
            msg.append('*Tipologia*: {}'.format(self.getTimeMode()))
            if self.start_datetime:
                giorni = [params.GIORNI_SETTIMANA_FULL[i] for i in self.programmato_giorni]
                giorni_str = ', '.join(giorni)
                msg.append('*Ora partenza*: {}'.format(self.getDepartingTimeStr()))
                msg.append('*Ogni*: {}'.format(giorni_str))
        else:
            msg.append('*Quando*: {}'.format(self.getTimeMode()))
            msg.append('*Giorno partenza*: {}'.format(self.getDepartingDateStr()))
            msg.append('*Ora partenza*: {}'.format(self.getDepartingTimeStr()))
        if driver_info:
            username = person.getPersonById(self.driver_id).getUsername()  # self.driver_username
            if username is None:
                from main import tell_admin
                tell_admin('❗ viaggio con driver_id {} non ha più username'.format(self.driver_id))
                username = '(username non più disponibile)'
            else:
                username = '@{}'.format(username)
            msg.append('*Autista*: {} {}'.format(self.getDriverName(), username))
            avg_distance, avg_duration = self.getAvgDistanceDuration()
            msg.append('*Distanza*: {}'.format(avg_distance))
            msg.append('*Durata*: {}'.format(avg_duration))
        return '\n'.join(msg)


def addRideOfferNew(driver, start_datetime, percorso,
                 time_mode, programmato, giorni):
    import date_time_util as dtu
    o = RideOfferNew(
        driver_id = driver.getId(),
        driver_name_lastname = driver.getFirstNameLastName(),
        driver_username=driver.getUsername(),
        start_datetime=start_datetime,
        percorso=percorso,
        registration_datetime = dtu.removeTimezone(dtu.nowCET()),
        time_mode = time_mode,
        programmato = programmato,
        programmato_giorni = giorni
    )
    o.put()
    return o

def filterAndSortOffersAbitualiAndPerDay(offers):
    import params
    import date_time_util as dtu
    from datetime import timedelta

    result_abituali = []
    result_per_day = [[],[],[],[],[],[],[]]
    today = dtu.getWeekday()
    now_dt = dtu.removeTimezone(dtu.nowCET()) - timedelta(minutes=params.TIME_TOLERANCE_MIN)
    now_time = now_dt.time()
    for o in offers:
        if o.start_datetime is None: # abituali
            result_abituali.append(o)
        elif o.programmato:
            for g in o.programmato_giorni:
                # exclude those of today which have already happened
                if g != today or o.start_datetime.time() > now_time: #o.programmato_time > now_time:
                    result_per_day[g].append(o)
        elif o.start_datetime > now_dt:
            g = dtu.getWeekday(o.start_datetime)
            result_per_day[g].append(o)
    for results_days in result_per_day:
        results_days.sort(key=lambda x: x.getDepartingTimeStr())
    return result_abituali, result_per_day

def getActiveRideOfferNewsQry():
    import params
    import date_time_util as dtu
    from datetime import timedelta
    qry = RideOfferNew.query(
        ndb.AND(
            RideOfferNew.active == True,
            ndb.OR(
                RideOfferNew.programmato == True,
                RideOfferNew.start_datetime >= dtu.removeTimezone(dtu.nowCET()) - timedelta(
                    minutes=params.TIME_TOLERANCE_MIN)
            )
        )
    )
    return qry


def getActiveRideOfferNewsCountInWeek():
    offers = getActiveRideOfferNewsQry().fetch()
    offers_abituali, offers_list_per_day = filterAndSortOffersAbitualiAndPerDay(offers)
    count = len(offers_abituali) + sum([len(d) for d in offers_list_per_day])
    return count

def getRideOfferNewInsertedLastDaysQry(days):
    import date_time_util as dtu
    from datetime import timedelta
    return RideOfferNew.query(
        RideOfferNew.start_datetime >= dtu.removeTimezone(dtu.nowCET()) - timedelta(days=days)
    )


def getActiveRideOfferNewsDriver(driver_id):
    import params
    import date_time_util as dtu
    from datetime import timedelta
    now_with_tolerance = dtu.removeTimezone(dtu.nowCET()) - timedelta(minutes=params.TIME_TOLERANCE_MIN)
    qry = RideOfferNew.query(
        ndb.AND(
            RideOfferNew.active == True,
            RideOfferNew.driver_id == driver_id,
            ndb.OR(
                RideOfferNew.programmato == True,
                RideOfferNew.start_datetime >= now_with_tolerance
            )
        )
    ).order(RideOfferNew.start_datetime)
    return qry.fetch()

def getActiveRideOfferNewsSortedAbitualiAndPerDay(percorso_passeggero):
    import route
    import params
    import date_time_util as dtu
    from datetime import timedelta

    nowWithTolerance = dtu.removeTimezone(dtu.nowCET()) - timedelta(minutes=params.TIME_TOLERANCE_MIN)

    percorsi_compatibili = route.getPercorsiCompatibili(percorso_passeggero)

    if percorsi_compatibili:
        qry_rides = RideOfferNew.query(
            ndb.AND(
                RideOfferNew.percorso.IN(percorsi_compatibili),
                RideOfferNew.active == True,
                ndb.OR(
                    RideOfferNew.programmato == True,
                    RideOfferNew.start_datetime >= nowWithTolerance
                )
            )
        )
        offers = qry_rides.fetch()
    else:
        offers = []
    return filterAndSortOffersAbitualiAndPerDay(offers) #abituali, perDay


# also expired ones
def getDriversIdQryWithCompatibleRideOfferNews(percorso_passeggero):
    import route
    percorsi_compatibili = route.getPercorsiCompatibili(percorso_passeggero)
    if percorsi_compatibili:
        qry_rides = RideOfferNew.query(
            RideOfferNew.percorso.IN(percorsi_compatibili),
            #projection=[RideOfferNew.driver_username], distinct=True
            projection=[RideOfferNew.driver_id], #distinct=True
        )
        return qry_rides
        #usernames = ['@{}'.format(r.driver_username) for r in qry_rides.fetch()]
        #return set(usernames)
    #else:
    #    return []


def getActiveRideOfferNews():
    import params
    import date_time_util as dtu
    from datetime import timedelta

    qry = RideOfferNew.query(
        ndb.AND(
            RideOfferNew.active == True,
            ndb.OR(
                RideOfferNew.programmato == True,
                RideOfferNew.start_datetime >= dtu.removeTimezone(dtu.nowCET()) - timedelta(minutes=params.TIME_TOLERANCE_MIN)
                # might be redundant as the filter is also applied afterwards
            )
        )
    )
    offers = qry.fetch()
    return offers

