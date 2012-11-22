__author__ = 'lexich'

import vtk


def init(label):
  g = vtk.vtkMutableDirectedGraph()

  # Create 3 vertices
  v1 = g.AddVertex()
  v2 = g.AddVertex()
  v3 = g.AddVertex()
  v4 = g.AddVertex()

  # Create a fully connected graph
  g.AddGraphEdge(v1, v2)
  g.AddGraphEdge(v2, v3)
  g.AddGraphEdge(v1, v3)
  g.AddGraphEdge(v2, v4)

  # Create the edge weight array
  weights = vtk.vtkDoubleArray()
  weights.SetNumberOfComponents(1)
  weights.SetName("Weights")

  # Set the edge weights
  weights.InsertNextValue(1.0)
  weights.InsertNextValue(1.0)
  weights.InsertNextValue(2.0)
  weights.InsertNextValue(2.0)


  # Add the edge weight array to the graph
  g.GetEdgeData().AddArray(weights);

  labels = vtk.vtkStringArray()
  labels.SetName("Labels")
  labels.InsertNextValue("One" + label)
  labels.InsertNextValue("Two" + label)
  labels.InsertNextValue("Three" + label)
  labels.InsertNextValue("Four" + label)

  g.GetVertexData().AddArray(labels)
  return g


class BaseInteractorStyle(vtk.vtkInteractorStyleRubberBand2D):
  def __init__(self, parent=None):
    self.AddObserver("RightButtonPressEvent", self.rightButtonPressEvent)
    self.AddObserver("LeftButtonPressEvent", self.leftButtonPressEvent)
    self.counter = 0
  def setRef(self,ref):
    self.ref = ref

  def rightButtonPressEvent(self, obj, event):
    print "left"
  def leftButtonPressEvent(self, obj, event):
    label = "1exich%s" % self.counter
    self.ref.addRepresentation(lambda : init(label))
    self.counter += 1
    print label

    print "right"



class Visualize(object):
  def __init__(self,clsInteractor):
    self.clsInteractor = clsInteractor
    self.graphLayoutView = vtk.vtkGraphLayoutView()
    self.representation = None

  def addRepresentation(self, func):
    if self.representation:
      self.graphLayoutView.RemoveRepresentation(self.representation)
    self.representation = self.graphLayoutView.AddRepresentationFromInput(func())
    self.graphLayoutView.SetLayoutStrategy("Simple 2D")
    self.graphLayoutView.GetLayoutStrategy().SetEdgeWeightField("Weights")
    self.graphLayoutView.GetLayoutStrategy().SetWeightEdges(1)
    self.graphLayoutView.SetEdgeLabelArrayName("Weights")
    self.graphLayoutView.SetEdgeLabelVisibility(1)

    self.graphLayoutView.SetVertexLabelArrayName("Labels")
    self.graphLayoutView.SetVertexLabelVisibility(1)
    self.graphLayoutView.ResetCamera()
    self.graphLayoutView.Render()
    self.graphLayoutView.GetLayoutStrategy().SetRandomSeed(0)

  def start(self):
    self.addRepresentation( lambda : init("default"))

    interactor = self.graphLayoutView.GetInteractor()
    irenStyle = self.clsInteractor()
    irenStyle.setRef(self)
    interactor.SetInteractorStyle(irenStyle)
    interactor.Start()

if __name__ == "__main__":
  vis = Visualize(BaseInteractorStyle)
  vis.start()