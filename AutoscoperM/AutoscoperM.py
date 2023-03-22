import contextlib
import os
import unittest
import logging
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

#
# AutoscoperM
#


class AutoscoperM(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "AutoscoperM"  # TODO: make this more human readable by adding spaces
        self.parent.categories = [
            "Tracking"
        ]  # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = [
            "Bardiya Akhbari and Amy M Morton (Brown University)"
        ]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#AutoscoperM">module documentation</a>.
"""
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
"""

        # Additional initialization step after application startup is complete
        # NA


#
# AutoscoperMWidget
#


class AutoscoperMWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None):
        """
        Called when the user opens the module the first time and the widget is initialized.
        """
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._updatingGUIFromParameterNode = False

    def setup(self):
        """
        Called when the user opens the module the first time and the widget is initialized.
        """
        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/AutoscoperM.ui"))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = AutoscoperMLogic()

        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        # These connections ensure that whenever user changes some settings on the GUI, that is saved in the MRML scene
        # (in the selected parameter node).
        # self.ui.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
        # self.ui.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
        # self.ui.imageThresholdSliderWidget.connect("valueChanged(double)", self.updateParameterNodeFromGUI)
        # self.ui.invertOutputCheckBox.connect("toggled(bool)", self.updateParameterNodeFromGUI)
        # self.ui.invertedOutputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)

        # Buttons
        self.ui.applyButton.connect("clicked(bool)", self.onApplyButton)

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()

    def cleanup(self):
        """
        Called when the application closes and the module widget is destroyed.
        """
        self.removeObservers()

    def enter(self):
        """
        Called each time the user opens this module.
        """
        # Make sure parameter node exists and observed
        self.initializeParameterNode()

    def exit(self):
        """
        Called each time the user opens a different module.
        """
        # Do not react to parameter node changes (GUI wlil be updated when the user enters into the module)
        self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

    def onSceneStartClose(self, caller, event):
        """
        Called just before the scene is closed.
        """
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event):
        """
        Called just after the scene is closed.
        """
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self):
        """
        Ensure parameter node exists and observed.
        """
        # Parameter node stores all user choices in parameter values, node selections, etc.
        # so that when the scene is saved and reloaded, these settings are restored.

        self.setParameterNode(self.logic.getParameterNode())

        # Select default input nodes if nothing is selected yet to save a few clicks for the user
        if not self._parameterNode.GetNodeReference("InputVolume"):
            firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
            if firstVolumeNode:
                self._parameterNode.SetNodeReferenceID("InputVolume", firstVolumeNode.GetID())

    def setParameterNode(self, inputParameterNode):
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """

        if inputParameterNode:
            self.logic.setDefaultParameters(inputParameterNode)

        # Unobserve previously selected parameter node and add an observer to the newly selected.
        # Changes of parameter node are observed so that whenever parameters are changed by a script or any other module
        # those are reflected immediately in the GUI.
        if self._parameterNode is not None:
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
        self._parameterNode = inputParameterNode
        if self._parameterNode is not None:
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

        # Initial GUI update
        self.updateGUIFromParameterNode()

    def updateGUIFromParameterNode(self, caller=None, event=None):
        """
        This method is called whenever parameter node is changed.
        The module GUI is updated to show the current state of the parameter node.
        """

        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        # Make sure GUI changes do not call updateParameterNodeFromGUI (it could cause infinite loop)
        self._updatingGUIFromParameterNode = True

        # Update node selectors and sliders
        # self.ui.inputSelector.setCurrentNode(self._parameterNode.GetNodeReference("InputVolume"))
        # self.ui.outputSelector.setCurrentNode(self._parameterNode.GetNodeReference("OutputVolume"))
        # self.ui.invertedOutputSelector.setCurrentNode(self._parameterNode.GetNodeReference("OutputVolumeInverse"))
        # self.ui.imageThresholdSliderWidget.value = float(self._parameterNode.GetParameter("Threshold"))
        # self.ui.invertOutputCheckBox.checked = (self._parameterNode.GetParameter("Invert") == "true")

        # Update buttons states and tooltips
        if self._parameterNode.GetNodeReference("InputVolume") and self._parameterNode.GetNodeReference("OutputVolume"):
            self.ui.applyButton.toolTip = "Compute output volume"
            self.ui.applyButton.enabled = True
        else:
            self.ui.applyButton.toolTip = "Select input and output volume nodes"
            self.ui.applyButton.enabled = True  # False

        # All the GUI updates are done
        self._updatingGUIFromParameterNode = False

    def updateParameterNodeFromGUI(self, caller=None, event=None):
        """
        This method is called when the user makes any change in the GUI.
        The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
        """

        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch

        # self._parameterNode.SetNodeReferenceID("InputVolume", self.ui.inputSelector.currentNodeID)
        # self._parameterNode.SetNodeReferenceID("OutputVolume", self.ui.outputSelector.currentNodeID)
        # self._parameterNode.SetParameter("Threshold", str(self.ui.imageThresholdSliderWidget.value))
        # self._parameterNode.SetParameter("Invert", "true" if self.ui.invertOutputCheckBox.checked else "false")
        # self._parameterNode.SetNodeReferenceID("OutputVolumeInverse", self.ui.invertedOutputSelector.currentNodeID)

        self._parameterNode.EndModify(wasModified)

    def onApplyButton(self):
        """
        Run processing when user clicks "Apply" button.
        """
        executablePath = os.path.join(self.ui.autoscoperRootPath.directory, "autoscoper")
        if slicer.app.os == "win":
            executablePath = executablePath + ".exe"
        self.logic.startAutoscoper(executablePath)

        self.sampleDir = os.path.join(self.ui.autoscoperRootPath.directory, "sample_data")

        if self.logic.isAutoscoperOpen == True:
            # read config file
            self.readConfigFile()

    def readConfigFile(self):
        configPath = self.ui.configSelector.currentPath
        if configPath.endswith(".cfg"):
            self.logic.loadTrial(configPath)
        else:
            configPath = os.path.join(self.sampleDir, "wrist.cfg")
            self.logic.loadTrial(configPath)

        print("Loading cfg file: " + configPath)


#
# AutoscoperMLogic
#


class AutoscoperMLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self):
        """
        Called when the logic class is instantiated. Can be used for initializing member variables.
        """
        ScriptedLoadableModuleLogic.__init__(self)

        self.AutoscoperProcess = qt.QProcess()
        self.AutoscoperProcess.setProcessChannelMode(qt.QProcess.ForwardedChannels)
        self.TcpSocket = qt.QTcpSocket()
        self.TcpSocket.connect("error(QAbstractSocket::SocketError)", self._displaySocketError)
        self.StreamFromAutoscoper = qt.QDataStream()
        self.StreamFromAutoscoper.setByteOrder(qt.QSysInfo.ByteOrder)
        self.StreamFromAutoscoper.setDevice(self.TcpSocket)
        self.isAutoscoperOpen = False

    def setDefaultParameters(self, parameterNode):
        """
        Initialize parameter node with default settings.
        """
        if not parameterNode.GetParameter("Threshold"):
            parameterNode.SetParameter("Threshold", "100.0")
        if not parameterNode.GetParameter("Invert"):
            parameterNode.SetParameter("Invert", "false")

    def connectToAutoscoper(self):
        """Connect to a running instance of Autoscoper."""
        if self.TcpSocket.state() == qt.QAbstractSocket.ConnectedState:
            logging.warning("connection to Autoscoper is already established")
            return
        if self.TcpSocket.state() != qt.QAbstractSocket.UnconnectedState:
            logging.warning("connection to Autoscoper is in progress")
            return
        self.TcpSocket.connectToHost("127.0.0.1", 30007)
        self.TcpSocket.waitForConnected(5000)
        logging.info("connection to Autoscoper is established")

    def disconnectFromAutoscoper(self):
        """Disconnect from a running instance of Autoscoper."""
        if self.TcpSocket.state() == qt.QAbstractSocket.UnconnectedState:
            logging.warning("connection to Autoscoper is not established")
            return
        if self.TcpSocket.state() != qt.QAbstractSocket.ConnectedState:
            logging.warning("disconnection to Autoscoper is in progress")
            return
        self.TcpSocket.disconnectFromHost()
        logging.info("Autoscoper is disconnected from 3DSlicer")

    def startAutoscoper(self, executablePath):
        """Start Autoscoper executable in a new process

        This call waits the process has been started and returns.
        """
        if not os.path.exists(executablePath):
            logging.error("Specified executable %s does not exist" % executablePath)
            return

        if self.AutoscoperProcess.state() in [qt.QProcess.Starting, qt.QProcess.Running]:
            logging.error("Autoscoper executable already started")
            return

        self.isAutoscoperOpen = True

        @contextlib.contextmanager
        def changeCurrentDir(directory):
            currentDirectory = os.getcwd()
            try:
                os.chdir(directory)
                yield
            finally:
                os.chdir(currentDirectory)

        executableDirectory = os.path.dirname(executablePath)

        with changeCurrentDir(executableDirectory):
            logging.info("Starting Autoscoper %s" % executablePath)
            # self.AutoscoperProcess.start("cmd.exe", ["/K ", executablePath])
            self.AutoscoperProcess.start(executablePath)
            self.AutoscoperProcess.waitForStarted()

        slicer.app.processEvents()

        self.connectToAutoscoper()

    def stopAutoscoper(self, force=True):
        """Stop Autoscoper process"""
        if self.AutoscoperProcess.state() == qt.QProcess.NotRunning:
            logging.error("Autoscoper executable is not running")
            return

        if force:
            self.AutoscoperProcess.kill()
        else:
            self.AutoscoperProcess.terminate()

    def _displaySocketError(self, sockerError):
        logging.error("The following error occurred: %s" % self.TcpSocket.errorString())

    @contextlib.contextmanager
    def _streamToAutoscoper(self):
        """Yield datastream for sending data to Autoscoper."""
        try:
            data = qt.QByteArray()
            stream = qt.QDataStream(data, qt.QIODevice.WriteOnly)
            stream.setByteOrder(qt.QSysInfo.ByteOrder)
            yield stream
        finally:
            self.TcpSocket.write(data)

    def _waitForAutoscoper(self, methodId, msecs=10000):
        """Block current process waiting for Autoscoper to finish executing a method."""
        self.TcpSocket.waitForReadyRead(msecs)
        if self.StreamFromAutoscoper.readUInt8() != methodId:
            logging.error("unexpected results")

    @contextlib.contextmanager
    def _streamFromAutoscoper(self, methodId, msecs=10000):
        """Yield datastream for receiving data from Autoscoper after current method finishes."""
        self._waitForAutoscoper(methodId, msecs)
        yield self.StreamFromAutoscoper

    def _checkAutoscoperConnection(method):
        """Decorator to check that Autoscoper process is ready."""

        from functools import wraps

        @wraps(method)
        def wrapped(self, *method_args, **method_kwargs):

            if self.TcpSocket.state() != qt.QAbstractSocket.ConnectedState:
                raise RuntimeError("Autoscoper connection is not established")

            return method(self, *method_args, **method_kwargs)

        return wrapped

    @_checkAutoscoperConnection
    def loadTrial(self, filename):
        """Load trial in Autoscoper"""
        autoscoperMethodId = 1

        with self._streamToAutoscoper() as stream:
            stream.writeUInt8(autoscoperMethodId)
            stream.writeRawData(filename.encode("latin1"))

        self._waitForAutoscoper(autoscoperMethodId)

    @_checkAutoscoperConnection
    def loadTrackingDataVolume(self):
        """Load tracking data in Autoscoper"""
        logging.error("not implemented")

    @_checkAutoscoperConnection
    def saveTrackingDataVolume(self):
        """Save tracking data in Autoscoper"""
        logging.error("not implemented")

    @_checkAutoscoperConnection
    def loadFilterSettings(self):
        """Load filter settings in Autoscoper"""
        logging.error("not implemented")

    @_checkAutoscoperConnection
    def setFrame(self):
        """Set frame in Autoscoper"""
        logging.error("not implemented")

    @_checkAutoscoperConnection
    def getPose(self):
        """Get pose from Autoscoper"""
        logging.error("not implemented")

    @_checkAutoscoperConnection
    def setPose(self):
        """Set pose in Autoscoper"""
        logging.error("not implemented")

    @_checkAutoscoperConnection
    def getNormalizedCrossCorrelation(self):
        """Get normalized cross-correlation (NCC) from Autoscoper"""
        autoscoperMethodId = 8

        with self._streamToAutoscoper() as stream:
            stream.writeUInt8(autoscoperMethodId)

        with self._streamFromAutoscoper(autoscoperMethodId) as stream:
            length = stream.readUInt8()
            return [stream.readDouble() for _ in range(length)]

    @_checkAutoscoperConnection
    def setBackground(self, threshold):
        """Set background in Autoscoper"""
        autoscoperMethodId = 9

        with self._streamToAutoscoper() as stream:
            stream.writeUInt8(autoscoperMethodId)
            stream.writeDouble(threshold)

        self._waitForAutoscoper(autoscoperMethodId)

    @_checkAutoscoperConnection
    def optimizeFrame(self):
        logging.error("not implemented")

    @_checkAutoscoperConnection
    def saveFullDRRImage(self):
        autoscoperMethodId = 12

        with self._streamToAutoscoper() as stream:
            stream.writeUInt8(autoscoperMethodId)

        self._waitForAutoscoper(autoscoperMethodId)

    def process(self, inputVolume, outputVolume, imageThreshold, invert=False, showResult=True):
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        :param inputVolume: volume to be thresholded
        :param outputVolume: thresholding result
        :param imageThreshold: values above/below this threshold will be set to 0
        :param invert: if True then values above the threshold will be set to 0, otherwise values below are set to 0
        :param showResult: show output volume in slice viewers
        """

        if not inputVolume or not outputVolume:
            raise ValueError("Input or output volume is invalid")

        import time

        startTime = time.time()
        logging.info("Processing started")

        # Compute the thresholded output volume using the "Threshold Scalar Volume" CLI module
        cliParams = {
            "InputVolume": inputVolume.GetID(),
            "OutputVolume": outputVolume.GetID(),
            "ThresholdValue": imageThreshold,
            "ThresholdType": "Above" if invert else "Below",
        }
        cliNode = slicer.cli.run(
            slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True, update_display=showResult
        )
        # We don't need the CLI module node anymore, remove it to not clutter the scene with it
        slicer.mrmlScene.RemoveNode(cliNode)

        stopTime = time.time()
        logging.info("Processing completed in {0:.2f} seconds".format(stopTime - startTime))