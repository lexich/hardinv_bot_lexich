__author__ = 'lexich'

def appendInDictOfArrayVal(d, key, value):
  if not d.has_key(key):
    d[key] = []
  d[key].append(value)


def updateInDictOfDictVal(d, key, val):
  if not d.has_key(key):
    d[key] = {}
  d[key].update(val)