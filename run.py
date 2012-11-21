#!/usr/bin/env python
# -*- coding: utf-8 -*-
from game import Game
import sys
from lib.signals import InterruptGame


__author__ = 'lexich'


class TestGame(Game):
  PATTERN = "2012-11-21-02-03-13"
  def __init__(self,*args,**kwargs):
    self.testStep = 0
    super(TestGame,self).__init__(*args,**kwargs)
  def connect(self):
    pass

  def close(self):
    pass

  def _recv(self):
    try:
      filepath = "log/%s/%s_recv.xml" %(self.PATTERN, self.testStep)
      self.testStep += 1
      with open(filepath,"r") as f:
        return f.read()
    except IOError,e:
      raise InterruptGame

  def _send(self, data):
    pass

  def handle(self, planets, request):
    result = super(TestGame,self).handle(planets,request)
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


