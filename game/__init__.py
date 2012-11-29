#!/usr/bin/env python
# -*- coding: utf-8 -*-

from actions import  GameActions
from helpers import *
from strategy import *
from lib.signals import GameOver, Win
__author__ = 'lexich'

class Game(MixinStrategies, GameActions):
  def handle(self, planets, request):
    myPlanets = {}
    freePlanets = {}
    enemyPlanets = {"all": {}, "owner": {}}
    planetLimitRating = {"my": {}, "free": {}, "enemy": {}}
    plan = {"from": {}, "to": {}, "strategy": {}}
    neighbours = {"my": {}, "free": {}, "enemy": {}}

    for id, p in planets.iteritems():
      #Проводим классификацию планет
      if    p.is_free:
        freePlanets[id] = p
        appendInDictOfArrayVal(planetLimitRating["free"], p.limit, p)
      elif  p.is_myself:
        myPlanets[id] = p
        appendInDictOfArrayVal(planetLimitRating["my"], p.limit, p)
      else:
        updateInDictOfDictVal(enemyPlanets["owner"], p.owner, {id: p})
        appendInDictOfArrayVal(planetLimitRating["enemy"], p.limit, p)

      #Далее анализируем только собственные планеты
      if not p.is_myself:
        continue
      if len(p.neighbours) == 1:
        self.actionOneNeighbours(plan, p, p.neighbours[0])
      for n in p.neighbours:
        if n.is_myself: iterNeighbours = neighbours["my"]
        elif n.is_free: iterNeighbours = neighbours["free"]
        else:           iterNeighbours = neighbours["enemy"]
        iterNeighbours[n.id] = n

    #Проверяем окончание игры
    if not len(myPlanets.keys()):
      raise GameOver()
    elif len(myPlanets.keys()) + len(freePlanets.keys()) == len(planets.keys()):
      raise Win()
    params = {
      "planetLimitRating": planetLimitRating,
      "neighbours": neighbours,
      "myPlanets": myPlanets,
      "planets": planets,
      "request": request,
      "plan": plan
    }
    self.actionGlobalFreeRush(**params)
    self.actionGlobalSupport(**params)
    self.actionFixPosition(**params)
    self.actionSendExplorers(**params)
    self.actionAttackEnemy(**params)
    for strategy in self.STRATEGIES_PRIORITY:
      self.execute(plan, request, strategy)

    print request.debugFull
