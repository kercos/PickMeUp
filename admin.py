# -*- coding: utf-8 -*-

from google.appengine.ext import ndb

from person import Person
from ride_offer import RideOffer
from route import Route
from fermata import Fermata
from utility import convertToUtfIfNeeded

def resetAllEntities(test = False):
    for x in [RideOffer, Route]: #Person, Feramta
        more, cursor = True, None
        total = 0
        while more:
            records, cursor, more = x.query().fetch_page(1000, keys_only=True, start_cursor=cursor)
            total += len(records)
            if records:
                create_futures = ndb.delete_multi_async(records)
                ndb.Future.wait_all(create_futures)
        print("Cleaned {} from {}".format(total, x.__name__))

'''
After fermate have been updated (change in name or deletion)
set fermate as inactive if no longer present in kml file
and add new fermate as active
should be run followed by:
- updatePercorsiInRideOffers()
- updatePercorsiPreferiti()
'''
def updateFermate():
    from routing_util import FERMATE

    # Update old active fermate as inactive
    fermate_keys = FERMATE.keys()
    updated_count = 0
    more, cursor = True, None
    while more:
        records, cursor, more = Fermata.query(Fermata.active == True).fetch_page(100, start_cursor=cursor)
        updated_records = []
        for f in records:
            f.active = False
            if f.key.id() not in fermate_keys:
                updated_records.append(f)
        create_futures = ndb.put_multi_async(updated_records)
        ndb.Future.wait_all(create_futures)
        updated_count += len(updated_records)
    print 'Set {} fermate as inactive'.format(updated_count)

    # Adding new fermate
    # FERMATE {zona_stop: {'zona': refZona, 'stop': <fermata_name>, 'loc': (<lat>,<lon>)}}
    new_entries = []
    for f_key, f_info in FERMATE.items():
        f_entry = Fermata(id=f_key, location=ndb.GeoPt(*f_info['loc']), active=True)
        f_entry.update_location()
        new_entries.append(f_entry)
    create_futures = ndb.put_multi_async(new_entries)
    ndb.Future.wait_all(create_futures)
    print 'Added {} new fermate'.format(len(create_futures))

'''
After fermate have been updated (change in name or deletion)
'''
def updatePercorsiInRideOffers(test = False):
    import route
    more, cursor = True, None
    while more:
        # not clear if we have to restrict to active RideOffer only
        records, cursor, more = RideOffer.query().fetch_page(100, start_cursor=cursor)
        updating_records = []
        for r in records:
            old_percorso = convertToUtfIfNeeded(r.percorso)
            new_percorso = getNewPercorso(old_percorso)
            if new_percorso is None:
                # triggering a warning in getNewPercorso
                print 'aborting'
                return
            if old_percorso!=new_percorso:
                print 'updating percorso from {} to {}'.format(old_percorso, new_percorso)
                r.percorso = new_percorso
                updating_records.append(r)
                if Route.get_by_id(new_percorso) is None:
                    rt = route.addRoute(new_percorso)
                    rt.populateWithDetails(put = not test)
                    print 'populating new route: {}'.format(new_percorso)
        if not test:
            create_futures = ndb.put_multi_async(updating_records)
            ndb.Future.wait_all(create_futures)

'''
After fermate have been updated (change in name or deletion)
'''
def updatePercorsiPreferiti(test = False):
    more, cursor = True, None
    while more:
        records, cursor, more = Person.query(Person.percorsi_size > 0).fetch_page(100, start_cursor=cursor)
        updating_records = []
        for r in records:
            new_percorsi = []
            updated = False
            for old_percorso in r.percorsi:
                old_percorso = convertToUtfIfNeeded(old_percorso)
                new_percorso = getNewPercorso(old_percorso)
                if new_percorso is None:
                    # triggering a warning in getNewPercorso
                    print 'aborting'
                    return
                if old_percorso != new_percorso:
                    updated = True
                    print 'updating percorso from {} to {}'.format(old_percorso, new_percorso)
                    new_percorsi.append(new_percorso)
                else:
                    new_percorsi.append(old_percorso)
            if updated:
                r.percorsi = new_percorsi
                updating_records.append(r)
        if not test:
            create_futures = ndb.put_multi_async(updating_records)
            ndb.Future.wait_all(create_futures)

'''
Aux function to get new percorso from an old one (after fermate have been updated)
'''
def getNewPercorso(percorso):
    import routing_util
    import fermata
    start_fermata_key, end_fermata_key = routing_util.decodePercorso(percorso)
    start_fermata = Fermata.get_by_id(start_fermata_key)
    end_fermata = Fermata.get_by_id(end_fermata_key)
    assert start_fermata is not None
    assert end_fermata is not None
    new_start_fermata, new_end_fermata = [
        fermata.getClosestActiveFermata(
            f.location.lat, f.location.lon, radius=5)
        for f in (start_fermata, end_fermata)
    ]
    if any([new_f is None for new_f in (new_start_fermata, new_end_fermata)]):
        if new_start_fermata is None:
            print 'warning: no new fermata found for {}'.format(start_fermata_key)
        if new_end_fermata is None:
            print 'warning: no new fermata found for {}'.format(end_fermata_key)
        return

    new_percorso = routing_util.encodePercorso(
        new_start_fermata.getFermataKey(),
        new_end_fermata.getFermataKey()
    )
    return new_percorso


'''
Needed to make sure that active RideOffer have their couterpart in Route
Should not be necessary (only if RideOffer are out of synch with Route)
'''
def updateRideOffers():
    prop_to_delete = ['routes_info', 'fermate_intermedie', 'percorsi_passeggeri_compatibili']
    more, cursor = True, None
    updated_records = []
    percorsi = set()
    while more:
        records, cursor, more = RideOffer.query(RideOffer.active==True).fetch_page(100, start_cursor=cursor)
        for ent in records:
            changed = False
            for prop in prop_to_delete:
                if prop in ent._properties:
                    del ent._properties[prop]
                    changed = True
            if changed:
                updated_records.append(ent)
            percorsi.add(ent.percorso)
    if updated_records:
        print 'Updating {} records'.format(len(updated_records))
        create_futures = ndb.put_multi_async(updated_records)
        ndb.Future.wait_all(create_futures)
    if percorsi:
        import route
        print 'Updating {} percorsi'.format(len(percorsi))
        routes = []
        for n, percorso in enumerate(percorsi,1):
            print '{}) {}'.format(n, percorso.encode('utf-8'))
            r = route.addRoute(percorso)
            r.populateWithDetails(put=False)
            routes.append(r)
        create_futures = ndb.put_multi_async(routes)
        ndb.Future.wait_all(create_futures)