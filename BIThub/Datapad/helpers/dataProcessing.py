from PyQt5 import QtWidgets, QtCore
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import sys  # We need sys so that we can pass argv to QApplication
import os
import numpy as np

def csvPlotter(folderPath, filename):

    print(os.path.splitext(os.path.basename(filename))[0])
    plt.style.use('seaborn-bright')

    plt.rc('axes', linewidth=2)
    font = {'weight' : 'bold',
    'size'   : 21}
    plt.rc('font', **font)

    x = []
    signalList = []
    y1 = []
    y2 = []
    y3 = []
    y4 = []
    y5 = []

    rlt = []
    idInfo = []
    ChResult = []
    OverallResult = ""

    with open(os.path.join(folderPath, filename),'r') as csvfile:
        plots = csv.reader(csvfile, delimiter=',')
        idx = 0

        for row in plots:
            if idx == 1:
                idInfo.append([row[0], row[2]])
                OverallResult = row[4]
            if idx == 8:
                x = row[7:]
                x = [float(i)/1000/60 - 5 for i in x]
            if idx == 11:
                ChResult.append(row[5])
                y1 = row[7:]
                rlt.append(row[6])
                y1 = np.array([float(i) for i in y1])
                if len(y1) >= 9: signalList.append(smooth(y1))
            if idx == 12:
                ChResult.append(row[5])
                y2 = row[7:]
                rlt.append(row[6])
                y2 = np.array([float(i) for i in y2])
                if len(y2) >= 9: signalList.append(smooth(y2))
            if idx == 13:
                ChResult.append(row[5])
                y3 = row[7:]
                rlt.append(row[6])
                y3 = np.array([float(i) for i in y3])
                if len(y3) >= 9: signalList.append(smooth(y3))
            if idx == 14:
                ChResult.append(row[5])
                y4 = row[7:]
                rlt.append(row[6])
                y4 = np.array([float(i) for i in y4])
                if len(y4) >= 9: signalList.append(smooth(y4))
            if idx == 15:
                ChResult.append(row[5])
                y5 = row[7:]
                rlt.append(row[6])
                y5 = np.array([float(i) for i in y5])
                if len(y5) >= 9: signalList.append(smooth(y5))

            idx += 1

    featList = np.zeros((5,4))

    if len(signalList) != 0:

        for i in range(5):
            _, diff, cp, stepWidth, avgRate= labelSteps(signalList[i])
            if diff == 0 and len(signalList[i]) >= 50:
                diff = round(consecutiveSum(np.diff(signalList[i]), 50), 1)
            featList[i] = [diff, cp, stepWidth, avgRate]

    plt.figure(num=None, figsize=(24, 6), dpi=40)
    ax = plt.subplot(111)
    ax.plot(x, y1, color = 'r', linewidth=2, label='PD1')
    ax.plot(x, y2, color = '#35ff35', linewidth=2, label='PD2')
    ax.plot(x, y3, color = '#3535ff', linewidth=2, label='PD3')
    ax.plot(x, y4, color = '#35ffff', linewidth=2, label='PD4')
    ax.plot(x, y5, color = '#ff35ff', linewidth=2, label='PD5')
    plt.xlabel('Time (mins)', fontsize = 19, fontweight = 'bold')
    plt.ylabel('Signal (mvs)', fontsize = 19, fontweight = 'bold')
    plt.title('{}_{}'.format(os.path.splitext(os.path.split(filename)[1])[0], OverallResult), fontsize = 20, fontweight = 'bold')
    box = ax.get_position()
    ax.set_position([box.x0*0.35, box.y0, box.width * 1.2, box.height])
    ax.grid(linestyle = '-.')
    ax.legend(loc='upper right',  ncol=5)
    # Print diffs data in plot
    diffs_text = 'Diffs(mvs) = PC:{}, N1:{}, N2:{}, M1:{}, M2:{}'.format\
    (featList[0][0], featList[1][0], featList[2][0], featList[3][0], featList[4][0])
    Tqs_text = 'Tqs(mins) = PC:{}, N1:{}, N2:{}, M1:{}, M2:{}'.format\
    (featList[0][1], featList[1][1], featList[2][1], featList[3][1], featList[4][1])
    plt.text(-2.5, 1100, diffs_text)
    plt.text(-2.5, 1000, Tqs_text)

    #ax.legend(loc='upper left')
    plt.axis([-5,45,40,1200])
    ax.xaxis.set_major_locator(MultipleLocator(5))
    ax.xaxis.set_major_formatter('{x:.0f}')
    ax.xaxis.set_minor_locator(MultipleLocator(2.5))

    ax.yaxis.set_major_locator(MultipleLocator(100))
    ax.yaxis.set_major_formatter('{x:.0f}')
    ax.yaxis.set_minor_locator(MultipleLocator(50))

    #plt.tight_layout()
    plt.savefig(os.path.join(folderPath, '{}_{}.png'.format(os.path.splitext(os.path.split(filename)[1])[0], OverallResult)))

    return idInfo, OverallResult, featList


