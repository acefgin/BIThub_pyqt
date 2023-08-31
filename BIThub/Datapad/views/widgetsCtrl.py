from views.resources.dataVisul_Widget_ui import Ui_dataVisualWidget_Form
from views.resources.dbList_Widget_ui import Ui_dbListWidget_Form
from views.resources.testImport_Widget import testImportWidget_Form

from PyQt5 import QtCore, QtGui, QtWidgets

import os, csv, glob, json, socket

from pathlib import Path

class dataVisual_Widget(QtWidgets.QWidget, Ui_dataVisualWidget_Form):
    def __init__(self, parent=None):
        super(dataVisual_Widget, self).__init__(parent)
        self.setupUi(self)
        self.checkBox.stateChanged.connect(lambda: self.graphicsView.toggleCurve(self.checkBox.isChecked(), 0))
        self.checkBox_2.stateChanged.connect(lambda: self.graphicsView.toggleCurve(self.checkBox_2.isChecked(), 1))
        self.checkBox_3.stateChanged.connect(lambda: self.graphicsView.toggleCurve(self.checkBox_3.isChecked(), 2))
        self.checkBox_4.stateChanged.connect(lambda: self.graphicsView.toggleCurve(self.checkBox_4.isChecked(), 3))
        self.checkBox_5.stateChanged.connect(lambda: self.graphicsView.toggleCurve(self.checkBox_5.isChecked(), 4))

    def updateTestInfo(self, testLog):
        self.checkBox.setChecked(True)
        self.checkBox_2.setChecked(True)
        self.checkBox_3.setChecked(True)
        self.checkBox_4.setChecked(True)
        self.checkBox_5.setChecked(True)
        # labelTexts = [testLog["Input"], testLog["Protocol"], testLog["TestDate"]]
        # self.label_2.setText(labelTexts[0])
        # self.label_4.setText(labelTexts[1])
        # self.label_6.setText(labelTexts[2])
        featList = self.graphicsView.curvesPlot(testLog)

        qTable = self.tableWidget

        for c in range(5):
            for r in range(3):
                if r == 0:
                    item = QtWidgets.QTableWidgetItem(str(featList[c][0]))
                elif r == 1:
                    item = QtWidgets.QTableWidgetItem(str(featList[c][3]))
                elif r == 2:
                    item = QtWidgets.QTableWidgetItem(str(featList[c][1]))
                qTable.setItem(r, c, item)

class dbList_Widget(QtWidgets.QWidget, Ui_dbListWidget_Form):
    def __init__(self, parent=None):
        super(dbList_Widget, self).__init__(parent)
        self.setupUi(self)
        self.pushButton_2.clicked.connect(self.getDbFile)
        self.pushButton_2.setEnabled(False)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.isDeviceConnected)
        self.timer.start(1000)
        
    def getDbFile(self):
        self.listWidget.getDd2Df()
        self.listWidget.loadItemFromDF()
        self.listWidget.getItemsForCombobox()
        self.listWidgetCtl()
    
    def isDeviceConnected(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('169.254.21.151', 22))
        print(result)
        if result == 0:
            self.pushButton_2.setEnabled(True)
        else:
            self.pushButton_2.setEnabled(False)
        self.timer.start(1000)
        
    def listWidgetCtl(self):
        cbboxItems = self.listWidget.cbboxItemsSets
        keylist = self.listWidget.keyList
        self.comboBox.addItem("All")
        self.comboBox_2.addItem("All")
        self.comboBox_3.addItem("All")
        for i in range(len(keylist)):
            for item in cbboxItems[i]:
                if i == 0:
                    self.comboBox.addItem(str(item))
                elif i == 1:
                    self.comboBox_2.addItem(str(item))
                elif i == 2:
                    self.comboBox_3.addItem(str(item))
            if i == 0:
                self.comboBox.currentTextChanged.connect(lambda value: self.listWidget.updateListItem(keylist[0], value))
            elif i == 1:
                self.comboBox_2.currentTextChanged.connect(lambda value: self.listWidget.updateListItem(keylist[1], value))
            elif i == 2:
                self.comboBox_3.currentTextChanged.connect(lambda value: self.listWidget.updateListItem(keylist[2], value))

