# -*- coding: utf-8 -*-
import math

__author__ = 'lexich'


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
  #Рейтинг показывает удовлетворительную
  #скорость прироста дройдов, которая вычисляется speedGrowRating
  SPEED_GROW_RATING = 0.3
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
    self._fast_stategy = False

  def set_fast_strategy(self):
    self._fast_stategy = True

  def is_fast_strategy(self):
    return self._fast_stategy

  def __unicode__(self):
    return "%s %s" % (self.user, self.id)

  @cache
  def get_neighbours(self):
    return map(lambda id: self.planets[id], self._neighbours)

  @property
  def neighbours(self):
    return self.get_neighbours()

  def speedGrowRating(self):
    return self.droids / self.limit

  def fullNeighboursDanger(self, equalValue=0, level=0, exclude=set()):
    """
    Ближайший уровень опасности
    """
    #если элемент уже исследовался, пропускаем
    if self.id in exclude:
      return 0
    exclude.add(self.id)
    danger = self.neighboursDanger()
    #Если у соседей нулевой уровень опасности
    #И параметр сравнения нулевой, то ищем на следующием уровне
    #(иначе можно дальше не искать)
    if danger <= 0 and equalValue <= 0:
      for n in self.get_neighbours():
        danger = max(danger, n.neighboursDanger())
        #Если у соседей опасность не найдена ищем дальше рекурсивно
      if danger <= 0:
        for n in self.get_neighbours():
          danger = max(danger, n.fullNeighboursDanger(danger, level + 1, exclude))
    return danger / 10.0 ** level

  @cache
  def neighboursMyself(self):
    """
    Возвращаем только соседей друзей
    """
    return filter(
      lambda x: x.is_myself,
      self.neighbours
    )

  @cache
  def maxMyselfNeighboursAttack(self):
    search = map(
      lambda n: n.attack,
      self.neighboursMyself()
    )
    return max(search) if len(search) > 0 else 0

  @cache
  def neighboursDanger(self):
    """
    Уровень опасности у окружающих соседей
    """
    search = map(
      lambda x: x.get_danger(),
      self.get_neighbours()
    )
    return max(search) if len(search) > 0 else 0

  @cache
  def is_dead(self):
    dangerResist = 0.7
    if not self.is_myself:
      myAttack = sum(map(lambda x:x.droids, self.neighboursMyself()))
      return myAttack < self.danger * dangerResist
    else:
      return self.droids + self.maxMyselfNeighboursAttack() < self.danger * dangerResist

  @cache
  def get_danger_rating(self):
    rating = {}
    if self.is_enemy:
      rating[self.owner] = self.droids

    for n in self.neighbours:
      if not n.is_enemy: continue
      if not rating.has_key(n.owner):
        rating[n.owner] = 0
      rating[n.owner] += n.droids
    return rating

  @cache
  def get_danger(self):
    rating = self.get_danger_rating()
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
    attack = 0
    rating = self.growRating(self.droids)
    if rating < self.RATING_ATTACK:
      attack = int(self.droids * self.percent)
      if self.danger > self.droids - attack:
        attack = self.droids - self.danger
    if attack < 0:
      attack = 0
    return attack

  @property
  def is_myself(self):
    return self.owner == self.user

  @property
  def is_free(self):
    return self.owner is None

  @property
  def is_enemy(self):
    return not self.is_free and self.owner != self.user

  @cache
  def findMyNearsPlanets(self):
    "Найти мои ближайшие планеты"
    result = self.recurciveFindMyNearsPlanets(self)
    return result if result  else None

  def recurciveFindMyNearsPlanets(self, planet, roadLong=0, roadLimit=0, exclude=set()):
    if roadLimit > 0 and roadLimit < roadLong:
      return None
    myPlanets = planet.neighboursMyself() or []
    if len(myPlanets) <= 0:
      #Добавим фильтр
      new_exclude = exclude.copy()
      new_exclude.update(planet.neighbours)
      new_exclude.add(planet)
      #Начинаем рекурсивный поиск
      for p in planet.neighbours:
        if p in exclude: continue
        result = self.recurciveFindMyNearsPlanets(p, roadLong + 1, roadLimit, new_exclude)
        if result and (roadLimit == 0 or result[0] < roadLimit):
          roadLimit, myPlanets = result
    return (roadLong, myPlanets) if len(myPlanets) > 0 else None


  def searchPathToTarget(self, targetPlanet, roadLong=0, roadLimit=0, _exclude=None):
    """
    Найти соседнюю планету с коротой лучше начать путь до цели
    Достаточно дорогая операция, максимально оптимизаровать результаты
    """
    if not _exclude:
      _exclude = set()
    #Если найден путь более короткий, данное решение игнорируем
    if roadLimit > 0 and roadLong >= roadLimit:
      return
    #Исключаем петли

    searchNeighbours = filter(lambda x:x==targetPlanet, self.neighbours)
    if len(searchNeighbours) > 0:
      return roadLong,searchNeighbours[0]

    if self.id in _exclude:
      return None
    _exclude.add(self.id)

    #Продолжаем рекурсивный поиск
    searchPath = None
    for p in self.neighbours:
      if p.id in _exclude: continue
      result = p.searchPathToTarget(targetPlanet, roadLong + 1, roadLimit, set(_exclude))
      if result and (roadLimit==0 or roadLimit > result[0]):
        roadLimit = result[0]
        searchPath = p
    return roadLimit, searchPath

  @property
  def percent(self):
    property = self.PROPERTY.get(self.type, {})
    return property.get("p", 0)

  @property
  def limit(self):
    property = self.PROPERTY.get(self.type, {})
    return property.get("limit", 0)


