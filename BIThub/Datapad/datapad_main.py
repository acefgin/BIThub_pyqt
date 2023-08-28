from views.mainWin import *

from views.myPlotWidget import *

def listWidgetCtrl(lsWidget, dataInfoWidget):
    lsWidget.listWidget.onClickSignal.connect(dataInfoWidget.updateTestInfo)

def testInfoWidgetCtrl(widget):
    
    labelTexts = ['AAA', 'BBB', 'CCC']
    widget.label_2.setText(labelTexts[0])
    widget.label_4.setText(labelTexts[1])
    widget.label_6.setText(labelTexts[2])
    # featList = widget.graphicsView.curvesPlot(testLog)

    qTable = widget.tableWidget

    # for c in range(5):
    #     for r in range(3):
    #         if r == 0:
    #             item = QtWidgets.QTableWidgetItem(str(featList[c][0]))
    #         elif r == 1:
    #             item = QtWidgets.QTableWidgetItem(str(featList[c][3]))
    #         elif r == 2:
    #             item = QtWidgets.QTableWidgetItem(str(featList[c][1]))
    #         qTable.setItem(r, c, item)

class mainAppWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(mainAppWindow, self).__init__(parent)
        self.setupUi(self)

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = mainAppWindow()
    lsWidget = MainWindow.widget_2
    dataInfoWidget = MainWindow.widget
    lsWidget.listWidget.onClickSignal.connect(dataInfoWidget.updateTestInfo)
    # testInfoWidgetCtrl(MainWindow.widget)
    MainWindow.show()
    sys.exit(app.exec_())