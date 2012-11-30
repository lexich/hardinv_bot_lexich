#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from optparse import OptionParser

__author__ = 'lexich'

DEFAULT_TOKEN = "h2oz5rnaepbcvn1uuq2elkvaw63nhpv1"
DEFAULT_USER = "lexich"
DEFAULT_HOST = "hardinv.ru"
DEFAULT_PORT = 10040

if __name__ == "__main__":
  p = OptionParser()
  p.add_option("--test", dest="test", action="store_true", default=False, help="Console test mode")
  p.add_option("--visual", dest="visual", action="store_true", default=False, help="Visual vtk test mode")
  p.add_option("--host", dest="host", metavar="HOST", default=DEFAULT_HOST, help="Host")
  p.add_option("-p", "--port", dest="port", type="int", metavar="PORT", default=DEFAULT_PORT, help="Port")
  p.add_option("-u", "--user", dest="user", metavar="USERNAME", default=DEFAULT_USER, help="User")
  p.add_option("-t", "--token", dest="token", metavar="TOKEN", default=DEFAULT_TOKEN, help="Token")
  (options, args) = p.parse_args()

  params = (
    options.host,
    options.port,
    options.token,
    options.user
    )

  if options.visual:
    from test.visualtest import Visualize, CustomBaseInteractorStyle, VisualizeGame

    vis = Visualize(CustomBaseInteractorStyle)
    vis.start(VisualizeGame(*params))
  elif options.test:
    from test.test import TestGame

    g = TestGame(*params)
    g.start()
  else:
    from game import Game
    g = Game(*params)
    g.start()
