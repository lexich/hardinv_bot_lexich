#!/usr/bin/env python
# -*- coding: utf-8 -*-
from client import Client

__author__ = 'lexich'


class Game(Client):
  def handle(self, planets, request):
    myPlanets = filter(lambda n: n.owner == self.user, planets)
    myPlanetNeighbours = {}
    for p in myPlanets:
      for n in p.neighbours:
        if not myPlanetNeighbours[n.id]:
          myPlanetNeighbours[n.id] = {
            "myPlanets":[],
            "maxAttack":0,
            "danger":0,
            "rating":0,
            "id":n.id
          }
        myPlanetNeighbours[n.id]["myPlanets"].append(
          planets[p.id]
        )
    for id, info in myPlanetNeighbours:
      info["danger"] = planets[id].danger
      for p in info["planets"]:
        info["maxAttack"] += p.droids
      info["rating"] = info["maxAttack"] - info["danger"]
    attackPlanets = sorted(myPlanetNeighbours.iteritems(), key=lambda item: (item[1]["rating"],item[1]), reverse=True)
    attack = attackPlanets[0]

    for myPlanet in attack[myPlanets]:
      request.add(myPlanet.id, attack.id, myPlanet.droids)


g = Game("hardinv.ru", 10040, "h2oz5rnaepbcvn1uuq2elkvaw63nhpv1", "lexich")
g.run()