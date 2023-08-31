import numpy as np
from PyQt5 import QtCore, QtWidgets # import PyQt5 before matplotlib

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)

from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

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
        plt.style.use('seaborn-bright')
        plt.rc('axes', linewidth=2)
        font = {'weight' : 'bold', 'size' : 21}
        plt.rc('font', **font)
        toolbar = NavigationToolbar(self.canvas, self)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.canvas)
        
        self.setLayout(layout)
        self.curvesList = []

    def curvesPlot(self, run):
        testInfo, lysisReads, detectReads = run
        self.curvesList = []
        self.canvas.axes.cla()
        CHANNELNUM = 5
        time = detectReads['Time'] / 60000 - 5
        targetName = detectReads['Target']
        sampleId = testInfo['SampleId']
        overallResult = testInfo['OverallResult']
        
        chList = detectReads['Signals']
        smoothedSignals = []
        for i in range(CHANNELNUM):

            smoothedSignals.append(self.smooth(chList[i]))

        featList = np.zeros((5,4))
        lnColorLs = ['r', '#35ff35', '#3535ff', '#35ffff', '#ff35ff']
        for i in range(CHANNELNUM):
            _, diff, cp, stepWidth, avgRate= self.labelSteps(smoothedSignals[i])
            if diff == 0 and len(smoothedSignals[i]) >= 50:
                diff = round(self.consecutiveSum(np.diff(smoothedSignals[i]), 50), 1)
            featList[i] = [diff, cp, stepWidth, avgRate]
            ln = self.plot(time, chList[i], targetName[i], lnColorLs[i])
            # print(ln)
            self.curvesList.append(ln)

        # Add Title
        title = '{}_{}'.format(sampleId, overallResult)
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

    def smooth(self, x,window_len=10,window='hanning'):

        if x.ndim != 1:
            raise ValueError("smooth only accepts 1 dimension arrays.")

        if x.size < window_len:
            raise ValueError("Input vector needs to be bigger than window size.")

        if window_len<3:
            return x

        if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
            raise ValueError("Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'")

        s = np.r_[x[window_len-1:0:-1],x,x[-2:-window_len-1:-1]]
        #print(len(s))
        if window == 'flat': #moving average
            w = np.ones(window_len,'d')
        else:
            w = eval('np.'+window+'(window_len)')

        y = np.convolve(w/w.sum(),s,mode='valid')
        return np.round(y, decimals = 3)

    def consecutiveSum(self, arr, window_len):
        if arr.ndim != 1:
            raise ValueError("smooth only accepts 1 dimension arrays.")

        arrSize = arr.size

        if arrSize < window_len:
            length = arrSize
        length = window_len
        maxSum = np.float64(1.0)
        for i in range(length):
            maxSum += arr[i]
        windowSum = maxSum
        for i in range(length,arrSize):
            windowSum += arr[i] - arr[i - length]
            maxSum = np.maximum(maxSum, windowSum)
        return maxSum

    def labelSteps(self, datas, startPt = 30, rateTh = 0.3, width_LB = 15, avgRate_LB = 0.8):
        
        dataDiffs = np.diff(datas)

        listOfSteps = []
        inStep = False
        stepL = 0
        stepR = 0
        
        for cnt, diff in enumerate(dataDiffs):
            if cnt < startPt:
                continue
            if not inStep and diff >= rateTh:
                stepL = cnt
                inStep = True
                continue
            if inStep and (diff < rateTh or (cnt == len(dataDiffs) - 1)):
                stepR = cnt
                inStep = False
                LAMPStepFL = False
                stepDiff = 0
                if (stepR - stepL) >= width_LB:
                    index = stepL
                    while index <= stepR:
                        stepDiff = stepDiff + dataDiffs[index]
                        index += 1
                    avgRate = stepDiff / (stepR - stepL + 1)
                    LAMPStepFL = avgRate >= avgRate_LB
                step = [stepL, stepR, LAMPStepFL]
                stepL = cnt + 1
                listOfSteps.append(step)
                continue
        stepDiff = 0
        cp = 0
        maxDiff = 0
        maxIndex = 0
        stepWidth = 0
        for step in listOfSteps:
            if step[-1]:
                index = step[0] - 1
                stepWidth += step[1] - step[0] + 1

                # Accumulate signal increase of all Ture step as Step Diff
                while index < step[1] + 1:
                    stepDiff = stepDiff + dataDiffs[index]
                    # Capture time for highest diff as Cp
                    if dataDiffs[index] >= maxDiff:
                        maxDiff = dataDiffs[index]
                        maxIndex = index
                    index += 1
                if len(datas) > 10: cp = (maxIndex - datas[maxIndex + 1] / dataDiffs[maxIndex]) * 10 / 60 - 5
        avgRate = 0
        if stepWidth != 0: avgRate = stepDiff/stepWidth
        
        return listOfSteps, round(stepDiff, 1), round(cp, 1), round(stepWidth, 1), round(avgRate, 1)