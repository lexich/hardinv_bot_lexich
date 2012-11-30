#!/usr/bin/env python
# -*- coding: utf-8 -*-
from exceptions import IOError
from game import Game
from lib.client import Logger
from lib.signals import InterruptGame
import os
__author__ = 'lexich'

class TestGame(Game):
  testMode = True

  def get_folder(self,folders,name=None,rnd=None):
    import random
    if name:
      return name
    elif rnd:
      return folders[random.randint(0, len(folders) - 1)]
    else:
      return  folders[len(folders) - 1]

  def __init__(self, *args, **kwargs):
    self.testStep = 0
    super(TestGame, self).__init__(*args, **kwargs)
    path = os.path.join(Logger.ROOT_DIR, self.host)
    if not os.path.exists(path):
      raise InterruptGame("no root folder")
    root, folders, files = os.walk(path).next()
    folders.sort()
    if len(folders) <= 0:
      raise InterruptGame("no folders to read")
    while len(folders) > 0:
      path = os.path.join(path, self.get_folder(folders))
      root, folders, files = os.walk(path).next()
    self.findFolder = path
    print "FOLDER:%s" % self.findFolder

  def connect(self):
    pass

  def close(self):
    pass

  def _recv(self):
    try:
      filepath = os.path.join(self.findFolder, "%s_recv.xml" %  self.testStep)
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