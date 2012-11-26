# -*- coding: utf-8 -*-
import simplejson as json

__author__ = 'lexich'

class Request(object):
  def __init__(self, token, planets={}):
    self.token = token
    self.actions = []
    self.planets = planets
    self.debug = {}
    self.debugFull = []

  def add(self, _from, _to, unitscount, strategy=""):
    if not self.planets[_from].is_myself:
      return
    if unitscount == 0:
      return
    elif unitscount < 0:
      return
    if strategy in ("quickexplore","aggressive","rush","redistribution"):
      self.planets[_from].set_fast_strategy()
    self.planets[_to].receive_droids = int(unitscount)

    self.addDebug(_from, _to, unitscount, strategy)
    self.actions.append({
      "from": int(_from),
      "to": int(_to),
      "unitscount": int(unitscount)
    })

  def addDebug(self, _from, _to, unitscount, strategy):
    val = {
      "from": _from,
      "to": _to,
      "unitscount": int(unitscount),
      "strategy": strategy
    }
    if not self.debug.has_key(_from):
      self.debug[_from] = {}
    if not self.debug.has_key(_to):
      self.debug[_to] = {}
    self.debug[_from][_to] = val
    self.debug[_to][_from] = val
    self.debugFull.append("%s - %s" % (strategy, unitscount))


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