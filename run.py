#!/usr/bin/env python
# -*- coding: utf-8 -*-
from game import Game
import sys
__author__ = 'lexich'


class TestGame(Game):
  TEST = True
  def connect(self):
    pass

  def close(self):
    pass

  def _recv(self):
    with open("log/2012-11-20-22-19-46/25_recv.xml") as f:
      return f.read()

  def _send(self, data):
    pass


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
