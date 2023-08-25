import numpy as np
import os, csv, glob

def stdBounding(arr, multiplier = 80):
    evaInterval = 120 # secs
    samplingPeriod = 10 # 10 secs/sample
    gapPeriod = 360 # secs
    evaDatapt = int(evaInterval / samplingPeriod)
    gapDataPt = int(gapPeriod / samplingPeriod)

    indexMax = len(arr) - evaDatapt - gapDataPt - evaDatapt
    isIndicatedLst = []
    globalMin = 1500
    globalMax = 0
    for i in range(indexMax):
        base = np.mean(arr[i:i + evaDatapt - 1])
        if base < globalMin:
            globalMin = base
        base_std = np.std(arr[i: i + evaDatapt - 1])
        cur = np.mean(arr[i + evaDatapt + gapDataPt:i + 2 * evaDatapt + gapDataPt - 1])
        if cur > globalMax:
            globalMax = cur
        #if (round((cur - base) / base_std, 2) > multiplier):
            #print(str(round(cur - base, 2)), str(round((cur - base) / base_std, 2)), str(round(cur, 2)))
        if cur > base + base_std * multiplier:
            isIndicatedLst.append(True)
        else:
            isIndicatedLst.append(False)
    
    posTime = 0
    for i, isIndicated in enumerate(isIndicatedLst):
        if isIndicated == True:
            posTime = (i + evaDatapt + gapDataPt - 1) * 10 / 60
            break
    return round(posTime, 1), globalMin, globalMax

def results_processing(folderPath, filename):
    x = []
    signalList = []
    y1 = []
    y2 = []
    y3 = []
    y4 = []
    y5 = []


    with open(os.path.join(folderPath, filename),'r') as csvfile:
        plots = csv.reader(csvfile, delimiter=',')
        idx = 0

        for row in plots:

            if idx == 8:
                x = row[7:]
                x = [float(i)/1000/60 - 5 for i in x]
            if idx == 11:

                y1 = row[7:]
                y1 = np.array([float(i) for i in y1])
                if len(y1) >= 9: signalList.append(y1[30:])
            if idx == 12:

                y2 = row[7:]
                y2 = np.array([float(i) for i in y2])
                if len(y2) >= 9: signalList.append(y2[30:])
            if idx == 13:

                y3 = row[7:]
                y3 = np.array([float(i) for i in y3])
                if len(y3) >= 9: signalList.append(y3[30:])
            if idx == 14:

                y4 = row[7:]
                y4 = np.array([float(i) for i in y4])
                if len(y4) >= 9: signalList.append(y4[30:])
            if idx == 15:

                y5 = row[7:]
                y5 = np.array([float(i) for i in y5])
                if len(y5) >= 9: signalList.append(y5[30:])

            idx += 1
    posTimeLst = np.zeros((5,1))
    print(np.shape(signalList))

    if len(signalList) != 0:
        for i in range(5):
            # 
            print("Ch" + str(i+1))
            posTime, globalMin, globalMax = stdBounding(signalList[i])
            posTimeLst[i] = posTime

    resultsItem = "PosTime,{},{},{},{},{}\n".format(posTimeLst[0],\
    posTimeLst[1],posTimeLst[2],posTimeLst[3],posTimeLst[4])
    print(filename + "---" + resultsItem + "\n")

if __name__=='__main__':
    csvfoler = os.path.join(os.path.dirname(__file__), 'test_csv')
    filenames = sorted(glob.glob(os.path.join(csvfoler, '*.csv')))
    for filename in filenames:
        results_processing(csvfoler, filename)