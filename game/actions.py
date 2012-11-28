# -*- coding: utf-8 -*-
from constants import *
from lib.client import Client
from helpers import *

__author__ = 'lexich'

class GameActions(Client):
  def trySendDroids(self, plan, _from, _to, _strategy=PATIENT):
    """
    strategy [AGGRESSIVE,RUSH,EXPLORER,PATIENT,REDISTRIBUTION,SUPPORT ]
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

  def _cmp_default(self,_x, _y):
    x, y = _x[1], _y[1]
    result = cmp(x.danger, y.danger)
    return result if result != 0 else cmp(x.limit, y.limit)

  def execute(self, plan, request, strategy):
    items = plan["strategy"].get(strategy, [])
    if strategy == EXPLORER:
      items = sorted(
        items,
        key=lambda x: x[1].growRating()
      )
    else:
      items = sorted(items, cmp=self._cmp_default, reverse=True)
    func = getattr(self, "strategy_%s" % strategy, None)
    if not func:
      return
    for item in items:
      _from, _to, _strategy = item
      if self.is_strategy_check(plan, request, _from, _to, _strategy):
        func(plan, request, _from, _to)

  def actionOneNeighbours(self, plan, src, target):
    if target.is_enemy:
      self.trySendDroids(plan, src, target, RUSH)

  def actionFixPosition(self, neighbours, plan, planets, *args, **kwargs):
    redistributionRouter = {}
    for id, target in neighbours["my"].iteritems():
      #Сортируем соседей-друзей по рейтингу
      mySourcesPlanets = sorted(
        target.neighboursMyself()
        ,key=lambda x: x.growRating(x.droids)
      )
      for src in mySourcesPlanets:
        #Если на планете источнике наблюдается переполнение
        if src.growRating(src.droids) <= 1:
          appendInDictOfArrayVal(redistributionRouter,src,target)
        #Если на планете источнике переполнение не наблюдается
        else:
          #Если переселятся не собираемся
          #Если скорость прироста дройдов больше границы {growSpeedRating}
          if target.speedGrowRating() > SPEED_GROW_RATING:
            #Если колличество дройдов недостаточно для отправки пропускаем
            if src.droids / src.limit < ACTION_FIXPOSITION_RATING_FILTER:
              continue
              #Если рейтинг у планеты приемника выше, то пропускаем
            if src.growRating(src.droids) > target.growRating(target.droids):
              continue
              #Если планета приемник готова сопротивлятся агрессии, то пропускаем
            if target.droids > target.danger:
              continue
            self.trySendDroids(plan, src, target, PATIENT)
    self._actionFixPosition_redistribution(plan, redistributionRouter)

  def _actionFixPosition_redistribution(self,plan, redistributionRouter):
    #Перераспределение
    for src, targetArray in redistributionRouter.iteritems():
      self._actionFixPosition_redistribution_parce(plan, src,targetArray)

  def _cmp_redistibution_r1(self,x,y):
    result = cmp(x.get_danger(), y.get_danger())
    return result if result != 0 else cmp(x.growRating(x.droids), y.growRating(y.droids))

  def _actionFixPosition_redistribution_parce(self,plan, src, targetArray):
    #Сортируем по самым приоритетным направлениям
    targetArray.sort(cmp=self._cmp_redistibution_r1,reverse=True)
    for target in targetArray:
      #Если планета приемник в безопасности
      if not target.danger:
        #Если планете источнику ничего не угражает
        if not src.danger:
          #Если опасность у соседей планеты приемника больше
          if target.neighboursDanger() > src.neighboursDanger():
            self.trySendDroids(plan, src, target, REDISTRIBUTION)
            return
          else:
            #Если у соседей планет тоже все в поряке применяем глубокий поиск
            fullTarget = target.fullNeighboursDanger()
            fullSrc = src.fullNeighboursDanger(fullTarget)
            if fullTarget > fullSrc:
              self.trySendDroids(plan, src, target, REDISTRIBUTION)
              return
      #У планета приемник в опасности
      else:
        self.trySendDroids(plan, src, target, REDISTRIBUTION)
        return


  def actionSendExplorers(self, neighbours, plan, *args, **kwargs):
    exclude = set()
    for id, target in neighbours["free"].iteritems():
      #Сортируем по рейтингу заполнености планет от самого низкого(дройдов много) до высокого
      mySourcesPlanets = sorted(
        target.neighboursMyself(),
        key=lambda x: x.growRating(x.droids)
      )
      for src in mySourcesPlanets:
        if src in exclude: continue
        exclude.add(src)
        self.trySendDroids(plan, src, target, EXPLORER)

  def actionAttackEnemy(self, neighbours, plan, *args, **kwargs):
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
          self.trySendDroids(plan, src, target, AGGRESSIVE)
        else:
          self.trySendDroids(plan, src, target, PATIENT)

  def actionGlobalFreeRush(self, planetLimitRating, planets, plan, *args, **kwargs):
    """
    Глобальная стратения поиска свободных более приоритетных планет
    """
    #Если свободные планеты отсутствуют, пропускаем
    if len(planetLimitRating["free"].keys()) <= 0:
      return
      #Фильтр для того чтобы одна и таже планета источник не участвовала дважды
    exclude = set()
    #Сортируем свободные планеты начиная с самых жирных
    keysPriority = sorted(planetLimitRating["free"].keys(), reverse=True)
    for limit in keysPriority:
      freePlanets = planetLimitRating["free"][limit]
      #строим карту самых коротких путей
      shortestRoad = float("inf")
      nearestToFreePlanets = {}

      for free in freePlanets:
        result = free.findMyNearsPlanets()
        if not result: continue
        roadLong, findMyPlanets = result
        #Если найден новый путь - обнуляем
        if roadLong < shortestRoad:
          nearestToFreePlanets = {}
          #Добавляем данные если длина пути не меньше заданного
        if roadLong <= shortestRoad:
          if not nearestToFreePlanets.has_key(free.id):
            nearestToFreePlanets[free.id] = set()
          nearestToFreePlanets[free.id].update(findMyPlanets)
          shortestRoad = roadLong

      for target_id, srcPlanets in nearestToFreePlanets.iteritems():
        #Фильтруем планеты у которых лимит больше чем у свободной планеты
        mySrcPlanets = filter(lambda x: x.limit < limit, srcPlanets)
        #Получаем обьект свободной планеты
        freePlanet = planets[target_id]
        for src in mySrcPlanets:
          #Ищем ближайшую планеты для перехода
          pathToTarget = src.searchPathToTarget(freePlanet)
          if not pathToTarget: continue
          roadLong, target = pathToTarget
          #Если данная планета участвовала в стратегии пропускаеи
          if src in exclude: continue
          exclude.add(src)
          if target.is_enemy:
            self.trySendDroids(plan, src, target, RUSH)
          else:
            self.trySendDroids(plan, src, target, QUICKEXPLORE)

  def actionGlobalSupport(self, myPlanets, plan, *args, **kwargs):
    """
    Стратегия глобальной поддержки
    """
    for id, target in myPlanets.iteritems():
      if target.speedGrowRating() > SPEED_GROW_RATING: continue
      neigh = sorted(target.neighbours, key=lambda x: x.droids, reverse=True)
      self.trySendDroids(plan, neigh[0], target, SUPPORT)