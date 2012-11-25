# -*- coding: utf-8 -*-
from lib.client import Client
from lib.planet import Planet
from lib.signals import GameOver, Win
import math

__author__ = 'lexich'

def appendInDictOfArrayVal(d, key, value):
  if not d.has_key(key):
    d[key] = []
  d[key].append(value)


def updateInDictOfDictVal(d, key, val):
  if not d.has_key(key):
    d[key] = {}
  d[key].update(val)


class MixinStrategies(object):
  STRATEGIES = (
    "aggressive",
    "rush",
    "support",
    "explorer",
    "patient",
    "redistribution",
    "runaway"
    )

  def strategy_aggressive(self, plan, request, _from, _to):
    """
    Реализация агрессивного нападения
    """
    needToAttack = _to.grow + 1
    #Если достаточно дройдов для захвата
    if _from.droids >= needToAttack:
      #Если опасность не угрожает
      if _from.danger < _from.droids - needToAttack:
        request.add(_from.id, _to.id, _from.sendDroids(needToAttack, limit=1), "aggressive")
        return

      #Если опасность угрожает но есть подмога
      friends = filter(lambda x: x.is_myself, _from.neighbours)
      maxHelp = sum(map(lambda x: x.attack, friends))

      #Если помощь подмоги достаточна
      if _from.danger < (_from.droids - needToAttack) + maxHelp:
        #Определяем коэффициент равномерности поддержки
        kSupport = (_from.droids - needToAttack) / maxHelp
        if kSupport < 0:
          return
          #Отправляем на атаку
        request.add(_from.id, _to.id, _from.sendDroids(needToAttack, limit=1), "aggressive")
        #Равномерно оказываем поддержку
        for friend in friends:
          droids = int(math.ceil(friend.attack * kSupport))
          request.add(friend.id, _from.id, friend.sendDroids(droids), "aggressive")
        return
        #Если агрессивное нападение не удалось пробрасваем его до умеренного
    super(MixinStrategies, self).trySendDroids(plan, _from, _to, "patient")

  def strategy_rush(self, plan, request, _from, _to):
    """
    Реализация быстрого нападения
    """
    kPlanetFull = 0.3
    kDroidsAttack = 0.7
    kResist = 0.9
    #Атака {kDroidsAttack} дройдов
    attackDroids = _from.droids * kDroidsAttack
    #Если сосед не враг
    if not _to.is_enemy:
      #Проверяем окружение планеты приемника на злобность
      if attackDroids > _to.get_danger() * kResist:
        request.add(_from.id, _to.id, _from.sendDroids(attackDroids), "rush")
    #Если сосед - враг
    else:
      #Заполненность планеты
      k = _from.growRating(_from.droids) / _from.growRating(10)
      #если заполненность меньше {kPlanetFull}, отказываемся
      if k > kPlanetFull:
        return
      maxResist = _to.danger

      #Если атака больше {kResist} сопротивления
      if attackDroids > maxResist * kResist:
        request.add(_from.id, _to.id, _from.sendDroids(attackDroids), "rush")

  def strategy_support(self, plan, request, _from, _to):
    """
    Стратегия помощи планетам ускорить рост популяции,
    целесообразно для планет доноров
    """
    #Если планета приемник в безопасности
    if not _to.danger:
      maxSendDroids = _from.attack
      #если допустимое для атаки кол-во дройдов ненулевое
      if maxSendDroids > 10 - _to.droids:
        needToSend = Planet.SPEED_GROW_RATING * _to.limit - _to.droids
        sendToDroids = maxSendDroids if needToSend > maxSendDroids else needToSend
        request.add(_from.id, _to.id, _from.sendDroids(sendToDroids), "support")
        #если у планеты приемника меньше 10 юнитов то отправим недостающее кол-во
      if _to.droids < 10 and not _to.maxMyselfNeighboursAttack():
        neighboursMyselfCount = len(filter(
          lambda x: x.droids > 10,
          _to.neighboursMyself()
        ))
        sendDroids = math.ceil(
          (10.0 - _to.droids) / neighboursMyselfCount
        ) if neighboursMyselfCount > 0 else 10
        request.add(_from.id, _to.id, _from.sendDroids(sendDroids), "support")

  def strategy_explorer(self, plan, request, _from, _to):
    explorerAttack = 10
    explorerRating = 7
    resistanceRating = 0.7
    #Если текущая планета менее привлектельна нежели соседняя
    #И одновременная атака нас не уничтожит
    #Переселяем всю планету кроме сухого остатка
    if _from.limit < _to.limit and\
       (_from.droids - explorerAttack) > _to.danger * resistanceRating:
      request.add(_from.id, _to.id, _from.sendDroids(_from.droids), "explorer")
    #Если допустима атака выше атаки исследования и ретинг роста позволяет
    #Начинаем исследование планет
    elif _from.attack > explorerAttack and\
         _from.growRating(_from.droids) < explorerRating:
      #Если исследование территории  опасно
      #И уровень опасности больше атаки планеты источника
      #То отправляем дройда на разведку
      if _to.danger > _from.attack:
        request.add(_from.id, _to.id, _from.sendDroids(1), "explorer")
      #Иначе проводим настоящую атаку
      else:
        request.add(_from.id, _to.id, _from.sendDroids(_to.danger + explorerAttack), "explorer")

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
        request.add(_from.id, _to.id, _from.sendDroids(_from.attack), "patient")
    else:
      for from_item in to_plan:
        src = from_item[0]
        request.add(src.id, _to.id, src.sendDroids(src.attack), "patient")

  def strategy_redistribution(self, plan, request, _from, _to):
    if _from.growRating(_from.droids) > 1:
      return
    droidsRedistribution = _from.droids - int(_from.limit / (1 + _from.percent))

    if droidsRedistribution < 0:
      print "executePlanRedistribution: Error droidsRedistribution %s" % droidsRedistribution
      return

    if not( _from.is_myself and _to.is_myself):
      return
      #Если у планеты приемника 1 сосед(источник) и заполнена, то пропускаем
    if _to.neighbours == 1 and _to.growRating(_to.droids) < 1:
      return

    if _to.growRating(_to.droids) < 1 and _from.growRating(_from.droids) < 1:
      if _to.droids > _from.droids:
        return
      if _from.danger > _to.danger:
        return
      fromDanger = _from.fullNeighboursDanger()
      toDanger = _to.fullNeighboursDanger(fromDanger)
      if fromDanger > toDanger:
        return

    request.add(_from.id, _to.id, _from.sendDroids(droidsRedistribution), "redistribution")

  def strategy_runaway(self, plan, request, _from, _to):
    if not _from.is_myself:
      return
    if _to.is_enemy:
      return
    if _to.danger > _from.droids:
      return
    request.add(_from.id, _to.id, _from.sendDroids(_from.droids, limit=0), "runaway")

  def is_strategy_check(self, plan, request, _from, _to, _strategy):
    if _strategy == "runaway":
      return True
    if not _from.is_myself:
      print "ERROR: is_strategy_check _from is not myself"
      return False
      #Если планета источник мертва
    if _from.is_dead():
      #Находим живых не чужих соседей
      arr = filter(
        lambda n: not n.is_dead() and not n.is_enemy,
        _from.neighbours
      )
      for target in arr:
        super(MixinStrategies, self).trySendDroids(plan, _from, target, "runaway")
        #если наша планета приемник мертва
    if _to.is_myself and _to.is_dead():
      #Находим живых не чужих соседей
      arr = filter(
        lambda n: not n.is_dead() and not n.is_enemy,
        _to.neighbours
      )
      for target in arr:
        super(MixinStrategies, self).trySendDroids(plan, _to, target, "runaway")
    if _from.is_dead() or _to.is_dead():
      return False
    return True


