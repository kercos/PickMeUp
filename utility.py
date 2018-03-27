# -*- coding: utf-8 -*-
import re
import logging
import string
import textwrap
from collections import OrderedDict

def representsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def representsFloat(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

re_digits = re.compile('^\d+$')

def hasOnlyDigits(s):
    return re_digits.match(s) != None

def representsIntBetween(s, low, high):
    if not representsInt(s):
        return False
    sInt = int(s)
    if sInt>=low and sInt<=high:
        return True
    return False

def representsFloatBetween(s, low, high):
    if not representsFloat(s):
        return False
    sFloat = float(s)
    if sFloat>=low and sFloat<=high:
        return True
    return False

def numberEnumeration(list):
    return [(str(x[0]), x[1]) for x in enumerate(list, 1)]

def letterEnumeration(list):
    return [(chr(x[0] + 65), x[1]) for x in enumerate(list, 0)]  #chd(65) = 'A'

def getIndexIfIntOrLetterInRange(input, max):
    if representsInt(input):
        result = int(input)
        if result in range(1, max + 1):
            return result
    if input in list(map(chr, range(65, 65 + max))):
        return ord(input) - 64  # ord('A') = 65
    return None

def makeArray2D(data_list, length=2):
    return [data_list[i:i+length] for i in range(0, len(data_list), length)]

def distributeElementMaxSize(seq, maxSize=5):
    if len(seq)==0:
        return []
    lines = len(seq) / maxSize
    if len(seq) % maxSize > 0:
        lines += 1
    avg = len(seq) / float(lines)
    out = []
    last = 0.0
    while last < len(seq):
        out.append(seq[int(last):int(last + avg)])
        last += avg
    return out


def segmentArrayOnMaxChars(array, maxChar=20, ignoreString=None):
    #logging.debug('selected_tokens: ' + str(selected_tokens))
    result = []
    lineCharCount = 0
    currentLine = []
    for t in array:
        t_strip = t.replace(ignoreString, '') if ignoreString and ignoreString in t else t
        t_strip_size = len(t_strip.decode('utf-8'))
        newLineCharCount = lineCharCount + t_strip_size
        if not currentLine:
            currentLine.append(t)
            lineCharCount = newLineCharCount
        elif newLineCharCount > maxChar:
            #logging.debug('Line ' + str(len(result)+1) + " " + str(currentLine) + " tot char: " + str(lineCharCount))
            result.append(currentLine)
            currentLine = [t]
            lineCharCount = t_strip_size
        else:
            lineCharCount = newLineCharCount
            currentLine.append(t)
    if currentLine:
        #logging.debug('Line ' + str(len(result) + 1) + " " + str(currentLine) + " tot char: " + str(lineCharCount))
        result.append(currentLine)
    return result

reSplitSpace = re.compile("\s")

def splitTextOnSpaces(text):
    return reSplitSpace.split(text)

def escapeMarkdown(text):
    for char in '*_`[':
        text = text.replace(char, '\\'+char)
    return text

def containsMarkdown(text):
    for char in '*_`[':
        if char in text:
            return True
    return False

# minutes should be positive
def getHourMinFromMin(minutes):
    hh = int(minutes / 60)
    mm = minutes % 60
    return hh, mm


def getSiNoFromBoolean(bool_value):
    return 'SI' if bool_value else 'NO'

def getTimeStringFormatHHMM(minutes, rjust=False):
    hh, mm = getHourMinFromMin(abs(minutes))
    #return "{}h {}min".format(str(hh).zfill(2), str(mm).zfill(2))
    sign = '-' if minutes<0 else ''
    signHH = sign+str(hh)
    if rjust:
        signHH = signHH.rjust(3)
    return "{}:{}".format(signHH, str(mm).zfill(2))

def unindent(s):
    return re.sub('[ ]+', ' ', textwrap.dedent(s))

# sheet_tables is a dict mapping sheet names to 2array
def convert_data_to_spreadsheet(sheet_tables):
    import StringIO
    from pyexcel_xls import save_data
    xls_data = OrderedDict()
    for name, array in sheet_tables.iteritems():
        xls_data.update({name: array})
        #xls_data.update({"Sheet 1": sheet_tables})
    output = StringIO.StringIO()
    save_data(output, xls_data, encoding="UTF-8")
    return output.getvalue()

def convert_arrayData_to_tsv(array):
    import csv
    import StringIO
    output = StringIO.StringIO()
    writer = csv.writer(output, dialect='excel-tab')
    writer.writerows(array)
    return output.getvalue()

def roundup(x, upTo):
    import math
    return int(math.ceil(x / float(upTo))) * upTo

def emptyStringIfNone(x):
    return '' if x==None else x

def emptyStringIfZero(x):
    return '' if x==0 else x

def convertToUtfIfNeeded(s):
    if isinstance(s, unicode):
        s = s.encode('utf-8')
    return s

def flatten(L):
    ret = []
    for i in L:
        if isinstance(i,list):
            ret.extend(flatten(i))
        else:
            ret.append(i)
    return ret

def matchInputToChoices(input, choices):
    perfectMatch = True
    if input in choices:
        return input, perfectMatch
    perfectMatch = False
    from fuzzywuzzy import process
    threshold = 75
    # choices = ["Atlanta Falcons", "New York Jets", "New York Giants", "Dallas Cowboys"]
    # process.extract("new york jets", choices, limit=2)
    # -> [('New York Jets', 100), ('New York Giants', 78)]
    try:
        results = process.extract(input, choices, limit=2)
    except:
        return None, False
    if results and results[0][1]>threshold:
        # and (len(results)==1 or results[0][1]>results[1][1]): # no more than one
        return results[0][0], perfectMatch
    return None, perfectMatch

def format_distance(dst_km):
    if (dst_km>=10):
        return str(round(dst_km, 0)) + " Km"
    if (dst_km>=1):
        return str(round(dst_km, 1)) + " Km"
    return str(int(dst_km * 1000)) + " m"

def makeListOfList(L):
    result = [[l] for l in L]
    return result

def removeDuplicatesFromList(list):
    no_dupicated_list = []
    for x in list:
        if x not in no_dupicated_list:
            no_dupicated_list.append(x)
    return no_dupicated_list