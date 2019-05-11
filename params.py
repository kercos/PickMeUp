# -*- coding: utf-8 -*-

GIORNI_SETTIMANA = ['LU', 'MA', 'ME', 'GI', 'VE', 'SA', 'DO']
GIORNI_SETTIMANA_FULL = ['lunedì', 'martedì', 'mercoledì', 'giovedì', 'venerdì', 'sabato', 'domenica']

TIME_TOLERANCE_MIN = 5 # show also rides scheduled 5 min ago
MAX_FERMATE_NEAR_LOCATION = 5
MAX_PERCORSI = 8
PATH_FERMATA_PROXIMITY_THRESHOLD = 1.0

DAY_START_HOUR = 6
MIN_TO_SWITCH_TO_NEXT_HOUR = 52 # if it's 13.52 don't show 13

NOTIFICATION_MODE_NONE = "NONE"
NOTIFICATION_MODE_ALL = "ALL"
NOTIFICATION_MODE_PERCORSI = "PERCORSI"
DEFAULT_NOTIFICATIONS_MODE = NOTIFICATION_MODE_ALL

NOTIFICATIONS_MODES = [NOTIFICATION_MODE_ALL, NOTIFICATION_MODE_PERCORSI, NOTIFICATION_MODE_NONE]
# should follow same order as in main.NOTIFICHE_BUTTONS

PERCORSO_COMMAND_PREFIX = '/percorso_'

COST_PER_0_KM = 1.0
COST_PER_10_KM = 1.5

def compute_cost(distance):
    return COST_PER_0_KM + (COST_PER_10_KM-COST_PER_0_KM)/10*distance

def getCommand(prefix, suffix, escapeMarkdown=True):
    import utility
    result = "{}{}".format(prefix, suffix)
    if escapeMarkdown:
        return utility.escapeMarkdown(result)
    return result

def getIndexFromCommand(command, prefix):
    import utility
    index = command[len(prefix):]
    if utility.representsInt(index):
        return int(index)
    return None
