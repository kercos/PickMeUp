# coding=utf-8

from key import GOOGLE_API_KEY

'''
--------------------------------
TERMINOLOGY
--------------------------------
- fermata : zona + stop encoded as 'zona (stop)'
- percorso: start_fermata + end_fermata encoded as 'start_zona (start_stop) → end_zona (end_stop)'
###############################
'''

# ZONE -> {zona: {'loc': (<lat>,<lon>), 'stops': [stop1, stop2, ...]}, 'polygon': <list polygon coords>}
# FERMATE -> {zona_stop: {'zona': refZona, 'stop': <fermata_name>, 'loc': (<lat>,<lon>)}}

import parseKml

# ZONE: {zona: {'loc': (<lat>,<lon>), 'stops': [stop1, stop2, ...]}, 'polygon': <list polygon coords>}
# FERMATE {zona_stop: {'zona': refZona, 'stop': <fermata_name>, 'loc': (<lat>,<lon>)}}

ZONE, FERMATE = parseKml.parseMap()
STOPS = [v['stop'] for v in FERMATE.values()]
#GPS_FERMATE_LOC = [v['loc'] for v in FERMATE.values()]

#SORTED_ZONE_ITEMS = sorted(ZONE.items(), key=lambda i: i) #alphabetically
SORTED_ZONE_ITEMS = sorted(ZONE.items(), key=lambda i: int(i[1]['order'])) #manual order

SORTED_STOPS_IN_ZONA = lambda z: sorted([x for x in ZONE[z]['stops']])

SORTED_ZONE_WITH_STOP_IF_SINGLE = [
    z if len(v['stops']) > 1 else '{} ({})'.format(z, v['stops'][0])
    for z, v in SORTED_ZONE_ITEMS
]

PERCORSO_SEPARATOR = ' → '

def getFermataKeyFromStop(stop):
    fermata = [k for k,v in FERMATE.items() if v['stop']==stop]
    assert len(fermata)==1
    return fermata[0]

def encodeFermataKey(zona, stop):
    return '{} ({})'.format(zona, stop)

def decodeFermataKey(fermata_key, do_assert=True):
    assert fermata_key.count('(')==1
    zona, stop = fermata_key[:-1].split(' (')
    if zona in ZONE and stop in SORTED_STOPS_IN_ZONA(zona):
        return zona, stop
    return None, None

def encodeFermateKeysFromQuartet(start_zona, start_stop, end_zona, end_stop):
    start_fermata_key = encodeFermataKey(start_zona, start_stop)
    end_fermata_key = encodeFermataKey(end_zona, end_stop)
    return start_fermata_key, end_fermata_key

def encodePercorsoFromQuartet(start_zona, start_fermata, end_zona, end_fermata):
    start_fermata_key, end_fermata_key = encodeFermateKeysFromQuartet(
        start_zona, start_fermata, end_zona, end_fermata)
    return encodePercorso(start_fermata_key, end_fermata_key)

def encodePercorsoShortFromQuartet(start_zona, start_fermata, end_zona, end_fermata):
    return '{}{}{}'.format(start_fermata, PERCORSO_SEPARATOR, end_fermata)

def encodePercorsoShortFromPercorsoKey(percorso_key):
    start_zona, start_stop, end_zone, end_stop = decodePercorsoToQuartet(percorso_key)
    return encodePercorsoShortFromQuartet(start_zona, start_stop, end_zone, end_stop)

def decodePercorsoToQuartet(percorso_key):
    start_fermata_key, end_fermata_key = decodePercorso(percorso_key)
    start_zona, start_stop = decodeFermataKey(start_fermata_key)
    end_zone, end_stop = decodeFermataKey(end_fermata_key)
    return start_zona, start_stop, end_zone, end_stop

def encodePercorso(start_fermata_key, end_fermata_key):
    assert start_fermata_key in FERMATE
    assert end_fermata_key in FERMATE
    #if start_fermata_key not in FERMATE:
    #    print '{} not in FERMATE'.format(start_fermata_key)
    #if end_fermata_key not in FERMATE:
    #    print '{} not in FERMATE'.format(end_fermata_key)
    return '{}{}{}'.format(start_fermata_key, PERCORSO_SEPARATOR, end_fermata_key)

def decodePercorso(percorso_key):
    start_fermata_key, end_fermata_key = percorso_key.split(PERCORSO_SEPARATOR)
    return start_fermata_key, end_fermata_key

def getReversePath(start, start_fermata, end, end_fermata):
    return end, end_fermata, start, start_fermata

MAX_THRESHOLD_RATIO = 2

