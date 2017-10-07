# coding=utf-8

import requests
import xml.etree.ElementTree as ET

ZONE_LAYER_NAME = 'Luoghi'
FARMATE_LAYER_NAME = 'Fermate'

tagPrefix = '{http://www.opengis.net/kml/2.2}'
docTag = tagPrefix + 'Document'
folderTag = tagPrefix + 'Folder'
nameTag = tagPrefix + 'name'
placemarkTag = tagPrefix + 'Placemark'
pointTag = tagPrefix + 'Point'
coordinatesTag = tagPrefix + 'coordinates'
polygonTag = tagPrefix + 'Polygon'
outerBoundaryIsTag = tagPrefix + 'outerBoundaryIs'
linearRingTag = tagPrefix + 'LinearRing'
lineStringTag = tagPrefix + 'LineString'

def mean(numbers):
    return float(sum(numbers)) / max(len(numbers), 1)

def getPolygonCentroid(poly):
    return mean([x[0] for x in poly]),mean([x[1] for x in poly])

def getZonaConainingPoint(point, zone):
    from geoUtils import point_inside_polygon
    for n, v in zone.iteritems():
        polycoordinateList = v['polygon']
        if point_inside_polygon(point[0], point[1], polycoordinateList):
            return n
    return None

# needs to be duplicated from routing_util to prevent cycle imports from parseMap()
def encodeFermataKey(zona, fermata):
    return '{} ({})'.format(zona, fermata)

def parseMap():
    import key
    r = requests.get(key.map_url)
    kml_xml = r.content
    root = ET.fromstring(kml_xml)
    #root = ET.parse('data/PickMeUp.kml') #getroot()
    document = root.find(docTag)
    folders = document.findall(folderTag)
    nameFolders = {}
    for fold in folders:
        name = fold.find(nameTag).text  # Fermate, ZoneFlags, Zone, Lines
        nameFolders[name] = fold

    # ZONE
    # IMPORTANT - ZONE CANNOT SHARE THE SAME PREFIX
    zone = {}  # {zona: {'loc': (<lat>,<lon>), 'stops': [stop1, stop2, ...]}, 'polygon': <list polygon coords>}
    zone_folder = nameFolders[ZONE_LAYER_NAME]
    placemarks = zone_folder.findall(placemarkTag)
    for p in placemarks:
        name = p.find(nameTag).text.strip() # zona name
        name = name.encode('utf-8')
        polygon = p.find(polygonTag)
        outerBoundaryIs = polygon.find(outerBoundaryIsTag)
        linearRing = outerBoundaryIs.find(linearRingTag)
        coordinatesStringList = [x.strip() for x in linearRing.find(coordinatesTag).text.strip().split('\n')]
        coordinateList = []
        for coordinatesString in coordinatesStringList:
            lon, lat = [float(x) for x in coordinatesString.split(',')[:2]]
            coordinateList.append((lat, lon))
        centroid_lat, centroid_lon = getPolygonCentroid(coordinateList)
        zone[name] = {
            'loc': (centroid_lat, centroid_lon), # centroid
            'polygon': coordinateList,
            'stops': []
        }

    # FERMATE
    fermate = {} # {zona_stop: {'zona': refZona, 'stop': <fermata_name>, 'loc': (<lat>,<lon>)}}
    fermate_folder = nameFolders[FARMATE_LAYER_NAME]
    placemarks = fermate_folder.findall(placemarkTag)
    for p in placemarks:
        stop = p.find(nameTag).text.strip() # fermata name
        stop = stop.encode('utf-8')
        point = p.find(pointTag)
        coordinatesString = point.find(coordinatesTag).text.strip().split(',')
        lon, lat = [float(x) for x in coordinatesString[:2]]
        #point = Point(lat, lon)
        zona = getZonaConainingPoint((lat, lon), zone)
        if zona is None:
            print "Fermata {} has no Zona".format(stop)
        zona_stop = encodeFermataKey(zona, stop)
        fermate[zona_stop] = {'zona': zona, 'stop': stop, 'loc': (lat, lon)}
        zone[zona]['stops'].append(stop)

    return zone, fermate

def checkMap():
    zone, fermate = parseMap()
    checkZone = all(len(v['stops'])>0 for v in zone.values())
    checkFermate = all(fv['zona'] is not None for fv in fermate.values())
    print "Zone: {} check: {}".format(len(zone), checkZone)
    if not checkZone:
        print "Error zones: {}".format([z for z in zone.keys() if len(zone[z]['stops'])==0])
    print "Fermate: {} check: {}".format(len(fermate), checkFermate)
    if not checkFermate:
        print "Error fermate: {}".format([f for f in fermate.keys() if fermate[f]['zona'] is None])
