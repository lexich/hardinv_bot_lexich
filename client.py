#!/usr/bin/env python
# -*- coding: utf-8 -*-
import socket
from datetime import datetime
from lib import Planet, Request
import xmltodict
import os

def log(txt):
  print txt


class Logger(object):
  def __init__(self):
    if not os.path.exists("log"):
      os.mkdir("log")
    self.log_dir = os.path.join("log", datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))
    os.mkdir(self.log_dir)

  def write(self, data, type, count):
    filename = os.path.join(self.log_dir, "{1}_{0}.xml".format(type, count))
    with open(filename, "w") as f:
      f.write(u"%s" % data)


class ClientBase(object):
  BUFFER_SIZE = 1024

  def __init__(self, host, port):
    self.host = host
    self.port = port
    self.s = socket.socket(
      socket.AF_INET,
      socket.SOCK_STREAM
    )
    self.s.connect((self.host, self.port))
    self.log = Logger()
    self.step = 0


  def close(self):
    self.s.close()

  def _send(self, data):
    sendData = 0
    while sendData < len(data):
      sendData += self.s.send(data)
    self.log.write(data, "send", self.step)

  def _recv(self):
    data = ""
    chunk = ""
    while chunk=="":
      chunk = self.s.recv(self.BUFFER_SIZE)
      data += chunk
      if data == "":
        continue
      if len(chunk) < self.BUFFER_SIZE:
        break
    self.log.write(data, "recv", self.step)
    return data

  def recv(self):
    data = self._recv()
    return xmltodict.parse(data)

  def send(self, obj):
    data = xmltodict.unparse(obj)
    return self._send(data)

  def handle(self, obj, request):
    raise NotImplemented("Need to implement")


class Client(ClientBase):
  def __init__(self, host, port, token, user):
    super(Client, self).__init__(host, port)
    self.token = token
    self.user = user

  def auth(self):
    auth = {
      "request": {
        "token": self.token,
        "actions": " "
      }
    }
    self.send(auth)
    return self.recv()

  def run(self):
    log("Begin game")
    response = None
    while True:
      response = self.auth()["response"]
      if not response['errors']:
        break
    log("Begin Gane")
    while True:
      self.step += 1
      planets = []
      planets = map(lambda planet: Planet(planet, planets, self.user), response["planets"])
      request = Request(self.token)
      self.handle(planets, request)
      self.send(request)
      response = self.recv()["response"]
