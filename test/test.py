#!/usr/bin/env python
# -*- coding: utf-8 -*-
from exceptions import IOError
from game import Game
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
    #self.findFolder = folders[random.randint(0, len(folders) - 1)]
    self.findFolder = folders[len(folders) - 1]
    #self.findFolder = "2012-11-26-11-55-32"
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