def getFermateNearPosition(lat, lon, radius):
    import geoUtils
    import params
    nearby_fermate_dict = {}
    centralPoint = (lat, lon)
    min_distance = None
    for f,v in FERMATE.iteritems():
        refPoint = v['loc']
        d = geoUtils.distance(refPoint, centralPoint)
        if d < radius:
            if min_distance is None or d < min_distance:
                min_distance = d
            nearby_fermate_dict[f] = {
                'loc': refPoint,
                'dist': d
            }
    min_distance = max(min_distance, 1) # if it's less than 1 km use 1 km as a min distance
    nearby_fermate_dict = {k:v for k,v in nearby_fermate_dict.items() if v['dist'] <= MAX_THRESHOLD_RATIO*min_distance}
    max_results = params.MAX_FERMATE_NEAR_LOCATION
    nearby_fermated_sorted_dict = sorted(nearby_fermate_dict.items(), key=lambda k: k[1]['dist'])[:max_results]
    return nearby_fermated_sorted_dict

BASE_MAP_IMG_URL = "http://maps.googleapis.com/maps/api/staticmap?" + \
                   "&size=400x400" + "&maptype=roadmap" + \
                   "&key=" + GOOGLE_API_KEY

def getFermateNearPositionImgUrl(lat, lon, radius = 10):
    from utility import format_distance
    nearby_fermated_sorted_dict = getFermateNearPosition(lat, lon, radius)
    if nearby_fermated_sorted_dict:
        fermate_number = len(nearby_fermated_sorted_dict)
        img_url = BASE_MAP_IMG_URL + \
                  "&markers=color:red|{},{}".format(lat, lon) + \
                  ''.join(["&markers=color:blue|label:{}|{},{}".format(num, v['loc'][0], v['loc'][1])
                           for num, (f,v) in enumerate(nearby_fermated_sorted_dict, 1)])
        text = 'Ho trovato *1 fermata* ' if fermate_number==1 else 'Ho trovato *{} fermate* '.format(fermate_number)
        text += "in prossimità dalla posizione inserita:\n"
        text += '\n'.join('{}. {}: {}'.format(num, f, format_distance(v['dist']))
                          for num, (f,v) in enumerate(nearby_fermated_sorted_dict,1))
    else:
        img_url = None
        text = 'Nessuna fermata trovata nel raggio di {} km dalla posizione inserita.'.format(radius)
    return img_url, text

def getIntermediateFermateOrderFromPath(path):
    import geoUtils
    import params
    intermediates = []
    for point in path:
        for f, v in FERMATE.items():
            if f in intermediates:
                continue
            loc = v['loc']
            dst = geoUtils.distance(point, loc)
            if dst < params.PATH_FERMATA_PROXIMITY_THRESHOLD:
                intermediates.append(f)
                break
    return intermediates

def getRoutingDetails(percorso):
    from key import GOOGLE_API_KEY
    import polyline
    import requests
    start_fermata_key, end_fermata_key = decodePercorso(percorso)
    origin_str = ','.join(str(x) for x in FERMATE[start_fermata_key]['loc'])
    destin_str = ','.join(str(x) for x in FERMATE[end_fermata_key]['loc'])
    api_url = 'https://maps.googleapis.com/maps/api/directions/json?' \
              'alternatives=true&units=metric&key={}'.format(GOOGLE_API_KEY)  # avoid=tolls,highways
    api_url += '&origin={}&destination={}'.format(origin_str, destin_str)
    response_dict = requests.get(api_url).json()
    #print str(response_dict)
    routes = response_dict['routes']
    routes_info = []
    for r in routes:
        poly_str = r['overview_polyline']['points']
        legs  = r['legs']
        #print 'duration:{} distance:{}'.format(r_duration, r_distance)
        path = polyline.decode(poly_str)
        routes_info.append({
            'route_intermediates_fermate': getIntermediateFermateOrderFromPath(path),
            'route_duration': sum(l['duration']['value'] for l in legs),
            'route_distance': sum(l['distance']['value'] for l in legs)
        })
    return routes_info
    # a list of route infor: for each route -> {route_intermediates_fermate, route_duration, route_distance}

def test_intermediate_stops(start=None, end=None):
    import random

    if start is None:
        start = random.choice(FERMATE.keys())
    while end is None or end == start:
        end = random.choice(FERMATE.keys())

    print('{} --> {}'.format(start, end))
    print('{} --> {}'.format(FERMATE[start]['loc'],FERMATE[end]['loc']))
    route_info = getRoutingDetails(encodePercorso(start, end))
    # a list of route infor: for each route -> {route_intermediates_fermate, route_duration, route_distance}

    print('Found {} routes.'.format(len(route_info)))

    for i, r_info in enumerate(route_info):
        fermate_str = ', '.join(r_info['route_intermediates_fermate'])
        distanza = r_info['route_distance']
        durata = r_info['route_duration']
        print 'Percorso {}\n' \
              ' - Fermate intermedie: {}\n' \
              ' - Distanza: {} m\n' \
              ' - Durata: {} s'.format(i+1, fermate_str, distanza, durata)