class graphWidget(QtWidgets.QGraphicsView):

    def __init__(self, *args, **kargs):
        super(graphWidget, self).__init__(*args, **kargs)

        self.graphWidget = pg.PlotWidget()
        # self.setCentralWidget(self.graphWidget)

        #Add Background colour to white
        self.graphWidget.setBackground('w')
    
    def curvesPlot(self, testLog):
        self.graphWidget.clear()
        CHANNELNUM = 5
        time = testLog['ReactTime']
        targetName = testLog['TargetName']
        testId = testLog['TestId']
        input = testLog['Input']
        reactDataNameLs = ['Well1Readings','Well2Readings','Well3Readings','Well4Readings','Well5Readings']
        PD1, PD2, PD3, PD4, PD5 = [], [], [], [], []
        chList = [PD1, PD2, PD3, PD4, PD5]
        smoothedSignals = []
        for i in range(CHANNELNUM):
            chList[i] = testLog[reactDataNameLs[i]]
            smoothedSignals.append(self.smooth(np.array(chList[i])))

        featList = np.zeros((5,4))
        lnColorLs = ['r', '#35ff35', '#3535ff', '#35ffff', '#ff35ff']
        for i in range(CHANNELNUM):
            _, diff, cp, stepWidth, avgRate= self.labelSteps(smoothedSignals[i])
            if diff == 0 and len(smoothedSignals[i]) >= 50:
                diff = round(self.consecutiveSum(np.diff(smoothedSignals[i]), 50), 1)
            featList[i] = [diff, cp, stepWidth, avgRate]
            self.plot(time, chList[i], targetName[i], lnColorLs[i])

        # Add Title
        title = '{}_{}'.format(testId, input)
        self.graphWidget.setTitle(title, color='k')
        # Add Axis Labels
        styles = {"color": "k", "font-size": "20px"}
        self.graphWidget.setLabel("left", "SensorRead (mvs)", **styles)
        self.graphWidget.setLabel("bottom", "Time (secs)", **styles)
        #Add legend
        legend = self.graphWidget.addLegend()
        legend.setBrush('w')
        #Add grid
        self.graphWidget.showGrid(x=True, y=True)
        #Set Range
        self.graphWidget.setXRange(0, 1800, padding=0)
        self.graphWidget.setYRange(0, 600, padding=0)


    def plot(self, x, y, plotname, color):
        pen = pg.mkPen(color=color, width=2)
        self.graphWidget.plot(x, y, name=plotname, pen=pen)
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
        
        #if len(datas) >= 10:
        #	datas = smooth(datas)
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
                    #print(stepDiff, stepR, stepL)
                    avgRate = stepDiff / (stepR - stepL + 1)
                    #print(avgRate)
                    LAMPStepFL = avgRate >= avgRate_LB
                step = [stepL, stepR, LAMPStepFL]
                stepL = cnt + 1
                listOfSteps.append(step)
                continue
        #print(listOfSteps)
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

def main():
    app = QtWidgets.QApplication(sys.argv)
    client, testLogs = connectDB('thy_testsDB', 's2r_testlog')
    testLog = queryDB(testLogs, {"TestId": "2022-06-22_NABITA010.10_3"})
    client.close()
    MainWindow = QtWidgets.QMainWindow()
    MainWindow.setGeometry(200, 200, 1280, 360)

    graphW = graphWidget()
    MainWindow.setCentralWidget(graphW.graphWidget)

    graphW.curvesPlot(testLog)
    MainWindow.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    from dbOperations import *
    main()