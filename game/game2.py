# -*- coding: utf-8 -*-
from lib.client import Client
from lib.signals import GameOver, Win
import math

__author__ = 'lexich'


class MixinStrategies(object):
  STRATEGIES = (
    "aggressive",
    "rush",
    "support",
    "explorer",
    "patient",
    "redistribution"
    )

  def strategy_redistribution(self, plan, request, _from, _to):
    if _from.growRating(_from.droids) > 1:
      return
    droidsRedistribution = _from.droids - int(_from.limit / (1 + _from.percent))

    if droidsRedistribution < 0:
      print "executePlanRedistribution: Error droidsRedistribution %s" % droidsRedistribution
      return
    request.add(_from.id, _to.id, _from.sendDroids(droidsRedistribution))


  def strategy_aggressive(self, plan, request, _from, _to):
    """
    Реализация агрессивного нападения
    """
    needToAttack = _to.grow + 1
    #Если достаточно дройдов для захвата
    if _from.droids >= needToAttack:
      #Если опасность не угрожает
      if _from.danger < _from.droids - needToAttack:
        request.add(_from.id, _to.id, _from.sendDroids(needToAttack, limit=1))
        return

      #Если опасность угрожает но есть подмога
      friends = filter(lambda x: x.is_myself, _from.neighbours)
      maxHelp = sum(map(lambda x: x.attack, friends))

      #Если помощь подмоги достаточна
      if _from.danger < (_from.droids - needToAttack) + maxHelp:
        #Определяем коэффициент равномерности поддержки
        kSupport = (_from.droids - needToAttack - _from.danger + 1.0) / maxHelp
        if kSupport < 0:
          return
          #Отправляем на атаку
        request.add(_from.id, _to.id, _from.sendDroids(needToAttack, limit=1))
        #Равномерно оказываем поддержку
        for friend in friends:
          droids = int(math.ceil(friend.attack * kSupport))
          request.add(friend.id, _from.id, friend.sendDroids(droids))
        return
        #Если агрессивное нападение не удалось пробрасваем его до умеренного
    super(MixinStrategies, self).trySendDroids(plan, _from, _to, "patient")

  def strategy_rush(self, plan, request, _from, _to):
    """
    Реализация быстрого нападения
    """
    kPlanetFull = 0.5
    kDroidsAttack = 0.7
    kResist = 0.9

    #Атака {kDroidsAttack} дройдов
    attackDroids = _from.droids * kDroidsAttack
    #Если сосед не враг
    if not _to.is_enemy:
      #Проверяем окружение планеты приемника на злобность
      if attackDroids > _to.neighboursDanger() * kResist:
        request.add(_from.id, _to.id, _from.sendDroids(attackDroids))
    #Если сосед враг
    else:
      #Заполненность планеты
      k = _from.growRating(_from.droids) / _from.growRating(10)
      #если заполненность меньше {kPlanetFull}, отказываемся
      if k > kPlanetFull:
        return
      maxResist = _to.danger

      #Если атака больше {kResist} сопротивления
      if attackDroids > maxResist * kResist:
        request.add(_from.id, _to.id, _from.sendDroids(attackDroids))

  def strategy_explorer(self, plan, request, _from, _to):
    explorerAttack = 15
    explorerRating = 7

    if _from.limit < _to.limit:
      request.add(_from.id, _to.id, _from.sendDroids(_from.droids))
    elif _from.attack > explorerAttack and\
         _from.growRating(_from.droids) < explorerRating:
      request.add(_from.id, _to.id, _from.sendDroids(explorerAttack))
    elif len(_from.neighbours) == 1:
      request.add(_from.id, _to.id, _from.sendDroids(explorerAttack))

  def strategy_patient(self, plan, request, _from, _to):
    attackPersentBarrier = 0.9
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

  def strategy_support(self, plan, request, _from, _to):
    if _to.danger == 0 and _to.droids <= 10:
      request.add(_from.id, _to.id, _from.sendDroids(15))
    elif _to.danger > _to.droids:
      request.add(_from.id, _to.id, _from.sendDroids(_from.attack))


