import os, csv, glob

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)

from slidingWin import *
from stepsFilter import *

import sys

def csvPlotter(folderPath, filename, yMin, yMax):

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
        headerDist = {}

        for row in plots:
            if idx == 0:
                for n, header in enumerate(row):
                    headerDist[header] = n
            if idx == 1:
                idInfo.append([row[0], row[headerDist["Barcode"]]])
                OverallResult = row[headerDist["OverallResult"]]
            if idx == 8:
                x = row[7:]
                x = [float(i)/1000/60 - 5 for i in x]
            if idx == 11:
                ChResult.append(row[5])
                y1 = row[7:]
                rlt.append(row[6])
                y1 = np.array([float(i) for i in y1])
                if len(y1) >= 9: signalList.append(y1)
            if idx == 12:
                ChResult.append(row[5])
                y2 = row[7:]
                rlt.append(row[6])
                y2 = np.array([float(i) for i in y2])
                if len(y2) >= 9: signalList.append(y2)
            if idx == 13:
                ChResult.append(row[5])
                y3 = row[7:]
                rlt.append(row[6])
                y3 = np.array([float(i) for i in y3])
                if len(y3) >= 9: signalList.append(y3)
            if idx == 14:
                ChResult.append(row[5])
                y4 = row[7:]
                rlt.append(row[6])
                y4 = np.array([float(i) for i in y4])
                if len(y4) >= 9: signalList.append(y4)
            if idx == 15:
                ChResult.append(row[5])
                y5 = row[7:]
                rlt.append(row[6])
                y5 = np.array([float(i) for i in y5])
                if len(y5) >= 9: signalList.append(y5)

            idx += 1

    featList = np.zeros((5,5))

    if len(signalList) != 0:

        for i in range(5):
            _, diff, cp, stepWidth, avgRate, maxDiff= labelSteps(signalList[i])
            if diff == 0 and len(signalList[i]) >= 50:
                diff = round(consecutiveSum(np.diff(signalList[i]), 50), 1)
            featList[i] = [diff, cp, stepWidth, avgRate, maxDiff]


    return idInfo, OverallResult, featList

def fileSplitter(filename, devicePrefix, savePath):
    headers = []
    testInfos = []
    lysisData = []
    detectData = []

    with open(filename,'r') as multiTests:
        rows = csv.reader(multiTests, delimiter=',')
        status = 0
        invalidSet = set()
        headerDist = {}
        splitPrapFlag = False

        for row in rows:
            if not splitPrapFlag:
                for n, header in enumerate(row):
                    headerDist[header] = n

            if len(row) == 0:
                status += 1
            elif row[0] == 'SampleId':
                headers.append(row)
                continue
            elif status == 0:
                if row[headerDist["OverallResult"]] == 'Unspecified':
                    invalidSet.add(row[headerDist["RunId"]])
                    continue
                testInfos.append(row)
            elif status == 1:
                if row[1] in invalidSet:
                    continue
                lysisData.append(row)
            elif status == 2:
                if row[1] in invalidSet:
                    continue
                detectData.append(row)

        for testNum in range(len(testInfos)):

            newFile = os.path.join(savePath, '{}_{}-{}-{}.csv'.format( \
                devicePrefix, testInfos[testNum][headerDist["RunId"]], \
                testInfos[testNum][headerDist["Barcode"]], \
                testInfos[testNum][headerDist["SampleId"]]))
            if os.path.isfile(newFile):
                continue
            with open(newFile,'w', newline = '') as slgTest:
                writer = csv.writer(slgTest)
                writer.writerow(headers[0])
                writer.writerow(testInfos[testNum])
                writer.writerow('\n')
                writer.writerow(headers[1])

                for i in range(2):
                    writer.writerow(lysisData[2 * testNum + i])
                writer.writerow('\n')
                writer.writerow(headers[2])
                for i in range(8):
                    writer.writerow(detectData[8 * testNum + i])

if __name__=='__main__':

    filePath = sys.argv[1]
    csvName = os.path.splitext(os.path.basename(filePath))[0]
    deviceNum = '000'
    yMin = '20'
    yMax = '480'

    nameTxt = csvName.split("_")

    cwd = os.path.dirname(filePath)

    devicePrefix = 'NABITA{}'.format(deviceNum)
    datetimePrefix = '{}'.format(nameTxt[1])

    resultFolder = '{}_{}'.format(devicePrefix, datetimePrefix)
    savePath = os.path.join(cwd, resultFolder)

    if not os.path.isdir(savePath):
        os.mkdir(savePath)

    filename = '{}.csv'.format(csvName)
    print(filePath, filename)
    fileSplitter(filePath, devicePrefix, savePath)

    filenames = sorted(glob.glob(os.path.join(savePath, '*.csv')))

    reportcsvFile = os.path.join(savePath, '{}_report.csv'.format(resultFolder))
    header = ["SampleID", "Barcode", "Result", "PD1", "PD2", "PD3", "PD4", "PD5"]
    with open(reportcsvFile,'w', newline = '') as reportCsv:
        writer = csv.writer(reportCsv)
        writer.writerow(header)

        for filename in filenames:

            idInfo, overallRlt, featList = csvPlotter(savePath, filename, int(yMin), int(yMax))
            data2Write = [idInfo[0][0], idInfo[0][1], overallRlt]
            for i in range(5):
                data2Write.append(str(featList[i][0]))
            writer.writerow(data2Write)

        writer.writerow('\n')
    input('Press <Enter> to exit')
