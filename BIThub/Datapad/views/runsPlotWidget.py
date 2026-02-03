import numpy as np
from PyQt5 import QtCore, QtWidgets # import PyQt5 before matplotlib

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)

from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from helpers.detectMethods import BITdetectMethods

matplotlib.use("Qt5Agg")

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=24, height=6, dpi=40):
        fig = Figure(figsize=(width, height), dpi=dpi)
        #Tight layout
        fig.tight_layout()
        self.axes = fig.add_subplot(111)
        super().__init__(fig)

class runsPlotWidget(QtWidgets.QGraphicsView):
    def __init__(self, parent=None):
        super(runsPlotWidget, self).__init__(parent)
        self.canvas = MplCanvas(self, width=24, height=6, dpi=40)
        plt.style.use('seaborn-v0_8-bright')
        plt.rc('axes', linewidth=2)
        font = {'weight' : 'bold', 'size' : 21}
        plt.rc('font', **font)
        toolbar = NavigationToolbar(self.canvas, self)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.canvas)
        
        self.bitMath = BITdetectMethods()
        self.setLayout(layout)
        self.curvesList = []

    def curvesPlot(self, run):
        testInfo, lysisReads, detectReads = run
        self.curvesList = []
        self.canvas.axes.cla()
        CHANNELNUM = 5
        time = detectReads['Time'] / 60000 - 5
        targetName = detectReads['Target']
        if len(targetName) < CHANNELNUM:
            targetName = ['Ch {}'.format(i+1) for i in range(CHANNELNUM)]
        sampleId = testInfo['SampleId']
        overallResult = testInfo['OverallResult']
        assayName = testInfo['Assay.Name']
        
        signalsList = detectReads['Signals']

        featList = np.zeros((5,4))
        lnColorLs = ['r', '#35ff35', '#3535ff', '#35ffff', '#ff35ff']
        for i in range(CHANNELNUM):
            _, diff, cp, stepWidth, avgRate= self.bitMath.labelSteps(signalsList[i])
            if diff == 0 and len(signalsList[i]) >= 50:
                diff = round(self.bitMath.consecutiveSum(np.diff(signalsList[i]), 50), 1)
            featList[i] = [diff, cp, stepWidth, avgRate]
            ln = self.plot(time, signalsList[i], targetName[i], lnColorLs[i])
            # print(ln)
            self.curvesList.append(ln)

        # Add Title
        title = '{}_{}'.format(sampleId, overallResult) if assayName != 'Dev_Mode' else '{}_{}'.format(sampleId, assayName)
        self.canvas.axes.set_title(title, color='k', fontsize = 21, fontweight = 'bold')
        # Add Axis Labels
        
        self.canvas.axes.set_ylabel("SensorRead (mvs)", fontsize = 21, fontweight = 'bold')
        self.canvas.axes.set_xlabel("Time (mins)", fontsize = 21, fontweight = 'bold')
        
        #Add grid
        self.canvas.axes.grid(linestyle = '-.')
        #Add legend
        legend = self.canvas.axes.legend(loc='upper right',  ncol=1)
        
        #Set tickers
        self.canvas.axes.xaxis.set_major_locator(MultipleLocator(5))
        self.canvas.axes.xaxis.set_major_formatter('{x:.0f}')
        self.canvas.axes.xaxis.set_minor_locator(MultipleLocator(2.5))

        self.canvas.axes.yaxis.set_major_locator(MultipleLocator(50))
        self.canvas.axes.yaxis.set_major_formatter('{x:.0f}')
        self.canvas.axes.yaxis.set_minor_locator(MultipleLocator(25))
        #Set Range
        self.canvas.axes.set_xlim(-5, 30)
        self.canvas.axes.set_ylim(0, 500)

        self.canvas.draw()
        return featList
        
    def plot(self, x, y, plotname, color):
        ln, = self.canvas.axes.plot(x, y, color = color, linewidth = 2, label = plotname)
        return ln
    
    def toggleCurve(self, status, index):
        if status:
            self.curvesList[index].set_alpha(1)
        else:
            self.curvesList[index].set_alpha(0)
        
        self.canvas.draw()