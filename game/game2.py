# -*- coding: utf-8 -*-
from lib.client import Client
from lib.lib import Win, GameOver

__author__ = 'lexich'


class Game(Client):
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
        self.trySendDroids(plan, p, p.neighbours[0], "rush")
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

  def fixPosition(self, myPlanets, neighbours, planets, request, plan):
    ratingFilter = 2
    for id, target in neighbours["my"].iteritems():
      mySourcesPlanets = filter(
        lambda p: p.is_myself,
        target.neighbours
      )
      for src in mySourcesPlanets:
        if src.growRating(src.droids) > ratingFilter:
          continue
        if src.growRating(src.droids) > target.growRating(target.droids):
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
        self.trySendDroids(plan, src, target, "patient")

  def trySendDroids(self, plan, _from, _to, _strategy="patient"):
    """
    strategy ['all','rush','explorer','patient' ]
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


  def executePlan(self, myPlanets, neighbours, planets, request, plan):
    all = plan["strategy"].get("all",[])
    for item in all:
      _from, _to, strategy = item
      request.add(_from.id,_to.id, _from.sendDroids(_from.droids))

    rush = plan["strategy"].get("rush",[])
    for item in rush:
      _from, _to, strategy = item
      #Заполненность планеты
      k = _from.growRating(_from.droids)/_from.growRating(10)
      #если заполненность меньше половины, отказываемся
      if k > 0.5: continue
      maxResist = _to.danger
      #Атака 70% дройдов
      attackDroids = _from.droids * 0.7
      #Если атака больше 90%
      if attackDroids > maxResist * 0.9:
        request.add(_from.id,_to.id, _from.sendDroids(attackDroids))

    explorer = sorted(
      plan["strategy"].get("explorer",[]),
      key=lambda x:x[1].growRating()
    )
    explorerAttack = 15
    explorerRating = 7
    for item in explorer:
      _from, _to, strategy = item
      if _from.limit < _to.limit:
        request.add(_from.id,_to.id, _from.sendDroids(_from.droids))
      elif _from.attack > explorerAttack and \
           _from.growRating(_from.droids) < explorerRating:
        request.add(_from.id,_to.id, _from.sendDroids(explorerAttack))

    patient = plan["strategy"].get("patient",[])
    for item in patient:
      _from, _to, strategy = item
      to_plan = plan["to"].get(_to,[])
      maxAttack = sum(map(
        lambda item:item[0].attack, to_plan
      )) if len(to_plan) > 0 else 0
      #Если атака меньше 90% то отказываемся
      if maxAttack < _to.danger * 0.9:
        #Но если планета заполнена атакуем в любом случае
        if _from.growRating(_from.droids) < 3:
          request.add(_from.id, _to.id, _from.sendDroids(_from.attack))
      else:
        for from_item in to_plan:
          src = from_item[0]
          request.add(src.id, _to.id, src.sendDroids(src.attack))

