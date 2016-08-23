import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

#
# CurveTracer
#

class CurveTracer(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "CurveTracer" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Informatics"]
    self.parent.dependencies = []
    self.parent.contributors = ["Sarah Elbenna (ENSEEIHT), Junichi Tokuda (BWH)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    This module traces a curve and lists structures intersecting with it.
    """
    self.parent.acknowledgementText = """
    This module was created using a template developed by Jean-Christophe Fillion-Robin, Kitware Inc.
    and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

#
# CurveTracerWidget
#

class CurveTracerWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...
    
    ####################
    # For debugging
    #
    # Reload and Test area
    reloadCollapsibleButton = ctk.ctkCollapsibleButton()
    reloadCollapsibleButton.text = "Reload && Test"
    self.layout.addWidget(reloadCollapsibleButton)
    reloadFormLayout = qt.QFormLayout(reloadCollapsibleButton)
    
    # reload button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadButton = qt.QPushButton("Reload")
    self.reloadButton.toolTip = "Reload this module."
    self.reloadButton.name = "CurveMaker Reload"
    reloadFormLayout.addWidget(self.reloadButton)
    self.reloadButton.connect('clicked()', self.onReload)
    #
    ####################

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # input label map selector
    #
    self.inputLabelSelector = slicer.qMRMLNodeComboBox()
    self.inputLabelSelector.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
    self.inputLabelSelector.selectNodeUponCreation = True
    self.inputLabelSelector.addEnabled = False
    self.inputLabelSelector.removeEnabled = False
    self.inputLabelSelector.noneEnabled = False
    self.inputLabelSelector.showHidden = False
    self.inputLabelSelector.showChildNodeTypes = False
    self.inputLabelSelector.setMRMLScene( slicer.mrmlScene )
    self.inputLabelSelector.setToolTip( "Pick the input label map." )
    parametersFormLayout.addRow("Label Map: ", self.inputLabelSelector)

    #
    # input fiducials (trajectory) selector
    #
    self.inputFiducialSelector = slicer.qMRMLNodeComboBox()
    self.inputFiducialSelector.nodeTypes = ["vtkMRMLMarkupsFiducialNode"]
    self.inputFiducialSelector.selectNodeUponCreation = True
    self.inputFiducialSelector.addEnabled = True
    self.inputFiducialSelector.removeEnabled = True
    self.inputFiducialSelector.noneEnabled = False
    self.inputFiducialSelector.showHidden = False
    self.inputFiducialSelector.showChildNodeTypes = False
    self.inputFiducialSelector.setMRMLScene( slicer.mrmlScene )
    self.inputFiducialSelector.setToolTip( "Pick the trajectory." )
    parametersFormLayout.addRow("Trajectory: ", self.inputFiducialSelector)


    #
    # Voxel Table area 
    #
    voxelCollapsibleButton = ctk.ctkCollapsibleButton()
    voxelCollapsibleButton.text = "Voxel Table"
    voxelCollapsibleButton.collapsed = True
    self.layout.addWidget(voxelCollapsibleButton)
    distanceFormLayout = qt.QFormLayout(voxelCollapsibleButton)

    #  - Markups selector for input points
    distanceLayout = qt.QVBoxLayout()
    
    self.targetFiducialsSelector = slicer.qMRMLNodeComboBox()
    self.targetFiducialsSelector.nodeTypes = ["vtkMRMLMarkupsFiducialNode"]
    self.targetFiducialsSelector.selectNodeUponCreation = True
    self.targetFiducialsSelector.addEnabled = True
    self.targetFiducialsSelector.removeEnabled = True
    self.targetFiducialsSelector.noneEnabled = True 
    self.targetFiducialsSelector.showHidden = False
    self.targetFiducialsSelector.showChildNodeTypes = False
    self.targetFiducialsSelector.setMRMLScene( slicer.mrmlScene )
    self.targetFiducialsSelector.setToolTip( "Select Markups for targets" )
    distanceFormLayout.addWidget(self.targetFiducialsSelector)

    self.targetFiducialsNode = None
    self.tagDestinationDispNode = None
    
    self.targetFiducialsSelector.connect("currentNodeChanged(vtkMRMLNode*)",
                                         self.onTargetFiducialsSelected)


    self.fiducialsTable = qt.QTableWidget(1, 4)
    self.fiducialsTable.setSelectionBehavior(qt.QAbstractItemView.SelectRows)
    self.fiducialsTable.setSelectionMode(qt.QAbstractItemView.SingleSelection)
    self.fiducialsTableHeaders = ["Label", "1", "2", "3"]
    self.fiducialsTable.setHorizontalHeaderLabels(self.fiducialsTableHeaders)
    self.fiducialsTable.horizontalHeader().setStretchLastSection(True)
    distanceLayout.addWidget(self.fiducialsTable)

    self.extrapolateCheckBox = qt.QCheckBox()
    self.extrapolateCheckBox.checked = 0
    self.extrapolateCheckBox.setToolTip("Extrapolate the first and last segment to calculate the distance")
    self.extrapolateCheckBox.connect('toggled(bool)', self.updateTargetFiducialsTable)
    self.extrapolateCheckBox.text = 'Extrapolate curves to measure the distances'

    self.showErrorVectorCheckBox = qt.QCheckBox()
    self.showErrorVectorCheckBox.checked = 0
    self.showErrorVectorCheckBox.setToolTip("Show error vectors, which is defined by the target point and the closest point on the curve. The vector is perpendicular to the curve, unless the closest point is one end of the curve.")
    self.showErrorVectorCheckBox.connect('toggled(bool)', self.updateTargetFiducialsTable)
    self.showErrorVectorCheckBox.text = 'Show error vectors'

    distanceLayout.addWidget(self.extrapolateCheckBox)
    distanceLayout.addWidget(self.showErrorVectorCheckBox)
    distanceFormLayout.addRow("Distance from:", distanceLayout)



    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = False
    parametersFormLayout.addRow(self.applyButton)

    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.inputLabelSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.inputFiducialSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = self.inputLabelSelector.currentNode() and self.inputFiducialSelector.currentNode()

  def onApplyButton(self):
    logic = CurveTracerLogic()
    logic.GetVoxelValue(self.inputLabelSelector.currentNode(), self.inputFiducialSelector.currentNode())


  def onReload(self,moduleName="CurveTracer"):
    """Generic reload method for any scripted module.
    ModuleWizard will subsitute correct default moduleName.
    """
    globals()[moduleName] = slicer.util.reloadScriptedModule(moduleName)



  def onTargetFiducialsSelected(self):

    # Remove observer if previous node exists
    if self.targetFiducialsNode and self.tag:
      self.targetFiducialsNode.RemoveObserver(self.tag)

    # Update selected node, add observer, and update control points
    if self.targetFiducialsSelector.currentNode():
      self.targetFiducialsNode = self.targetFiducialsSelector.currentNode()
      self.tag = self.targetFiducialsNode.AddObserver('ModifiedEvent', self.onTargetFiducialsUpdated)
    else:
      self.targetFiducialsNode = None
      self.tag = None
    self.updateTargetFiducialsTable()

    
  def onTargetFiducialsUpdated(self,caller,event):
    if caller.IsA('vtkMRMLMarkupsFiducialNode') and event == 'ModifiedEvent':
      self.updateTargetFiducialsTable()


  def updateTargetFiducialsTable(self):

    logic = CurveTracerLogic()

    if not self.targetFiducialsNode:
      self.fiducialsTable.clear()
      self.fiducialsTable.setHorizontalHeaderLabels(self.fiducialsTableHeaders)

    else:

      labell = self.inputLabelSelector.currentNode()
      fiducial = self.targetFiducialsNode
      self.fiducialsTableData = []
      nOfControlPoints = self.targetFiducialsNode.GetNumberOfFiducials()

      if self.fiducialsTable.rowCount != nOfControlPoints:
        self.fiducialsTable.setRowCount(nOfControlPoints)

      
      for i in range(nOfControlPoints):

        label = self.targetFiducialsNode.GetNthFiducialLabel(i)
        pos = [0.0, 0.0, 0.0]

        self.targetFiducialsNode.GetNthFiducialPosition(i,pos)
        vox = logic.GetVoxelValue(labell, fiducial)

        
        if vox != 0.0:
          c1 = "1"
          c2 = "1"
          c3= "1"
        else:
          c1 = "0"
          c2 = "0"
          c3 = "0"
          
          

        cellLabel = qt.QTableWidgetItem(label)
        cell1 = qt.QTableWidgetItem(c1)
        cell2= qt.QTableWidgetItem(c2)
        cell3 = qt.QTableWidgetItem(c3) 
        row = [cellLabel, cell1, cell2, cell3]

        self.fiducialsTable.setItem(i, 0, row[0])
        self.fiducialsTable.setItem(i, 1, row[1])
        self.fiducialsTable.setItem(i, 2, row[2])
        self.fiducialsTable.setItem(i, 3, row[3])

        self.fiducialsTableData.append(row)
        
    self.fiducialsTable.show()

      

    
#
# CurveTracerLogic
#

class CurveTracerLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """



  def hasImageData(self,volumeNode):
    """This is an example logic method that
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      logging.debug('hasImageData failed: no volume node')
      return False
    if volumeNode.GetImageData() is None:
      logging.debug('hasImageData failed: no image data in volume node')
      return False
    return True

  def isValidInputOutputData(self, inputLabelMapNode, inputFiducialNode):
    """Validates if the output is not the same as input
    """
    if not inputLabelMapNode:
      logging.debug('isValidInputOutputData failed: no input label map node defined')
      return False
    if not inputFiducialNode:
      logging.debug('isValidInputOutputData failed: no input fiducial  node defined')
      return False
    return True

  def takeScreenshot(self,name,description,type=-1):
    # show the message even if not taking a screen shot
    slicer.util.delayDisplay('Take screenshot: '+description+'.\nResult is available in the Annotations module.', 3000)

    lm = slicer.app.layoutManager()
    # switch on the type to get the requested window
    widget = 0
    if type == slicer.qMRMLScreenShotDialog.FullLayout:
      # full layout
      widget = lm.viewport()
    elif type == slicer.qMRMLScreenShotDialog.ThreeD:
      # just the 3D window
      widget = lm.threeDWidget(0).threeDView()
    elif type == slicer.qMRMLScreenShotDialog.Red:
      # red slice window
      widget = lm.sliceWidget("Red")
    elif type == slicer.qMRMLScreenShotDialog.Yellow:
      # yellow slice window
      widget = lm.sliceWidget("Yellow")
    elif type == slicer.qMRMLScreenShotDialog.Green:
      # green slice window
      widget = lm.sliceWidget("Green")
    else:
      # default to using the full window
      widget = slicer.util.mainWindow()
      # reset the type so that the node is set correctly
      type = slicer.qMRMLScreenShotDialog.FullLayout

    # grab and convert to vtk image data
    qpixMap = qt.QPixmap().grabWidget(widget)
    qimage = qpixMap.toImage()
    imageData = vtk.vtkImageData()
    slicer.qMRMLUtils().qImageToVtkImageData(qimage,imageData)

    annotationLogic = slicer.modules.annotations.logic()
    annotationLogic.CreateSnapShot(name, description, type, 1, imageData)

  def GetVoxelValue(self, inputLabelMapNode, inputFiducialNode):
    """
    Run the actual algorithm
    """

    logging.info('Processing started')

    print ("run() is called.")


    nOfFiducials = inputFiducialNode.GetNumberOfFiducials()
    
    for i in range(nOfFiducials):
      pos = [0.0, 0.0, 0.0]
      lab = inputFiducialNode.GetNthFiducialLabel(i)
      inputFiducialNode.GetNthFiducialPosition(i, pos)
      image = inputLabelMapNode.GetImageData()
      xyz = [pos[0], pos[1],pos[2], 1.0]
      matrix = vtk.vtkMatrix4x4()
      inputLabelMapNode.GetRASToIJKMatrix(matrix)
      ijk = matrix.MultiplyDoublePoint(xyz)
      voxel = image.GetScalarComponentAsDouble(int(round(ijk[0])), int(round(ijk[1])), int(round(ijk[2])), 0)
      return voxel
    


  

class CurveTracerTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_CurveTracer1()

  def test_CurveTracer1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
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
        logging.info('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        logging.info('Loading %s...' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = CurveTracerLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
