#!/usr/bin/env python
# -*- coding: utf-8 -*-
from lib.visualize import BaseInteractorStyle, Visualize, vtk
from runner.test import TestGame

class VisualizeGame(TestGame):
  def __init__(self, *args, **kwargs):
    self.response = None
    super(VisualizeGame, self).__init__(*args, **kwargs)

  def handle(self, planets, request):
    super(VisualizeGame,self).handle(planets,request)
    self.planets = planets
    self.request = request


  def run(self):
    if not self.response:
      self.response = self.auth()
    self.response = self._parceResponce(self.response)

class CustomBaseInteractorStyle(BaseInteractorStyle):
  def __init__(self, parent=None):
    BaseInteractorStyle.__init__(self, parent)

  def leftButtonPressEvent(self, obj, event):
    self.g.testStep -=2
    if self.g.testStep < 0:
      self.g.testStep = 0
    self.rightButtonPressEvent(obj,event)

  def rightButtonPressEvent(self, obj, event):
    self.g.run()
    self.ref.addRepresentation(self.init)

  def init(self):
    g = vtk.vtkMutableDirectedGraph()
    planets = self.g.planets
    request = self.g.request
    G, E = {}, {}
    G_labels = vtk.vtkStringArray()
    G_labels.SetName("VLabels")
    E_labels = vtk.vtkStringArray()
    E_labels.SetName("ELabels")

    self.algoritm(planets.values(), request, g, G_labels, E_labels, G, E)
    g.GetVertexData().AddArray(G_labels)
    g.GetEdgeData().AddArray(E_labels)
    return g

  def _cmp_my_user(self,x,y):
    if x.owner == self.g.user:
      return -1
    elif y.owner == self.g.user:
      return 1
    else:
      return 0

  def algoritm(self, planets,request, g, G_labels, E_labels, G, E):
    minCount = min(
      map(lambda x: len(x.neighbours), planets)
    ) if len(planets) > 0 else 0
    if not minCount: return
    minPlanets, otherPlanets = [], []
    for planet in planets:
      iter = minPlanets if len(planet.neighbours) == minCount else otherPlanets
      iter.append(planet)
    minPlanets.sort(cmp=self._cmp_my_user)
    self.createVertex(minPlanets, g, G, E, G_labels)
    self.createEdges(minPlanets,request, g, G, E, E_labels)
    self.algoritm(otherPlanets,request, g, G_labels, E_labels, G, E)

  def createVertex(self, planets, g, G, E, G_labels):
    for planet in planets:
      if G.has_key(planet.id): continue
      G[planet.id] = g.AddVertex()
      params = {
        "attack":planet.attack,
        "danger":planet.danger,
        "growRating":planet.growRating(planet.droids),
        "neighboursDanger":planet.neighboursDanger(),
        "is_dead":planet.is_dead(),
      }
      label = "\n".join(["%s - %s" % tuple(x) for x in params.iteritems()])
      label = "{1} - ({0}:{4}) - {2}d.\n{3}".format(planet.type,planet.owner,planet.droids,label,planet.id)
      G_labels.InsertNextValue(label)
      E[planet.id] = set()


  def createEdges(self, planets,request, g, G, E, E_labels):
    for planet in planets:
      for neig in planet.neighbours:
        if not G.has_key(neig.id): continue
        if planet.id in E[neig.id]: continue
        g.AddGraphEdge(G[planet.id], G[neig.id])
        reqDebug = request.debug.get(planet.id,{}).get(neig.id,None)
        label = "\n".join(["%s - %s" % tuple(x) for x in reqDebug.iteritems()]) if reqDebug else ""
        E_labels.InsertNextValue(label)
        E[neig.id].add(planet.id)
        E[planet.id].add(neig.id)