class testImport_Widget(QtWidgets.QWidget, testImportWidget_Form):
    def __init__(self, parent=None):
        super(testImport_Widget, self).__init__(parent)
        self.setupUi(self)
        self.objectDis = {}
        self.filenamesSet = set()

        self.pushButton.clicked.connect(self.createTest)
        self.pushButton_2.clicked.connect(self.deleteTest)
        self.pushButton_7.clicked.connect(self.selectFolder)
        self.pushButton_5.clicked.connect(self.modifyTest)
        self.pushButton_6.clicked.connect(self.checkMap)
        self.pushButton_4.clicked.connect(self.dumpTestInfo2JsonFile)

        # creating editable combo box
        self.comboBox.setEditable(True)
        self.comboBox_2.setEditable(True)
        self.comboBox_3.setEditable(True)
        self.comboBox_4.setEditable(True)
        self.comboBox_5.setEditable(True)
  
        # setting insertion policy
        # new item will get added alphabetically
        self.comboBox.setInsertPolicy(QComboBox.InsertAlphabetically)
        self.comboBox_2.setInsertPolicy(QComboBox.InsertAlphabetically)
        self.comboBox_3.setInsertPolicy(QComboBox.InsertAlphabetically)
        self.comboBox_4.setInsertPolicy(QComboBox.InsertAlphabetically)
        self.comboBox_5.setInsertPolicy(QComboBox.InsertAlphabetically)

        self.listWidget.itemDoubleClicked.connect(self.select2Edit)


        self.checkTestInfoMsg = QMessageBox()
        self.checkTestInfoMsg.setWindowTitle("Please check the new tests")
        self.checkTestInfoMsg.setText("Raw file not found for some tests")
        self.checkTestInfoMsg.setIcon(QMessageBox.Warning)

        self.mapChkPassed = False

    def createTest(self):
        date = self.lineEdit.text()
        deviceId = self.lineEdit_2.text()
        runNum = self.spinBox.value()
        location = self.lineEdit_4.text()
        input = self.lineEdit_3.text()
        kitLot = self.lineEdit_5.text()
        protocol = self.comboBox.currentText()
        devOperator = self.comboBox_2.currentText()
        kitOperator = self.comboBox_3.currentText()

        usage = self.comboBox_4.currentText()
        asExpected = self.comboBox_5.currentText()

        testId = date + '_' + deviceId + f'_{runNum}'

        document = {}
        document["TestId"] = testId
        document["Protocol"] = protocol
        document["Location"] = location
        document["DeviceOperator"] = devOperator
        document["devOperator"] = kitOperator
        document["KitLot"] = kitLot
        document["Input"] = input
        document["TestDate"] = date
        document["DeviceId"] = deviceId
        document["Usage"] = usage
        document["AsExpected"] = asExpected

        self.listWidget.addItem(f'{testId}==>{protocol}==>{input}@{location}')
        self.objectDis[testId] = document

    
    def deleteTest(self):
        curText = self.listWidget.currentItem().text()
        curRow = self.listWidget.currentRow()
        self.listWidget.takeItem(curRow)
        testId = curText[:curText.index("=")]
        self.objectDis.pop(testId)
    
    def modifyTest(self):
        date = self.lineEdit.text()
        deviceId = self.lineEdit_2.text()
        runNum = self.spinBox.value()
        location = self.lineEdit_4.text()
        input = self.lineEdit_3.text()
        kitLot = self.lineEdit_5.text()
        protocol = self.comboBox.currentText()
        devOperator = self.comboBox_2.currentText()
        kitOperator = self.comboBox_3.currentText()

        usage = self.comboBox_4.currentText()
        asExpected = self.comboBox_5.currentText()

        testId = date + '_' + deviceId + f'_{runNum}'

        document = self.objectDis[testId]

        document["TestId"] = testId
        document["Protocol"] = protocol
        document["Location"] = location
        document["DeviceOperator"] = devOperator
        document["devOperator"] = kitOperator
        document["KitLot"] = kitLot
        document["Input"] = input
        document["TestDate"] = date
        document["DeviceId"] = deviceId
        document["Usage"] = usage
        document["AsExpected"] = asExpected

        curRow = self.listWidget.currentRow()
        self.listWidget.takeItem(curRow)
        self.listWidget.addItem(f'{testId}==>{protocol}==>{input}@{location}')

    
    def select2Edit(self, listWidgeItem):
        curText = listWidgeItem.text()
        testId = curText[:curText.index("=")]
        document = self.objectDis[testId]
        self.updateInputFields(document)
    
    def updateInputFields(self, document):
        testId = document["TestId"]
        protocol = document["Protocol"] 
        runNum = int(testId[-1])
        location = document["Location"]
        devOperator= document["DeviceOperator"]
        kitOperator = document["devOperator"]
        kitLot = document["KitLot"]
        input = document["Input"]
        date = document["TestDate"]
        deviceId = document["DeviceId"]
        usage = document["Usage"]
        asExpected = document["AsExpected"]

        self.lineEdit.setText(date)
        self.lineEdit_2.setText(deviceId)
        self.spinBox.setValue(runNum)
        self.lineEdit_4.setText(location)
        self.lineEdit_3.setText(input)
        self.lineEdit_5.setText(kitLot)

        self.updateComboBox(self.comboBox, protocol)
        self.updateComboBox(self.comboBox_2, devOperator)
        self.updateComboBox(self.comboBox_3, kitOperator)
        self.updateComboBox(self.comboBox_4, usage)
        self.updateComboBox(self.comboBox_5, asExpected)

    
    def updateComboBox(self, comboBox, itemText):
        for i in range(comboBox.count()):
            if itemText == comboBox.itemText(i):
                comboBox.setCurrentIndex(i)

    def selectFolder(self):
        self.folderpath = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder')
        model = QFileSystemModel()
        model.setRootPath(self.folderpath)
        
        self.listView.setModel(model)
        self.listView.setRootIndex(model.index(self.folderpath))

        self.filepathes = sorted(glob.glob(os.path.join(self.folderpath, '*.csv')))
        
        for filepath in self.filepathes:
            self.filenamesSet.add(Path(filepath).stem)
    
    def checkMap(self):
        cnt = 0
        for idx in range(0, self.listWidget.count()):
            item = self.listWidget.item(idx)
            itemText = item.text()
            testId = itemText[:itemText.index("=")]

            if testId in self.filenamesSet:
                item.setForeground(QtCore.Qt.green)
                cnt += 1
            else:
                item.setForeground(QtCore.Qt.red)
        if cnt != 0 and cnt == self.listWidget.count():
            self.mapChkPassed = True

    def dumpTestInfo2JsonFile(self):

        filenames = self.filepathes
        jsonFile = "S2R_testlog.json"
        if not self.mapChkPassed:
            msg = self.checkTestInfoMsg.exec_()
            return

        with open(jsonFile,'w') as file:

            idx = 1
            objList = []
            for filename in filenames:
                testId = os.path.splitext(os.path.basename(filename))[0]
                
                idx += 1
                if testId in self.objectDis:
                    testDocument = self.objectDis[testId]
                    resultDocument = self.readTestRsult(self.folderpath, filename)
                    self.Merge(resultDocument, testDocument)
                    objList.append(testDocument)
                    print(str(idx) + ":" + testId)
                
            json.dump(objList, file, indent = 2)
    
    # Merge dict1 to dict2, update in dict2
    def Merge(self, dict1, dict2):
        return(dict2.update(dict1))
    
    def readTestRsult(self, folderPath, filename):

        LysisTemp = []
        LysisTime = []
        CartTemp = []
        AdcTemp = []
        TargetName = []
        WellResult = []
        ECVolDiffs = []
        SampleId = ''

        ReactTime = []
        Well1Readings = []
        Well2Readings = []
        Well3Readings = []
        Well4Readings = []
        Well5Readings = []

        dcoument = {}

        with open(os.path.join(folderPath, filename),'r') as csvfile:
            plots = csv.reader(csvfile, delimiter=',')
            idx = 0

            for row in plots:
                if idx == 1:
                    SampleId = row[0]
                if idx == 4:
                    LysisTime = row[3:]
                    LysisTime = [round(float(i)/1000, 2) for i in LysisTime if i != '']
                if idx == 5:
                    LysisTemp = row[3:]
                    LysisTemp = [round(float(i), 2) for i in LysisTemp if i != '']
                if idx == 8:
                    ReactTime = row[7:]
                    ReactTime = [round(float(i)/1000, 2) for i in ReactTime if i != '']
                if idx == 9:
                    CartTemp = row[7:]
                    CartTemp = [round(float(i), 2) for i in CartTemp if i != '']
                if idx == 10:
                    AdcTemp = row[7:]
                    AdcTemp = [round(float(i), 2) for i in AdcTemp if i != '']
                if idx == 11:

                    TargetName.append(row[4])
                    WellResult.append(row[5])
                    ECVolDiffs.append(round(float(row[6]), 2))
                    Well1Readings = row[7:]
                    Well1Readings = [round(float(i), 2) for i in Well1Readings if i != '']

                if idx == 12:

                    TargetName.append(row[4])
                    WellResult.append(row[5])
                    ECVolDiffs.append(round(float(row[6]), 2))
                    Well2Readings = row[7:]   
                    Well2Readings = [round(float(i), 2) for i in Well2Readings if i != '']

                if idx == 13:

                    TargetName.append(row[4])
                    WellResult.append(row[5])
                    ECVolDiffs.append(round(float(row[6]), 2))
                    Well3Readings = row[7:]
                    Well3Readings = [round(float(i), 2) for i in Well3Readings if i != '']

                if idx == 14:

                    TargetName.append(row[4])
                    WellResult.append(row[5])
                    ECVolDiffs.append(round(float(row[6]), 2))
                    Well4Readings = row[7:]
                    Well4Readings = [round(float(i), 2) for i in Well4Readings if i != '']

                if idx == 15:

                    TargetName.append(row[4])
                    WellResult.append(row[5])
                    ECVolDiffs.append(round(float(row[6]), 2))
                    Well5Readings = row[7:]
                    Well5Readings = [round(float(i), 2) for i in Well5Readings if i != '']
                
                idx += 1

        dcoument["LysisTemp"] = LysisTemp
        dcoument["LysisTime"] = LysisTime
        dcoument["CartTemp"] = CartTemp
        dcoument["AdcTemp"] = AdcTemp
        dcoument["TargetName"] = TargetName
        dcoument["WellResult"] = WellResult
        dcoument["ECVolDiffs"] = ECVolDiffs
        dcoument["SampleId"] = SampleId

        dcoument["ReactTime"] = ReactTime
        dcoument["Well1Readings"] = Well1Readings
        dcoument["Well2Readings"] = Well2Readings
        dcoument["Well3Readings"] = Well3Readings
        dcoument["Well4Readings"] = Well4Readings
        dcoument["Well5Readings"] = Well5Readings

        return dcoument
        


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()

    centralwidget = QtWidgets.QWidget(MainWindow)

    MainWindow.show()
    sys.exit(app.exec_())
