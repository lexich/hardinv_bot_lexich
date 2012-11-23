#!/usr/bin/env python
# -*- coding: utf-8 -*-
from game import Game
import sys
from lib.signals import InterruptGame


__author__ = 'lexich'


class TestGame(Game):
  testMode = True

  def __init__(self, *args, **kwargs):
    self.testStep = 0
    import os
    import random

    root, folders, files = os.walk("log").next()
    folders.sort()
    self.findFolder = folders[random.randint(0, len(folders) - 1)]
    #self.findFolder = "2012-11-23-14-56-46"
    super(TestGame, self).__init__(*args, **kwargs)
    print "FOLDER:%s" % self.findFolder

  def connect(self):
    pass

  def close(self):
    pass

  def _recv(self):
    try:
      filepath = "log/%s/%s_recv.xml" % (self.findFolder, self.testStep)
      self.testStep += 1
      with open(filepath, "r") as f:
        print "read: %s" % filepath
        return f.read()
    except IOError, e:
      raise InterruptGame

  def _send(self, data):
    pass

  def handle(self, planets, request):
    result = super(TestGame, self).handle(planets, request)
    return result


params = (
  "hardinv.ru",
  10040,
  "h2oz5rnaepbcvn1uuq2elkvaw63nhpv1",
  "lexich"
  )

if __name__ == "__main__":
  if len(sys.argv) > 1 and sys.argv[1] == "--visual":
    from lib.visualize import BaseInteractorStyle, Visualize, vtk

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
        self.g = VisualizeGame(*params)


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

      def algoritm(self, planets,request, g, G_labels, E_labels, G, E):
        """

        """
        minCount = min(
          map(lambda x: len(x.neighbours), planets)
        ) if len(planets) > 0 else 0
        if not minCount: return
        minPlanets, otherPlanets = [], []
        for planet in planets:
          iter = minPlanets if len(planet.neighbours) == minCount else otherPlanets
          iter.append(planet)
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
          label = "{0}({1}:{4}) - {2}d.\n{3}".format(planet.type,planet.owner,planet.droids,label,planet.id)
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


    vis = Visualize(CustomBaseInteractorStyle)
    vis.start()

  if len(sys.argv) > 1 and sys.argv[1] == "--test":
    g = TestGame(*params)
    g.run()
  else:
    g = Game(*params)
    g.run()
