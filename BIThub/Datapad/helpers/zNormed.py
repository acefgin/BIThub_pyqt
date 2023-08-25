import numpy as np
import os, csv, glob

import matplotlib.pyplot as plt
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)

from stdBounding import *
from slidingWin import *
from stepsFilter import *

def zNormArr(arr):
    baseline = round(np.mean(arr[30:60]), 2)
    sensorStd = round(np.std(arr[:30]) , 2)
    if sensorStd < 0.1:
        sensorStd = 0.1
    return (arr - baseline) / sensorStd, sensorStd

def results_processing(folderPath, filename):

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
    OverallResult = ""

    with open(os.path.join(folderPath, filename),'r') as csvfile:
        plots = csv.reader(csvfile, delimiter=',')
        idx = 0

        for row in plots:
            if idx == 1:
                OverallResult = row[4]
            if idx == 8:
                x = row[7:]
                x = [float(i)/1000/60 - 5 for i in x if i != '']
            if idx == 11:

                y1 = row[7:]
                y1 = np.array([float(i) for i in y1 if i != ''])
                yNormed, PD1Scalar = zNormArr(y1)
                signalList.append(yNormed)
            if idx == 12:

                y2 = row[7:]
                y2 = np.array([float(i) for i in y2 if i != ''])
                yNormed, PD2Scalar = zNormArr(y2)
                signalList.append(yNormed)
            if idx == 13:

                y3 = row[7:]
                y3 = np.array([float(i) for i in y3 if i != ''])
                yNormed, PD3Scalar = zNormArr(y3)
                signalList.append(yNormed)
            if idx == 14:

                y4 = row[7:]
                y4 = np.array([float(i) for i in y4 if i != ''])
                yNormed, PD4Scalar = zNormArr(y4)
                signalList.append(yNormed)
            if idx == 15:

                y5 = row[7:]
                y5 = np.array([float(i) for i in y5 if i != ''])
                yNormed, PD5Scalar = zNormArr(y5)
                signalList.append(yNormed)
            
            idx += 1
    avgScalar = (PD1Scalar + PD2Scalar + PD3Scalar + PD4Scalar + PD5Scalar) / 5
    print("test scalar: " + str(round(avgScalar, 2)))
    for i in range(len(signalList)):
        signalList[i] = signalList[i] * avgScalar
    
    featList = np.zeros((5,4))
    #print(np.shape(signalList))

    if len(signalList) != 0:
        for i in range(5):
            _, diff, cp, stepWidth, avgRate= labelSteps(signalList[i])
            print(_)
            if diff == 0 and len(signalList[i]) >= 50:
                diff = round(consecutiveSum(np.diff(signalList[i]), 50), 1)
            featList[i] = [diff, cp, stepWidth, avgRate]

    plt.figure(num=None, figsize=(24, 6), dpi=40)
    ax = plt.subplot(111)
    ax.plot(x, signalList[0], color = 'r', linewidth=2, label='PC')
    ax.plot(x, signalList[1], color = '#35ff35', linewidth=2, label='N1')
    ax.plot(x, signalList[2], color = '#3535ff', linewidth=2, label='N2')
    ax.plot(x, signalList[3], color = '#35ffff', linewidth=2, label='M1')
    ax.plot(x, signalList[4], color = '#ff35ff', linewidth=2, label='M2')
    plt.xlabel('Time (mins)', fontsize = 19, fontweight = 'bold')
    plt.ylabel('Normalized Signal', fontsize = 19, fontweight = 'bold')
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
    plt.text(-2.5, 280, diffs_text)
    plt.text(-2.5, 240, Tqs_text)


    #ax.legend(loc='upper left')
    plt.axis([-5,30,-5,315])
    ax.xaxis.set_major_locator(MultipleLocator(2))
    ax.xaxis.set_major_formatter('{x:.0f}')
    ax.xaxis.set_minor_locator(MultipleLocator(1))

    ax.yaxis.set_major_locator(MultipleLocator(40))
    ax.yaxis.set_major_formatter('{x:.0f}')
    ax.yaxis.set_minor_locator(MultipleLocator(20))


    #plt.tight_layout()
    plt.savefig(os.path.join(folderPath, '{}-{}.png'.format(os.path.splitext(os.path.split(filename)[1])[0], OverallResult)))




if __name__=='__main__':
    csvfoler = os.path.join(os.path.dirname(__file__), 'test_csv')
    filenames = sorted(glob.glob(os.path.join(csvfoler, '*.csv')))
    for filename in filenames:
        print(filename)
        results_processing(csvfoler, filename)