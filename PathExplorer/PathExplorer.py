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
    self.inputSelector = slicer.qMRMLNodeComboBox()
    self.inputSelector.nodeTypes = ( ("vtkMRMLMarkupsFiducialNode"), "" )
    self.inputSelector.selectNodeUponCreation = True
    self.inputSelector.addEnabled = True
    self.inputSelector.removeEnabled = True
    self.inputSelector.noneEnabled = False
    self.inputSelector.showHidden = False
    self.inputSelector.showChildNodeTypes = False
    self.inputSelector.setMRMLScene( slicer.mrmlScene )
    self.inputSelector.setToolTip( "Markups Fiducial List" )
    parametersFormLayout.addRow("Markups Fiducial List: ", self.inputSelector)

    #
    # reslicing plane position
    #
    self.planePositionWidget = qt.QSlider(qt.Qt.Horizontal)
    self.planePositionWidget.setMinimum(0)
    self.planePositionWidget.setMaximum(0)
    parametersFormLayout.addRow("Plane Position: ", self.planePositionWidget)

    #
    # reslicing plane orientation
    #
    self.planeOrientationWidget = qt.QSlider(qt.Qt.Horizontal)
    self.planeOrientationWidget.setMinimum(0)
    self.planeOrientationWidget.setMaximum(360)
    parametersFormLayout.addRow("Plane Orientation: ", self.planeOrientationWidget)

    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = False
    parametersFormLayout.addRow(self.applyButton)

    self.markupsFiducialList = None
    self.polydataPoints = None
    self.curveModel = slicer.mrmlScene.CreateNodeByClass('vtkMRMLModelNode')
    self.planeTransform = slicer.mrmlScene.CreateNodeByClass('vtkMRMLLinearTransformNode')
    self.redViewer = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed')

    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.planePositionWidget.connect("valueChanged(int)", self.onPlaneChanged)
    self.planeOrientationWidget.connect("valueChanged(int)", self.onPlaneChanged)

    # Add vertical spacer
    self.layout.addStretch(1)

  def cleanup(self):
    pass

  def onMarkupsModified(self,obj,event):
    print (obj,event)

  def onPlaneChanged(self,value):
    pt = self.planePositionWidget.value
    angle = self.planeOrientationWidget.value
    pos = self.polydataPoints.GetPoint(pt)
    norm = [0.0, 0.0, 0.0]
    v1 = [0.0, 0.0, 0.0]
    v2 = [0.0, 0.0, 0.0]

    if pt < self.polydataPoints.GetNumberOfPoints()-1:
      pos1 = self.polydataPoints.GetPoint(pt+1)
      norm = [pos1[0]-pos[0], pos1[1]-pos[1], pos1[2]-pos[2]]
    else:
      pos1 = self.polydataPoints.GetPoint(pt-1)
      norm = [-(pos1[0]-pos[0]), -(pos1[1]-pos[1]), -(pos1[2]-pos[2])]

    math = vtk.vtkMath()
    
    normLength = math.Normalize(norm)
    norm[0] /= normLength
    norm[1] /= normLength
    norm[2] /= normLength

    math.Perpendiculars(norm,v1,v2,angle*math.Pi()/180)

    self.redViewer.SetSliceToRASByNTP(norm[0],norm[1],norm[2],v1[0],v1[1],v1[2],pos[0],pos[1],pos[2],0)

  def onSelect(self):
#    if (self.markupsFiducialList):
#      self.markupsFiducialList.RemoveObserver(self.markupsFiducialList.LabelFormatModifiedEvent)
#      self.markupsFiducialList.RemoveObserver(self.markupsFiducialList.PointModifiedEvent)
#      self.markupsFiducialList.RemoveObserver(self.markupsFiducialList.NthMarkupModifiedEvent)
#      self.markupsFiducialList.RemoveObserver(self.markupsFiducialList.MarkupAddedEvent)
#      self.markupsFiducialList.RemoveObserver(self.markupsFiducialList.MarkupRemovedEvent)
#
    self.markupsFiducialList = self.inputSelector.currentNode()
#
#    self.markupsFiducialList.AddObserver(self.markupsFiducialList.LabelFormatModifiedEvent, self.onMarkupsModified)
#    self.markupsFiducialList.AddObserver(self.markupsFiducialList.PointModifiedEvent, self.onMarkupsModified)
#    self.markupsFiducialList.AddObserver(self.markupsFiducialList.NthMarkupModifiedEvent, self.onMarkupsModified)
#    self.markupsFiducialList.AddObserver(self.markupsFiducialList.MarkupAddedEvent, self.onMarkupsModified)
#    self.markupsFiducialList.AddObserver(self.markupsFiducialList.MarkupRemovedEvent, self.onMarkupsModified)
#
    self.applyButton.enabled = self.inputSelector.currentNode()

  def onApplyButton(self):
    logic = PathExplorerLogic()
    curveMakerLogic = CurveMaker.CurveMakerLogic()
    curveMakerLogic.NumberOfIntermediatePoints = 30
    curveMakerLogic.TubeRadius = 1.0
    curveMakerLogic.activateEvent(self.markupsFiducialList,self.curveModel)
    self.polydataPoints = curveMakerLogic.getGeneratedPoints()
    self.planePositionWidget.setMaximum(self.polydataPoints.GetNumberOfPoints()-1)
    self.planePositionWidget.setValue(0)
    print("Run the algorithm")
    logic.run(self.inputSelector.currentNode())

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
    pass

  def hasImageData(self,volumeNode):
    """This is a dummy logic method that
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      print('no volume node')
      return False
    if volumeNode.GetImageData() == None:
      print('no image data')
      return False
    return True

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

  def run(self,inputVolume):
    """
    Run the actual algorithm
    """

    self.delayDisplay('Running the aglorithm')

    return True


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
    self.assertTrue( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