def _cmp_default(_x, _y):
  x, y = _x[1], _y[1]
  result = cmp(x.danger, y.danger)
  return result if result != 0 else cmp(x.limit, y.limit)


class GameConfig(Client):
  def trySendDroids(self, plan, _from, _to, _strategy="patient"):
    """
    strategy ['aggressive','rush','explorer','patient','redistribution','support' ]
    """
    if not _from.is_myself:
      return
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
    else:
      items = sorted(items, cmp=_cmp_default, reverse=True)
    func = getattr(self, "strategy_%s" % strategy, None)
    if not func:
      return
    for item in items:
      _from, _to, _strategy = item
      if self.is_strategy_check(plan, request, _from, _to, _strategy):
        func(plan, request, _from, _to)

  def actionOneNeighbours(self, plan, src, target):
    if target.is_enemy or (
      target.is_myself
      and src.growRating(src.droids) < target.growRating(target.droids)):
      self.trySendDroids(plan, src, target, "rush")

  def actionFixPosition(self, myPlanets, neighbours, planets, request, plan):
    ratingFilter = 0.5
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
                fullTarget = target.fullNeighboursDanger()
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
          #Если переселятся не собираемся
          #Если скорость прироста дройдов больше границы {growSpeedRating}
          if target.speedGrowRating() > Planet.SPEED_GROW_RATING:
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
    freePlanets = {}
    enemyPlanets = {
      "all": {},
      "owner": {}
    }
    planetLimitRating = {
      "my": {},
      "free": {},
      "enemy": {}
    }
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

    self.actionGlobalStrategy(planetLimitRating, neighbours, planets, request, plan)
    self.actionGlobalSupport(myPlanets, neighbours, planets, request, plan)
    self.actionFixPosition(myPlanets, neighbours, planets, request, plan)
    self.actionSendExplorers(myPlanets, neighbours, planets, request, plan)
    self.actionAttackEnemy(myPlanets, neighbours, planets, request, plan)

    for strategy in self.STRATEGIES:
      self.execute(plan, request, strategy)

    print request.debugFull

  def actionGlobalStrategy(self, planetLimitRating, neighbours, planets, request,
                           plan):
    if len(planetLimitRating["free"].keys()) <= 0:
      return
    exclude = set()
    keysPriority = sorted(planetLimitRating["free"].keys(), reverse=True)
    for limit in keysPriority:
      freePlanets = planetLimitRating["free"][limit]
      for free in freePlanets:
        findmyPlanets = free.findMyNearsPlanets()
        myPlanets = filter(lambda x: x.limit < limit, findmyPlanets)
        for p in myPlanets:
          pathToTarget = p.searchPathToTarget(free)
          if not pathToTarget: continue
          roadLong, target = pathToTarget
          if p in exclude: continue
          exclude.add(p)
          self.trySendDroids(plan, p, target, "rush")

  def actionGlobalSupport(self, myPlanets, neighbours, planets, request, plan):
    for id, target in myPlanets.iteritems():
      if target.speedGrowRating() > Planet.SPEED_GROW_RATING: continue
      neigh = sorted(target.neighbours, key=lambda x: x.droids, reverse=True)
      self.trySendDroids(plan, neigh[0], target, "support")



