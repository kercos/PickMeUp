# -*- coding: utf-8 -*-

from google.appengine.ext import ndb
from utility import convertToUtfIfNeeded

class Route(ndb.Model):
    #percorso = ndb.StringProperty() # id

    percorso_info = ndb.PickleProperty()
    # list of route info:
    # for each route ->
    # {route_intermediates_fermate: <list>,
    # route_duration: <num> (seconds),
    # route_distance: <num> (meters)}

    fermate_intermedie = ndb.StringProperty(repeated=True) # set of fermate intermedie
    percorsi_passeggeri_compatibili = ndb.StringProperty(repeated=True) # set of percorsi compatibili

    average_distance = ndb.ComputedProperty(lambda self: self.getAverageDistance())

    average_duration = ndb.ComputedProperty(lambda self: self.getAverageDuration())

    def getPercorso(self):
        return self.key.id()

    def hasDetails(self):
        return self.percorso_info is not None

    def getPercorsiPasseggeriCompatibili(self):
        return [convertToUtfIfNeeded(x) for x in self.percorsi_passeggeri_compatibili]

    def getNumberPercorsiPasseggeriCompatibili(self):
        return len(self.percorsi_passeggeri_compatibili)

    def getFermateIntermedie(self):
        return [convertToUtfIfNeeded(x) for x in self.fermate_intermedie]

    def getAverageDistance(self):
        from utility import format_distance
        assert self.percorso_info
        distances = [r_info['route_distance'] for r_info in self.percorso_info]
        avg_km = sum(distances) / float(len(distances)) / 1000
        return format_distance(avg_km)

    def getAverageDuration(self):
        import date_time_util as dtu
        assert self.percorso_info
        durations = [r_info['route_duration'] for r_info in self.percorso_info]
        avg = sum(durations) / float(len(durations))
        return dtu.convertSecondsInHourMinString(avg)

    def getFermateIntermedieRoutes(self):
        assert self.percorso_info
        return [r_info['route_intermediates_fermate'] for r_info in self.percorso_info]

    def populateWithDetails(self, put=True):
        import routing_util
        import itertools
        self.percorso_info = routing_util.getRoutingDetails(self.getPercorso())
        # a list of route info: for each route -> {route_intermediates_fermate, route_duration, route_distance}
        fermate_intermedie_set = set()
        percorsi_compatibili_set = set()
        if self.percorso_info:
            for r_info in self.percorso_info:
                fermate = r_info['route_intermediates_fermate']
                fermate_intermedie_set.update(fermate)
                fermate_pairs = tuple(itertools.combinations(fermate, 2))
                for pair in fermate_pairs:
                    percorso = routing_util.encodePercorso(*pair)
                    percorsi_compatibili_set.add(percorso)

        self.fermate_intermedie = list(fermate_intermedie_set)
        self.percorsi_passeggeri_compatibili = list(percorsi_compatibili_set)
        if put:
            self.put()

    def getDetails(self):
        from utility import format_distance
        import date_time_util as dtu
        msg = []
        msg.append('{} tragitto/i trovati per viaggio\n*{}*:\n'.
                   format(len(self.percorso_info), self.getPercorso()))
        for n, r_info in enumerate(self.percorso_info, 1):
            msg.append('*{}.*'.format(n))
            distance = format_distance(float(r_info['route_distance']) / 1000)
            duration = dtu.convertSecondsInHourMinString(r_info['route_duration'])
            fermate_intermedie_str = ', '.join(r_info['route_intermediates_fermate'])
            msg.append('   ∙ Fermate intermedie: {}'.format(fermate_intermedie_str))
            msg.append('   ∙ Distanza: {}'.format(distance))
            msg.append('   ∙ Durata: {}'.format(duration))
        num_percorsi_compatibili = len(self.getPercorsiPasseggeriCompatibili())
        msg.append('\n{} percorso/i passeggeri compatibilie.'.format(num_percorsi_compatibili))
        #percorsi_compatibili_str = ', '.join(self.getPercorsiPasseggeriCompatibili())
        #msg.append('\n{} percorso/i passeggeri compatibilie: {}'.format(
        #    num_percorsi_compatibili, percorsi_compatibili_str))
        return '\n'.join(msg)

def addRoute(percorso):
    r = Route(
        id=percorso,
    )
    #r.put() always after populatePercorsoWithDetails
    return r

def getRouteAddIfNotPresent(percorso):
    r = Route.get_by_id(percorso)
    if r is None:
        r = Route(
            id=percorso,
        )
        #r.put() always after populatePercorsoWithDetails
    return r

def getPercorsiCompatibili(percorso_passeggero):
    qry_routes = Route.query(
        Route.percorsi_passeggeri_compatibili == percorso_passeggero
    )
    percorsi_compatibili = [r.getPercorso() for r in qry_routes.fetch()]
    return percorsi_compatibili

def populateRoutesWithDetails():
    more, cursor = True, None
    while more:
        records, cursor, more = Route.query().fetch_page(100, start_cursor=cursor)
        print 'Updating {} records'.format(len(records))
        for n, ent in enumerate(records, 1):
            print '{}) {}'.format(n, ent.getPercorso().encode('utf-8'))
            ent.populateWithDetails(put=False)
        create_futures = ndb.put_multi_async(records)
        ndb.Future.wait_all(create_futures)
