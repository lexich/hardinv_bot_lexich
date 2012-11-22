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
    self.findFolder = folders[random.randint(0, len(folders) - 1)]
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
        pass

      def rightButtonPressEvent(self, obj, event):
        self.g.run()
        self.ref.addRepresentation(self.init)

      def init(self):
        g = vtk.vtkMutableDirectedGraph()
        planets = self.g.planets
        request = self.g.request
        G = {}
        G_labels = vtk.vtkStringArray()
        G_labels.SetName("Labels")

        E = {}
        for id,planet in planets.iteritems():
          G[id] = {
            "vert":g.addVertex(),
          }
          G_labels.InsertNextValue("owner:{0}\ndroids:{1}, type:{2}"%[
            planet.owner, planet.droids, planet.type
          ])

        for id,planet in planets.iteritems():
          for n in planet.get_neighbours():
            pair = [id,n.id].sort()
            _hash = "%s%s" % pair
            E[_hash] = {
              "edge":g.AddGraphEdge(
                G[pair[0]]["vert"],
                G[pair[1]]["vert"]
              ),
              "pair":pair
            }
        g.GetVertexData().AddArray(G_labels)
        return g
    vis = Visualize(CustomBaseInteractorStyle)
    vis.start()



  if len(sys.argv) > 1 and sys.argv[1] == "--test":
    g = TestGame(*params)
    g.run()
  else:
    g = Game(*params)
    g.run()
