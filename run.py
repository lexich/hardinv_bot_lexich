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
  if len(sys.argv) > 1 and sys.argv[1] == "--test":
    g = TestGame(*params)
    g.run()
  else:
    g = Game(*params)
    g.run()
