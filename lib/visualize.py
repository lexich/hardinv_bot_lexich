__author__ = 'lexich'

import vtk

class BaseInteractorStyle(vtk.vtkInteractorStyleRubberBand2D):
  def __init__(self, parent=None):
    self.AddObserver("KeyPressEvent", self.keyPressEvent)
    self.counter = 0
    self.g = None

  def setGame(self,game):
    self.g = game

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

    self.graphLayoutView.SetVertexColorArrayName("vertex_degree_centrality")
    self.graphLayoutView.SetColorVertices(True)

    theme = vtk.vtkViewTheme.CreateMellowTheme()
    theme.SetLineWidth(2)
    theme.SetPointSize(10)
    theme.SetCellOpacity(1)
    theme.SetSelectedCellColor(1,0,1)
    self.graphLayoutView.ApplyViewTheme(theme)

    theme.FastDelete()
    self.graphLayoutView.GetRenderWindow().SetSize(1366, 700)

    self.graphLayoutView.SetVertexLabelFontSize(9)
    self.graphLayoutView.SetEdgeLabelFontSize(9)

    self.graphLayoutView.ResetCamera()
    self.graphLayoutView.Render()

  def _init(self):
    g = vtk.vtkMutableDirectedGraph()
    v1 = g.AddVertex()
    v2 = g.AddVertex()
    g.AddGraphEdge(v1,v2)
    G_labels = vtk.vtkStringArray()
    G_labels.SetName("VLabels")
    G_labels.InsertNextValue("One")
    G_labels.InsertNextValue("Two")
    g.GetVertexData().AddArray(G_labels)
    G_labels = vtk.vtkStringArray()
    G_labels.SetName("VLabels")
    G_labels.InsertNextValue("Three")
    G_labels.InsertNextValue("Four")
    g.GetVertexData().AddArray(G_labels)
    return g

  def start(self, game):
    self.irenStyle = self.clsInteractor()
    self.irenStyle.setRef(self)
    self.irenStyle.setGame(game)
    self.addRepresentation(self._init)
    interactor = self.graphLayoutView.GetInteractor()
    interactor.SetInteractorStyle(self.irenStyle)
    interactor.Start()
