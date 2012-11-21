from exceptions import ValueError

__author__ = 'lexich'

class DomEl(object):
  def __init__(self, el):
    self._el = el

  @property
  def el(self):
    return super(DomEl, self).__getattribute__("_el")

  @property
  def to_int(self):
    try:
      return int(self.val)
    except ValueError, e:
      return 0

  @property
  def val(self):
    return self.el.firstChild.nodeValue if self.el.firstChild else None

  def attr(self, name):
    return self.el.attributes.get(name).value

  @property
  def planets(self):
    return [DomEl(x) for x in self.el.getElementsByTagName("planet")]

  @property
  def neighbours(self):
    return [DomEl(x).val for x in self.el.getElementsByTagName("neighbour")]

  @property
  def errors(self):
    return [DomEl(x).val for x in self.el.getElementsByTagName("error")]

  def __getattribute__(self, name):
    if type(self).__dict__.has_key(name):
      return super(DomEl, self).__getattribute__(name)
    else:
      resp = self.el.getElementsByTagName(name)
      return DomEl(resp[0]) if len(resp) == 1 else self