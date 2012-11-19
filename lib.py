# -*- coding: utf-8 -*-
__author__ = 'lexich'

class Planet(object):

  PROPERTY = {
    "TYPE_A":{
      "p":0.1,
      "limit":100
    },
    "TYPE_B":{
      "p":0.15,
      "limit":200
    },
    "TYPE_C":{
      "p":0.2,
      "limit":500
    },
    "TYPE_D":{
      "p":0.3,
      "limit":1000
    }
  }
  def __init__(self, obj, planets, user):
    self.user = user
    self.id = obj["@id"]
    self.planets = planets
    planets[self.id] = self
    self.owner = obj["owner"]["#text"]
    self.type = obj["type"]["#text"]
    self.droids = int(obj["droids"]["#text"])
    self._neighbours = map(lambda neighbour: neighbour["#text"], obj["neighbours"])

  @property
  def neighbours(self):
    if not self._neighbours_cache:
      self._neighbours_cache = map(lambda id:self.planets[id], self._neighbours )
    return self._neighbours_cache

  @property
  def danger(self):
    def handle(n):
      if n.owner == "" or n.owner == self.user:
        return 0
      else:
        if n.owner == self.owner:
          return self.droids + n.droids
        else:
          return self.droids

    return max(
      max(map(handle, self.neighbours)),
      self.droids
    )

  @property
  def grow(self):
    return self.droids * (1+self.percent)

  @property
  def percent(self):
    property = getattr(self.PROPERTY,self.type,{})
    return getattr(property,"p",0)

  @property
  def limit(self):
    property = getattr(self.PROPERTY,self.type,{})
    return getattr(property,"limit",0)


class Request(object):
  def __init__(self, token):
    self.token = token
    self.actions = []

  def add(self, _from, _to, unitscount):
    self.actions.append({
      "from":_from,
      "to":_to,
      "unitscount":unitscount
    })

  def get(self):
    return {
      "request":{
        "token":self.token,
        "actions":self.actions
      }
    }