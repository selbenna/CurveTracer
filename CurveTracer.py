import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy as np
import math

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
    self.reloadButton.name = "CurveTracer Reload"
    reloadFormLayout.addWidget(self.reloadButton)
    self.reloadButton.connect('clicked()', self.onReload)
    #
    ####################

    #
    # Voxel Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Voxel"
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
    # Entry Angle area
    #
    angleCollapsibleButton = ctk.ctkCollapsibleButton()
    angleCollapsibleButton.text = "Entry Angle"
    angleCollapsibleButton.collapsed = True
    self.layout.addWidget(angleCollapsibleButton)
    angleFormLayout = qt.QFormLayout(angleCollapsibleButton)


    #  - Model selector
    angleLayout = qt.QVBoxLayout()

    self.inputModelSelector = slicer.qMRMLNodeComboBox()
    self.inputModelSelector.nodeTypes = ["vtkMRMLModelHierarchyNode"]
    self.inputModelSelector.selectNodeUponCreation = True
    self.inputModelSelector.addEnabled = True
    self.inputModelSelector.removeEnabled = True
    self.inputModelSelector.noneEnabled = True
    self.inputModelSelector.showHidden = False
    self.inputModelSelector.showChildNodeTypes = False
    self.inputModelSelector.setMRMLScene( slicer.mrmlScene )
    self.inputModelSelector.setToolTip( "Select a 3D Model" )
    angleFormLayout.addRow("Model:", self.inputModelSelector)


    self.inputModelNode = None
    

    
    self.inputModelSelector.connect("currentNodeChanged(vtkMRMLNode*)",
                                         self.onModelSelected)


    self.anglesTable = qt.QTableWidget(1, 2)
    self.anglesTable.setSelectionBehavior(qt.QAbstractItemView.SelectRows)
    self.anglesTable.setSelectionMode(qt.QAbstractItemView.SingleSelection)
    self.anglesTableHeaders = ["Model", "Entry Angle (Degrees)"]
    self.anglesTable.setHorizontalHeaderLabels(self.anglesTableHeaders)
    self.anglesTable.horizontalHeader().setStretchLastSection(True)
    angleLayout.addWidget(self.anglesTable)

    self.extrapolateCheckBox = qt.QCheckBox()
    self.extrapolateCheckBox.checked = 0
    self.extrapolateCheckBox.setToolTip("Extrapolate the first and last segment to calculate the distance")
    self.extrapolateCheckBox.connect('toggled(bool)', self.updateAnglesTable)
    self.extrapolateCheckBox.text = 'Extrapolate curves to measure the distances'

    self.showErrorVectorCheckBox = qt.QCheckBox()
    self.showErrorVectorCheckBox.checked = 0
    self.showErrorVectorCheckBox.setToolTip("Show error vectors, which is defined by the target point and the closest point on the curve. The vector is perpendicular to the curve, unless the closest point is one end of the curve.")
    self.showErrorVectorCheckBox.connect('toggled(bool)', self.updateAnglesTable)
    self.showErrorVectorCheckBox.text = 'Show error vectors'

    angleLayout.addWidget(self.extrapolateCheckBox)
    angleLayout.addWidget(self.showErrorVectorCheckBox)
    angleFormLayout.addRow(angleLayout)


   
  

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
##    self.onSelectCalcul()

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



  def onModelSelected(self):

    # Remove observer if previous node exists
    if self.inputModelNode and self.tag:
      self.inputModelNode.RemoveObserver(self.tag)

    # Update selected node, add observer, and update control points
    if self.inputModelSelector.currentNode():
      self.inputModelNode = self.inputModelSelector.currentNode()
      self.tag = self.inputModelNode.AddObserver('ModifiedEvent', self.onModelUpdated)
    else:
      self.inputModelNode = None
      self.tag = None
    self.updateAnglesTable()

    
  def onModelUpdated(self,caller,event):
    if caller.IsA('vtkMRMLModelHierarchyNode') and event == 'ModifiedEvent':
      self.updateAnglesTable()


  def updateAnglesTable(self):

    logic = CurveTracerLogic()

    if not self.inputModelNode:
      self.anglesTable.clear()
      self.anglesTable.setHorizontalHeaderLabels(self.anglesTableHeaders)

    else:

      self.anglesTableData = []
      nOfControlPoints = self.inputModelNode.GetNumberOfChildrenNodes()
      
      if self.anglesTable.rowCount != nOfControlPoints:
        self.anglesTable.setRowCount(nOfControlPoints)

      
      for i in range(nOfControlPoints):

        chnode = self.inputModelNode.GetNthChildNode(i)
        if chnode == None: 
          continue
      
        mnode = chnode.GetAssociatedNode()
        if mnode == None:
          continue

        name = mnode.GetName()
        entryAngle = logic.EntryAngle(mnode, self.inputFiducialSelector.currentNode())
       
        cellModels = qt.QTableWidgetItem(name)
        cellAngle  = qt.QTableWidgetItem("%f" % entryAngle)
        

        row = [cellModels, cellAngle]
        self.anglesTable.setItem(i, 0, row[0])
        self.anglesTable.setItem(i, 1, row[1])
        
    
        self.anglesTableData.append(row)
        
    self.anglesTable.show()

      

    
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

    print ("GetVoxelValue() is called.")


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
      print voxel


  def EntryAngle(self, inputChildModelNode, inputFiducialNode):
    """
    Run the actual algorithm
    """

    logging.info('Processing started')

    print ("EntryAngle() is called.")



    if inputChildModelNode == None:
      return None
    
    if inputFiducialNode == None:
      return None
    

    poly = inputChildModelNode.GetPolyData()

     
    points = vtk.vtkPoints()
    idList = vtk.vtkIdList()
    pos0 = [0.0, 0.0, 0.0]
    posN = [0.0, 0.0, 0.0]
    n = inputFiducialNode.GetNumberOfFiducials()
      
      
    inputFiducialNode.GetNthFiducialPosition(0, pos0)
    inputFiducialNode.GetNthFiducialPosition(n-1, posN)
      
    traj = [pos0[0]- posN[0], pos0[1]-posN[1], pos0[2]-posN[2]]

    bspTree = vtk.vtkModifiedBSPTree()
    bspTree.SetDataSet(poly)
    bspTree.BuildLocator()

    tolerance = 0.001
    bspTree.IntersectWithLine(posN, pos0, tolerance, points, idList)

    angle = 0.0

    if bspTree.IntersectWithLine(posN, pos0, tolerance, points, idList) < 1:
      angle = 0.0
      
    else :
      
      cell0 = poly.GetCell(idList.GetId(0))  
      p0 = cell0.GetPoints()
      
      x0 = p0.GetPoint(1)[0]- p0.GetPoint(0)[0]
      y0 = p0.GetPoint(1)[1]- p0.GetPoint(0)[1]
      z0 = p0.GetPoint(1)[2]- p0.GetPoint(0)[2]
      v0 = [x0, y0, z0]
      x1 = p0.GetPoint(2)[0]- p0.GetPoint(0)[0]
      y1 = p0.GetPoint(2)[1]- p0.GetPoint(0)[1]
      z1 = p0.GetPoint(2)[2]- p0.GetPoint(0)[2]
      v1 = [x1, y1, z1]

      v0xv1 = np.cross(v1, v0)
      norm = math.sqrt(v0xv1[0]*v0xv1[0] + v0xv1[1]*v0xv1[1] + v0xv1[2]*v0xv1[2] )
      
      normal = (1/norm)*v0xv1
      angle = (vtk.vtkMath.AngleBetweenVectors(normal, traj))*180/(math.pi)
      

    return angle

   
  
 

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
