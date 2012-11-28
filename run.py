#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
__author__ = 'lexich'

params = (
  "hardinv.ru",
  10040,
  "h2oz5rnaepbcvn1uuq2elkvaw63nhpv1",
  "lexich"
  )

if __name__ == "__main__":
  if len(sys.argv) > 1 and sys.argv[1] == "--visual":
    from runner.visualtest import Visualize, CustomBaseInteractorStyle,VisualizeGame
    vis = Visualize(CustomBaseInteractorStyle)
    vis.start(VisualizeGame(*params))
  if len(sys.argv) > 1 and sys.argv[1] == "--test":
    from runner.test import TestGame
    g = TestGame(*params)
    g.start()
  else:
    from game import Game
    g = Game(*params)
    g.start()
