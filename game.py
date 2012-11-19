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
            "planets":[],
            "maxAttack":0,
          }
        myPlanetNeighbours[n.id]["planets"].append(
          planets[p.id]
        )
    for id, info in myPlanetNeighbours:
      for p in info["planets"]:
        info["maxAttack"] += p.droids








g = Game("hardinv.ru", 10040, "h2oz5rnaepbcvn1uuq2elkvaw63nhpv1", "lexich")
g.run()