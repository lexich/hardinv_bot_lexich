# -*- coding: utf-8 -*-
from exceptions import ValueError
import math
import simplejson as json

__author__ = 'lexich'

class Win(Exception):
  pass


class GameOver(Exception):
  pass


def cache(func):
  key = func.func_name

  def wrap(self, *args, **kwargs):
    if not hasattr(self, "__cache_wrap"):
      self.__cache_wrap = {}
    if not self.__cache_wrap.has_key(key):
      self.__cache_wrap[key] = func(self, *args, **kwargs)
    return self.__cache_wrap[key]

  return wrap


class Planet(object):
  PROPERTY = {
    "TYPE_A": {
      "p": 0.1,
      "limit": 100.0
    },
    "TYPE_B": {
      "p": 0.15,
      "limit": 200.0
    },
    "TYPE_C": {
      "p": 0.2,
      "limit": 500.0
    },
    "TYPE_D": {
      "p": 0.3,
      "limit": 1000.0
    }
  }

  def __init__(self, obj, planets, user):
    self.user = user
    self.id = obj.attr("id")
    self.planets = planets
    planets[self.id] = self
    self.owner = obj.owner.val
    self.type = obj.type.val
    self.droids = obj.droids.to_int
    self._neighbours = obj.neighbours

  def __unicode__(self):
    return "%s %s" % (self.user, self.id)

  @cache
  def get_neighbours(self):
    return map(lambda id: self.planets[id], self._neighbours)

  @property
  def neighbours(self):
    return self.get_neighbours()


  @cache
  def get_danger(self):
    rating = {}
    if self.is_enemy:
      rating[self.owner] = self.grow

    for n in self.neighbours:
      if not n.is_enemy: continue
      if not rating.has_key(n.owner):
        rating[n.owner] = 0
      rating[n.owner] += n.droids
    return max(rating.values()) if len(rating.values()) > 0 else 0

  @property
  def danger(self):
    return self.get_danger()

  def sendDroids(self, n, limit=10):
    """
    Отправить дройдов
    """
    if self.droids - limit > n:
      self.droids -= n
      return n
    elif self.droids < limit:
      return 0
    else:
      res = self.droids - limit
      self.droids = limit
      return res

  def growRating(self, x=10):
    """
    За сколько шагов планета достигнет полной населенности
    с x дройдов
    """
    base = self.limit / x if x > 0 else self.limit
    if not base: raise Exception("Unknown planet")
    return math.log(base, 1 + self.percent)

  @property
  def grow(self):
    return self.droids * (1 + self.percent)

  #рейтинг для атаки
  RATING_ATTACK = 3

  @property
  def attack(self):
    """
    Дройды используемые для атаки
    """
    rating = self.growRating(self.droids)
    if rating < self.RATING_ATTACK:
      return int(self.droids * self.percent)
    return 0

  @property
  def is_myself(self):
    return self.owner == self.user

  @property
  def is_free(self):
    return self.owner is None

  @property
  def is_enemy(self):
    return not self.is_free and self.owner != self.user


  @property
  def percent(self):
    property = self.PROPERTY.get(self.type, {})
    return property.get("p", 0)

  @property
  def limit(self):
    property = self.PROPERTY.get(self.type, {})
    return property.get("limit", 0)


class Request(object):
  def __init__(self, token):
    self.token = token
    self.actions = []

  def add(self, _from, _to, unitscount):
    self.actions.append({
      "from": int(_from),
      "to": int(_to),
      "unitscount": int(unitscount)
    })

  @property
  def _xmlActions(self):
    return u"".join(
      map(
        lambda action: u"""
        <action>
          <from>%(from)d</from>
          <to>%(to)d</to>
          <unitscount>%(unitscount)d</unitscount>
        </action>
        """ % action, self.actions))

  @property
  def to_xml(self):
    return u'''<?xml version="1.0" encoding="utf-8"?>
    <request>
      <token>{0}</token>
      <actions>{1}</actions>
    </request>
    '''.format(self.token, self._xmlActions)

  def __unicode__(self):
    return json.dumps(self.actions)


class DomEl(object):
  def __init__(self, el):
    self._el = el

  @property
  def el(self):
    return super(DomEl, self).__getattribute__("_el")

  @property
  def to_int(self):
    try:
      return int(self.val)
    except ValueError, e:
      return 0

  @property
  def val(self):
    return self.el.firstChild.nodeValue if self.el.firstChild else None

  def attr(self, name):
    return self.el.attributes.get(name).value

  @property
  def planets(self):
    return [DomEl(x) for x in self.el.getElementsByTagName("planet")]

  @property
  def neighbours(self):
    return [DomEl(x).val for x in self.el.getElementsByTagName("neighbour")]

  @property
  def errors(self):
    return [DomEl(x).val for x in self.el.getElementsByTagName("error")]

  def __getattribute__(self, name):
    if type(self).__dict__.has_key(name):
      return super(DomEl, self).__getattribute__(name)
    else:
      resp = self.el.getElementsByTagName(name)
      return DomEl(resp[0]) if len(resp) == 1 else self