class GameConfig(Client):
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

  def execute(self, plan, request, strategy):
    items = plan["strategy"].get(strategy, [])
    if strategy == "explorer":
      items = sorted(
        items,
        key=lambda x: x[1].growRating()
      )
    func = getattr(self, "strategy_%s" % strategy, None)
    if not func:
      return
    for item in items:
      _from, _to, _strategy = item
      func(plan, request, _from, _to)

  def oneNeighbours(self, plan, src, target):
    if target.is_enemy or (
      target.is_myself
      and src.growRating(src.droids) < target.growRating(target.droids)):
      self.trySendDroids(plan, src, target, "rush")

  def actionFixPosition(self, myPlanets, neighbours, planets, request, plan):
    ratingFilter = 0.5
    minDroids = 10
    for id, target in neighbours["my"].iteritems():
      mySourcesPlanets = filter(
        lambda p: p.is_myself,
        target.neighbours
      )
      for src in mySourcesPlanets:
        #Если на планете источнике наблюдается переполнение
        if src.growRating(src.droids) <= 1:
          #Если планета приемник в безопасности
          if not target.danger:
            #Если планете источнику ничего не угражает
            if not src.danger:
              #Если опасность у соседей планеты приемника больше
              if target.neighboursDanger() > src.neighboursDanger():
                self.trySendDroids(plan, src, target, "redistribution")
              else:
              #Если у соседей планет тоже все в поряке применяем глубокий поиск
                fullTarget = target.fullNeighboursDanger(0)
                fullSrc = src.fullNeighboursDanger(fullTarget)
                if fullTarget > fullSrc:
                  self.trySendDroids(plan, src, target, "redistribution")

                continue
            else:
              continue
          #У планеты приемника есть опасность
          else:
            self.trySendDroids(plan, src, target, "redistribution")
        else:
          #если дройлов меньше минимального колличества {minDroids}
          if target.droids < minDroids:
            self.trySendDroids(plan, src, target, "support")
          #если дройдов больше минимума
          else:
            #Если колличество дройдов недостаточно для отправки пропускаем
            if src.droids / src.limit < ratingFilter:
              continue
            #Если рейтинг у планеты приемника выше, то пропускаем
            if src.growRating(src.droids) > target.growRating(target.droids):
              continue
            #Если планета приемник готова сопротивлятся агрессии, то пропускаем
            if target.droids > target.danger:
              continue
            self.trySendDroids(plan, src, target, "patient")


  def actionSendExplorers(self, myPlanets, neighbours, planets, request, plan):
    for id, target in neighbours["free"].iteritems():
      mySourcesPlanets = filter(
        lambda p: p.is_myself,
        target.neighbours
      )
      for src in mySourcesPlanets:
        self.trySendDroids(plan, src, target, "explorer")

  def actionAttackEnemy(self, myPlanets, neighbours, planets, request, plan):
    for id, target in neighbours["enemy"].iteritems():
      mySourcesPlanets = filter(
        lambda p: p.is_myself,
        target.neighbours
      )
      for src in mySourcesPlanets:
        #Если планета источник наедине с врагом, агрессивное нападение
        if len(target.neighbours) == 1 or len(filter(
          lambda x: x.is_enemy,
          target.neighbours
        )) == 0:
          self.trySendDroids(plan, src, target, "aggressive")
        else:
          self.trySendDroids(plan, src, target, "patient")


class Game(MixinStrategies, GameConfig):
  def handle(self, planets, request):
    myPlanets = {}
    plan = {"from": {}, "to": {}, "strategy": {}}
    neighbours = {"my": {}, "free": {}, "enemy": {}}

    for id, p in planets.iteritems():
      if not p.is_myself:
        continue
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

    self.actionFixPosition(myPlanets, neighbours, planets, request, plan)
    self.actionSendExplorers(myPlanets, neighbours, planets, request, plan)
    self.actionAttackEnemy(myPlanets, neighbours, planets, request, plan)

    for strategy in self.STRATEGIES:
      self.execute(plan, request, strategy)
