from exceptions import Exception

__author__ = 'lexich'

class Win(Exception):
  pass


class GameOver(Exception):
  pass


class InterruptGame(Exception):
  pass