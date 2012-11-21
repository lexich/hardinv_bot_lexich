# -*- coding: utf-8 -*-
from lib.client import Client
from lib.signals import GameOver, Win
import math

__author__ = 'lexich'


class Game(Client):
  def trySendDroids(self, plan, _from, _to, _strategy="patient"):
    """
    strategy ['aggressive','rush','explorer','patient','redistribution','support' ]
    """
    config = [
      ("from", _from.id),
      ("to", _to.id),
      ("strategy", _strategy)
    ]
    value = (_from, _to, _strategy)
    for key, id in config:
      if not plan[key].has_key(id):
        plan[key][id] = []
      plan[key][id].append(value)

  def handle(self, planets, request):
    myPlanets = {}
    plan = {
      "from": {},
      "to": {},
      "strategy": {}
    }
    neighbours = {
      "my": {},
      "free": {},
      "enemy": {}
    }
    for id, p in planets.iteritems():
      if not p.is_myself: continue
      myPlanets[id] = p
      if len(p.neighbours) == 1:
        self.oneNeighbours(plan, p, p.neighbours[0])
      for n in p.neighbours:
        if n.is_myself:
          iterNeighbours = neighbours["my"]
        elif n.is_free:
          iterNeighbours = neighbours["free"]
        else:
          iterNeighbours = neighbours["enemy"]
        iterNeighbours[n.id] = n

    #Проверяем окончание игры
    if not len(myPlanets.keys()):
      raise GameOver()
    elif len(myPlanets) == len(planets.values()):
      raise Win()

    self.fixPosition(myPlanets, neighbours, planets, request, plan)
    self.sendExplorers(myPlanets, neighbours, planets, request, plan)
    self.attackEnemy(myPlanets, neighbours, planets, request, plan)
    self.executePlan(myPlanets, neighbours, planets, request, plan)

  def oneNeighbours(self, plan, src, target):
    if target.is_enemy or (
      target.is_myself
      and src.growRating(src.droids) < target.growRating(target.droids)):
      self.trySendDroids(plan, src, target, "rush")

  def fixPosition(self, myPlanets, neighbours, planets, request, plan):
    ratingFilter = 0.5
    minDroids = 10
    for id, target in neighbours["my"].iteritems():
      mySourcesPlanets = filter(
        lambda p: p.is_myself,
        target.neighbours
      )
      for src in mySourcesPlanets:
        if src.growRating(src.droids) <= 1:
          self.trySendDroids(plan, src, target, "redistribution")
        #если дройлов меньше {minDroids}
        if target.droids < minDroids:
          self.trySendDroids(plan, src, target, "support")
        else:
          if src.droids / src.limit < ratingFilter:
            continue
          if src.growRating(src.droids) > target.growRating(target.droids):
            continue
          if target.droids > target.danger:
            continue
          self.trySendDroids(plan, src, target, "patient")


  def sendExplorers(self, myPlanets, neighbours, planets, request, plan):
    for id, target in neighbours["free"].iteritems():
      mySourcesPlanets = filter(
        lambda p: p.is_myself,
        target.neighbours
      )
      for src in mySourcesPlanets:
        self.trySendDroids(plan, src, target, "explorer")

  def attackEnemy(self, myPlanets, neighbours, planets, request, plan):
    for id, target in neighbours["enemy"].iteritems():
      mySourcesPlanets = filter(
        lambda p: p.is_myself,
        target.neighbours
      )
      for src in mySourcesPlanets:
        if len(target.neighbours) == 1 or len(filter(
          lambda x: x.is_enemy,
          target.neighbours
        )) == 0:
          self.trySendDroids(plan, src, target, "aggressive")
        else:
          self.trySendDroids(plan, src, target, "patient")


  def executePlanRedistribution(self, plan, request):
    redistribution = plan["strategy"].get("redistribution", [])
    for item in redistribution:
      _from, _to, strategy = item
      if _from.growRating(_from.droids) > 1: continue
      droidsRedistribution = _from.droids - int(_from.limit / (1 + _from.percent))

      if droidsRedistribution < 0:
        print "executePlanRedistribution: Error droidsRedistribution %s" % droidsRedistribution
        continue

      if _to.growRating(_to.droids) > 1:
        request.add(_from.id, _to.id, _from.sendDroids(droidsRedistribution))
      elif _from.limit > _to.limit:
        request.add(_from.id, _to.id, _from.sendDroids(droidsRedistribution))
      elif _from.limit == _to.limit:
        if len(_from.neighbours) < len(_to.neighbours):
          request.add(_from.id, _to.id, _from.sendDroids(droidsRedistribution))


  def executePlanAggressive(self, plan, request):
    """
    Реализация агрессивного нападения
    """
    aggressive = plan["strategy"].get("aggressive", [])
    for item in aggressive:
      _from, _to, strategy = item
      needToAttack = _to.grow + 1
      #Если достаточно дройдов для захвата
      if _from.droids >= needToAttack:
        #Если опасность не угрожает
        if _from.danger < _from.droids - needToAttack:
          request.add(_from.id, _to.id, _from.sendDroids(needToAttack, limit=1))
          continue

        #Если опасность угрожает но есть подмога
        friends = filter(lambda x: x.is_myself, _from.neighbours)
        maxHelp = sum(map(lambda x: x.attack, friends))

        #Если помощь подмоги достаточна
        if _from.danger < (_from.droids - needToAttack) + maxHelp:
          #Определяем коэффициент равномерности поддержки
          kSupport = (_from.droids - needToAttack - _from.danger + 1.0) / maxHelp
          if kSupport < 0: continue
          #Отправляем на атаку
          request.add(_from.id, _to.id, _from.sendDroids(needToAttack, limit=1))
          #Равномерно оказываем поддержку
          for friend in friends:
            droids = int(math.ceil(friend.attack * kSupport))
            request.add(friend.id, _from.id, friend.sendDroids(droids))
          continue
        #Если агрессивное нападение не удалось пробрасваем его до умеренного
      self.trySendDroids(plan, _from, _to, "patient")

  def executePlanRush(self, plan, request):
    """
    Реализация быстрого нападения
    """
    rush = plan["strategy"].get("rush", [])
    kPlanetFull = 0.5
    kDroidsAttack = 0.7
    kResist = 0.9
    for item in rush:
      _from, _to, strategy = item
      #Атака {kDroidsAttack} дройдов
      attackDroids = _from.droids * kDroidsAttack
      #Если сосед не враг
      if not _to.is_enemy:
        request.add(_from.id,_to.id, _from.sendDroids(attackDroids))
      #Если сосед враг
      else:
        #Заполненность планеты
        k = _from.growRating(_from.droids) / _from.growRating(10)
        #если заполненность меньше {kPlanetFull}, отказываемся
        if k > kPlanetFull: continue
        maxResist = _to.danger

        #Если атака больше {kResist} сопротивления
        if attackDroids > maxResist * kResist:
          request.add(_from.id, _to.id, _from.sendDroids(attackDroids))

  def executePlanExplorer(self, plan, request):
    explorer = sorted(
      plan["strategy"].get("explorer", []),
      key=lambda x: x[1].growRating()
    )
    explorerAttack = 15
    explorerRating = 7
    for item in explorer:
      _from, _to, strategy = item
      if _from.limit < _to.limit:
        request.add(_from.id, _to.id, _from.sendDroids(_from.droids))
      elif _from.attack > explorerAttack and\
           _from.growRating(_from.droids) < explorerRating:
        request.add(_from.id, _to.id, _from.sendDroids(explorerAttack))
      elif len(_from.neighbours) == 1:
        request.add(_from.id, _to.id, _from.sendDroids(explorerAttack))

  def executePlanPatient(self, plan, request):
    attackPersentBarrier = 0.9
    patient = plan["strategy"].get("patient", [])
    for item in patient:
      _from, _to, strategy = item
      to_plan = plan["to"].get(_to, [])
      maxAttack = sum(map(
        lambda item: item[0].attack, to_plan
      )) if len(to_plan) > 0 else 0
      #Если атака меньше 90% то отказываемся
      if maxAttack < _to.danger * attackPersentBarrier:
        #Но если планета заполнена атакуем в любом случае
        if _from.growRating(_from.droids) < 3:
          request.add(_from.id, _to.id, _from.sendDroids(_from.attack))
      else:
        for from_item in to_plan:
          src = from_item[0]
          request.add(src.id, _to.id, src.sendDroids(src.attack))

  def executePlanSupport(self, plan, request):
    support = plan["strategy"].get("support", [])
    for item in support:
      _from, _to, strategy = item
      if _to.danger == 0 and _to.droids <= 10:
        request.add(_from.id, _to.id, _from.sendDroids(15))
      elif _to.danger > _to.droids:
        request.add(_from.id, _to.id, _from.sendDroids(_from.attack) )



  def executePlan(self, myPlanets, neighbours, planets, request, plan):
    self.executePlanAggressive(plan, request)
    self.executePlanRush(plan, request)
    self.executePlanSupport(plan,request)
    self.executePlanExplorer(plan, request)
    self.executePlanPatient(plan, request)
    self.executePlanRedistribution(plan, request)
