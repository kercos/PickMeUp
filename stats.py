# -*- coding: utf-8 -*-

import utility
from person import Person
from ride_offer import RideOffer

def getAnagraficaTable():
    header = [
        "Nome", "Cognome", "Username",
        "Id", "Applicazione",
        "Enabled", "Modalità Notifica",
        "Numero Percorsi Preferiti"
    ]
    result = [header]
    more, cursor = True, None
    while more:
        # not clear if we have to restrict to active RideOffer only
        people, cursor, more = Person.query().order(Person.last_name).fetch_page(1000, start_cursor=cursor)
        for p in people:
            p_details = [
                p.getFirstName(), p.getLastName(), p.getUsername(escapeMarkdown=False),
                p.chat_id, p.application,
                p.enabled, p.getNotificationMode(),
                p.percorsi_size
            ]
            p_details = [utility.emptyStringIfNone(x) for x in p_details]
            result.append(p_details)
    return result

def getOffertePassaggi():
    import date_time_util as dtu
    header = [
        "driver_name_lastname", "driver_username", "driver_id",
        "percorso", "registration_datetime",
        "active", "start_datetime",
        "disactivation_datetime", "time_mode",
        "programmato", "programmato_giorni"
    ]
    result = [header]
    more, cursor = True, None
    while more:
        # not clear if we have to restrict to active RideOffer only
        offerte, cursor, more = RideOffer.query().fetch_page(1000, start_cursor=cursor)
        for o in offerte:
            o_details = [
                o.getDriverName(), o.driver_username, o.driver_id,
                o.getPercorso(), dtu.formatDateTime(o.registration_datetime),
                o.active, dtu.formatDateTime(o.start_datetime),
                dtu.formatDateTime(o.disactivation_datetime), o.getTimeMode(),
                o.programmato, o.getProgrammato_giorni_str()
            ]
            o_details = [utility.emptyStringIfNone(x) for x in o_details]
            result.append(o_details)
    return result

COMMAND_FUNCTIONS = {
    '/anagrafica': getAnagraficaTable,
    '/offerte_passaggi': getOffertePassaggi
}

def getStats(inputCommand):
    if inputCommand in COMMAND_FUNCTIONS.keys():
        return COMMAND_FUNCTIONS[inputCommand]()
    else:
        return None
