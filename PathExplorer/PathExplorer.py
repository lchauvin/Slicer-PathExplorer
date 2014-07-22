import os
import unittest
from __main__ import vtk, qt, ctk, slicer
import CurveMaker

#
# PathExplorer
#

class PathExplorer:
  def __init__(self, parent):
    parent.title = "PathExplorer" # TODO make this more human readable by adding spaces
    parent.categories = ["Examples"]
    parent.dependencies = []
    parent.contributors = ["Laurent Chauvin (BWH)"] # replace with "Firstname Lastname (Organization)"
    parent.helpText = """
    This is an example of scripted loadable module bundled in an extension.
    """
    parent.acknowledgementText = """
    This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
    and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.
    self.parent = parent

    # Add this test to the SelfTest module's list for discovery when the module
    # is created.  Since this module may be discovered before SelfTests itself,
    # create the list if it doesn't already exist.
    try:
      slicer.selfTests
    except AttributeError:
      slicer.selfTests = {}
    slicer.selfTests['PathExplorer'] = self.runTest

  def runTest(self):
    tester = PathExplorerTest()
    tester.runTest()

#
# PathExplorerWidget
#

class PathExplorerWidget:
  def __init__(self, parent = None):
    if not parent:
      self.parent = slicer.qMRMLWidget()
      self.parent.setLayout(qt.QVBoxLayout())
      self.parent.setMRMLScene(slicer.mrmlScene)
    else:
      self.parent = parent
    self.layout = self.parent.layout()
    if not parent:
      self.setup()
      self.parent.show()

  def setup(self):
    # Instantiate and connect widgets ...

    #
    # Reload and Test area
    #
    reloadCollapsibleButton = ctk.ctkCollapsibleButton()
    reloadCollapsibleButton.text = "Reload && Test"
    self.layout.addWidget(reloadCollapsibleButton)
    reloadFormLayout = qt.QFormLayout(reloadCollapsibleButton)

    # reload button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadButton = qt.QPushButton("Reload")
    self.reloadButton.toolTip = "Reload this module."
    self.reloadButton.name = "PathExplorer Reload"
    reloadFormLayout.addWidget(self.reloadButton)
    self.reloadButton.connect('clicked()', self.onReload)

    # reload and test button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadAndTestButton = qt.QPushButton("Reload and Test")
    self.reloadAndTestButton.toolTip = "Reload this module and then run the self tests."
    reloadFormLayout.addWidget(self.reloadAndTestButton)
    self.reloadAndTestButton.connect('clicked()', self.onReloadAndTest)

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # input volume selector
    #
    self.fiducialListSelector = slicer.qMRMLNodeComboBox()
    self.fiducialListSelector.nodeTypes = ( ("vtkMRMLMarkupsFiducialNode"), "" )
    self.fiducialListSelector.selectNodeUponCreation = True
    self.fiducialListSelector.addEnabled = True
    self.fiducialListSelector.removeEnabled = True
    self.fiducialListSelector.renameEnabled = True
    self.fiducialListSelector.noneEnabled = False
    self.fiducialListSelector.showHidden = False
    self.fiducialListSelector.showChildNodeTypes = False
    self.fiducialListSelector.setMRMLScene( slicer.mrmlScene )
    self.fiducialListSelector.setToolTip( "Markups Fiducial List" )
    parametersFormLayout.addRow("Markups Fiducial List: ", self.fiducialListSelector)

    #
    # reslicing plane position
    #
    self.planePositionSlider = qt.QSlider(qt.Qt.Horizontal)
    self.planePositionSlider.setMinimum(0)
    self.planePositionSlider.setMaximum(0)
    parametersFormLayout.addRow("Plane Position: ", self.planePositionSlider)

    #
    # reslicing plane orientation
    #
    self.planeOrientationSlider = qt.QSlider(qt.Qt.Horizontal)
    self.planeOrientationSlider.setMinimum(0)
    self.planeOrientationSlider.setMaximum(360)
    parametersFormLayout.addRow("Plane Orientation: ", self.planeOrientationSlider)

    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = False
    parametersFormLayout.addRow(self.applyButton)

    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.fiducialListSelector.connect("nodeActivated(vtkMRMLNode*)", self.onSelect)
    self.planePositionSlider.connect("valueChanged(int)", self.onPlaneChanged)
    self.planeOrientationSlider.connect("valueChanged(int)", self.onPlaneChanged)

    # Add vertical spacer
    self.layout.addStretch(1)

  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = self.fiducialListSelector.currentNode()

  def onApplyButton(self):
    self.logic = PathExplorerLogic()

    print("Run the algorithm")
    self.logic.run(self.fiducialListSelector.currentNode())
    self.planePositionSlider.setMaximum(self.logic.numberOfPoints-1)
    self.logic.updateSlice(self.planePositionSlider.value, self.planeOrientationSlider.value)

  def onReload(self,moduleName="PathExplorer"):
    """Generic reload method for any scripted module.
    ModuleWizard will subsitute correct default moduleName.
    """
    globals()[moduleName] = slicer.util.reloadScriptedModule(moduleName)

  def onReloadAndTest(self,moduleName="PathExplorer"):
    try:
      self.onReload()
      evalString = 'globals()["%s"].%sTest()' % (moduleName, moduleName)
      tester = eval(evalString)
      tester.runTest()
    except Exception, e:
      import traceback
      traceback.print_exc()
      qt.QMessageBox.warning(slicer.util.mainWindow(),
          "Reload and Test", 'Exception!\n\n' + str(e) + "\n\nSee Python Console for Stack Trace")

  def onPlaneChanged(self,value):
    if self.logic:
      pt = self.planePositionSlider.value
      angle = self.planeOrientationSlider.value

      self.logic.updateSlice(pt,angle)


#
# PathExplorerLogic
#

class PathExplorerLogic:
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget
  """
  def __init__(self):
    self.markupsFiducialList = None
    self.polydataPoints = None
    self.curveModel = slicer.mrmlScene.CreateNodeByClass('vtkMRMLModelNode')
    self.redViewer = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed')
    self.yellowViewer = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeYellow')
    self.greenViewer = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeGreen')
    self.numberOfPoints = 0

    # Configure CurveMakerLogic
    self.curveMakerLogic = CurveMaker.CurveMakerLogic()
    self.curveMakerLogic.NumberOfIntermediatePoints = 30
    self.curveMakerLogic.TubeRadius = 1.0

  def delayDisplay(self,message,msec=1000):
    #
    # logic version of delay display
    #
    print(message)
    self.info = qt.QDialog()
    self.infoLayout = qt.QVBoxLayout()
    self.info.setLayout(self.infoLayout)
    self.label = qt.QLabel(message,self.info)
    self.infoLayout.addWidget(self.label)
    qt.QTimer.singleShot(msec, self.info.close)
    self.info.exec_()

  def run(self,markups):
    """
    Run the actual algorithm
    """
    self.markupsFiducialList = markups

    if self.curveMakerLogic and self.markupsFiducialList and self.curveModel:
      self.delayDisplay('Running the aglorithm')

      self.curveMakerLogic.activateEvent(self.markupsFiducialList,self.curveModel)
      self.polydataPoints = self.curveMakerLogic.getGeneratedPoints()
      self.numberOfPoints = self.polydataPoints.GetNumberOfPoints()

    return True

  def updateSlice(self, point, angle):
    pos = self.polydataPoints.GetPoint(point)
    norm = [0.0, 0.0, 0.0]
    v1 = [0.0, 0.0, 0.0]
    v2 = [0.0, 0.0, 0.0]

    if point < self.numberOfPoints-1:
      pos1 = self.polydataPoints.GetPoint(point+1)
      norm = [pos1[0]-pos[0], pos1[1]-pos[1], pos1[2]-pos[2]]
    else:
      pos1 = self.polydataPoints.GetPoint(point-1)
      norm = [-(pos1[0]-pos[0]), -(pos1[1]-pos[1]), -(pos1[2]-pos[2])]

    math = vtk.vtkMath()

    normLength = math.Normalize(norm)
    norm[0] /= normLength
    norm[1] /= normLength
    norm[2] /= normLength

    math.Perpendiculars(norm,v1,v2,angle*math.Pi()/180)

    self.redViewer.SetSliceToRASByNTP(norm[0],norm[1],norm[2],v1[0],v1[1],v1[2],pos[0],pos[1],pos[2],0)


class PathExplorerTest(unittest.TestCase):
  """
  This is the test case for your scripted module.
  """

  def delayDisplay(self,message,msec=1000):
    """This utility method displays a small dialog and waits.
    This does two things: 1) it lets the event loop catch up
    to the state of the test so that rendering and widget updates
    have all taken place before the test continues and 2) it
    shows the user/developer/tester the state of the test
    so that we'll know when it breaks.
    """
    print(message)
    self.info = qt.QDialog()
    self.infoLayout = qt.QVBoxLayout()
    self.info.setLayout(self.infoLayout)
    self.label = qt.QLabel(message,self.info)
    self.infoLayout.addWidget(self.label)
    qt.QTimer.singleShot(msec, self.info.close)
    self.info.exec_()

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_PathExplorer1()

  def test_PathExplorer1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests sould exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import urllib
    downloads = (
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        print('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        print('Loading %s...\n' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading\n')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = PathExplorerLogic()
    self.delayDisplay('Test passed!')
