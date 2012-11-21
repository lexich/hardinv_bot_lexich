#!/usr/bin/env python
# -*- coding: utf-8 -*-
from lib.client import Client


__author__ = 'lexich'


class Game(Client):
  def rating(self, info):
    planet = info["planet"]
    if not planet.is_enemy:
      return planet.growRating(x=planet.droids)
    else:
      delta = info["maxAttack"] - planet.danger
      return planet.growRating(x=delta)


  def _analyseNeighbours(self, myPlanets, planets):
    planetNeighbours = {
      "my": {},
      "enemy": {},
      "empty": {}
    }
    for p in myPlanets:
      for n in p.neighbours:
        #Классифицируем тип соседей
        if n.is_free:
          iterNeighbours = planetNeighbours["empty"]
        elif n.is_enemy:
          iterNeighbours = planetNeighbours["enemy"]
        else:
          iterNeighbours = planetNeighbours["my"]

        #Формируем макет статистики
        if not iterNeighbours.has_key(n.id):
          iterNeighbours[n.id] = {
            "myPlanets": [],
            "maxAttack": 0,
            "rating": 0,
            "id": n.id,
            "planet": n,
            }
          #Заполняем статистику
        iterNeighbours[n.id]["myPlanets"].append(
          planets.get(p.id)
        )
    return planetNeighbours


  SEND_TO_EMPTY_DEFAULT = 15
  MY_PLANET_NEED_HELP_RATING = 5
  MY_PLANET_CAN_HELP_RATING = 2
  MY_PLANET_MUST_HELP_RATING = 2

  def _helpMyPlanets(self, planetNeighbours, request):
    #Перераспределим своих дройдов по своим планетам
    for id, myPlanet in planetNeighbours["my"].iteritems():
      my = myPlanet["planet"]

      #Проверяем может ли планета помочь соседям
      myGrowRating = my.growRating(my.droids)
      if myGrowRating > self.MY_PLANET_CAN_HELP_RATING:
        continue
        #Если может пытаемся понять кому
      maxSend = my.droids * my.percent

      #Если есть куда расти
      if myGrowRating > self.MY_PLANET_MUST_HELP_RATING:
        myPlanetsNeedHelp = filter(
          lambda p: p.growRating(p.droids) < self.MY_PLANET_NEED_HELP_RATING,
          myPlanet["myPlanets"]
        )
      #Иначе раздаем всем с рейтингом меньше максимального
      else:
        myPlanetsNeedHelp = filter(
          lambda p: p.growRating(p.droids) < self.MY_PLANET_MUST_HELP_RATING,
          myPlanet["myPlanets"]
        )
      for p in myPlanetsNeedHelp:
        request.add(id, p.id, my.sendDroids(
          maxSend / len(myPlanetsNeedHelp)
        ))

  def handle(self, planets, request):
    myPlanets = []
    enemyPlanets = []
    emptyPlanets = []
    for id, p in planets.items():
      if p.is_enemy:
        enemyPlanets.append(p)
      elif p.is_free:
        emptyPlanets.append(p)
      else:
        myPlanets.append(p)

    #Проверяем окончание игры
    if not len(myPlanets):
      raise GameOver()
    elif len(myPlanets) == len(planets.values()):
      raise Win()

    planetNeighbours = self._analyseNeighbours(myPlanets, planets)
    #На пустую планету отправим дройдов для закрепления
    #делаем это заранее чтобы результаты не так сильно влияли на статистику
    for id, emptyPlanet in planetNeighbours["empty"].iteritems():
      my = emptyPlanet["myPlanets"]
      for p in my:
        request.add(p.id, id, p.sendDroids(
          self.SEND_TO_EMPTY_DEFAULT / len(my)
        ))

    self._helpMyPlanets(planetNeighbours, request)
    #Начинаем атаковать

    fullRating = 0
    for id, info in planetNeighbours["enemy"].iteritems():
      for p in info["myPlanets"]:
        info["maxAttack"] += p.attack
      info["rating"] = self.rating(info)
      fullRating += info["rating"]

    attackPlanets = sorted(
      planetNeighbours["enemy"].iteritems(),
      key=lambda item: (item[1]["rating"], item[1]),
      reverse=True
    )

    if len(attackPlanets) > 0:
      id, attack = attackPlanets[0]
      for p in attack["myPlanets"]:
        request.add(p.id, attack["id"], p.sendDroids(
          p.attack
        ))
