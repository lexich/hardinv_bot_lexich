__author__ = 'lexich'

import vtk




class BaseInteractorStyle(vtk.vtkInteractorStyleRubberBand2D):
  def __init__(self, parent=None):
    self.AddObserver("KeyPressEvent", self.keyPressEvent)
    self.counter = 0

  def setRef(self, ref):
    self.ref = ref
    self.graphLayoutView = self.ref.graphLayoutView
    self.representation = self.ref.representation
    self.interactor = self.graphLayoutView.GetInteractor()

  def keyPressEvent(self, obj, event):
    key = self.interactor.GetKeySym()
    if key == "Right":
      self.rightButtonPressEvent(obj, event)
    elif key == "Left":
      self.leftButtonPressEvent(obj, event)

  def rightButtonPressEvent(self, obj, event):
    print "left"

  def leftButtonPressEvent(self, obj, event):
    print "right"


class Visualize(object):
  def __init__(self, clsInteractor):
    self.clsInteractor = clsInteractor
    self.graphLayoutView = vtk.vtkGraphLayoutView()
    self.representation = None

  def addRepresentation(self, func):
    if self.representation:
      self.graphLayoutView.RemoveRepresentation(self.representation)
    funcRes = func()
    self.representation = self.graphLayoutView.AddRepresentationFromInput(funcRes)
    self.graphLayoutView.SetLayoutStrategy("Simple 2D")
    self.graphLayoutView.GetLayoutStrategy().SetRandomSeed(3)
    self.graphLayoutView.GetLayoutStrategy().SetEdgeWeightField("Weights")
    self.graphLayoutView.GetLayoutStrategy().SetWeightEdges(1)
    self.graphLayoutView.SetEdgeLabelArrayName("ELabels")
    self.graphLayoutView.SetEdgeLabelVisibility(1)
    self.graphLayoutView.SetVertexLabelArrayName("VLabels")
    self.graphLayoutView.SetVertexLabelVisibility(1)
    self.graphLayoutView.ResetCamera()
    self.graphLayoutView.Render()


  def start(self):
    self.irenStyle = self.clsInteractor()
    self.irenStyle.setRef(self)
    self.addRepresentation(vtk.vtkMutableDirectedGraph)
    interactor = self.graphLayoutView.GetInteractor()
    interactor.SetInteractorStyle(self.irenStyle)
    interactor.Start()

if __name__ == "__main__":
  vis = Visualize(BaseInteractorStyle)
  vis.start()