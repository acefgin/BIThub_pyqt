import numpy as np

class BITdetectMethods:
    def __init__(self):
        pass
    
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
        
        if len(datas) >= 10:
            smoothedDatas = self.smooth(np.array(datas))
        else:
            smoothedDatas = np.array(datas)
         
        dataDiffs = np.diff(smoothedDatas)

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
                if len(datas) > 10 : 
                    cp = (maxIndex - datas[maxIndex - 1] / dataDiffs[maxIndex]) * 10 / 60 - 5
        avgRate = 0
        if stepWidth != 0: avgRate = stepDiff/stepWidth
        
        return listOfSteps, round(stepDiff, 1), round(cp, 1), round(stepWidth, 1), round(avgRate, 1)

    def zNormArr(self, arr):
        baseline = round(np.mean(arr[30:60]), 2)
        sensorStd = round(np.std(arr[:30]) , 2)
        if sensorStd < 0.1:
            sensorStd = 0.1
        return (arr - baseline) / sensorStd, sensorStd

    def stdBounding(self, arr, multiplier = 80):
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

    def smooth(self, x, window_len=10,window='hanning'):
        """smooth the data using a window with requested size.

        This method is based on the convolution of a scaled window with the signal.
        The signal is prepared by introducing reflected copies of the signal
        (with the window size) in both ends so that transient parts are minimized
        in the begining and end part of the output signal.

        input:
            x: the input signal
            window_len: the dimension of the smoothing window; should be an odd integer
            window: the type of window from 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
                flat window will produce a moving average smoothing.

        output:
            the smoothed signal

        example:

        t=linspace(-2,2,0.1)
        x=sin(t)+randn(len(t))*0.1
        y=smooth(x)

        see also:

        numpy.hanning, numpy.hamming, numpy.bartlett, numpy.blackman, numpy.convolve
        scipy.signal.lfilter

        TODO: the window parameter could be the window itself if an array instead of a string
        NOTE: length(output) != length(input), to correct this: return y[(window_len/2-1):-(window_len/2)] instead of just y.
        """

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
'''
def curve_fit():

    def func(x, a, k, m, b):
        return a + (k - a) / (1 + np.exp(-b * (x - m)))


    time = []
    y1 = []
    y2 = []
    y3 = []
    y4 = []
    y5 = []
    timeLB = 10
    timeRB = 32.5

    with open("test_data2.csv",'r') as csvfile:
    	plots = csv.reader(csvfile, delimiter=',')
    	idx = 0

    	for row in plots:
    		if idx ==0:
    			idx += 1
    			continue
    		if float(row[0]) < timeLB or float(row[0]) > timeRB:
    			continue
    		time.append(float(row[0]))
    		y1.append(float(row[1]))
    		y2.append(float(row[2]))
    		y3.append(float(row[3]))
    		y4.append(float(row[4]))
    		y5.append(float(row[5]))
    yplot = y5
    plt.style.use('seaborn-bright')

    plt.rc('axes', linewidth=2)
    font = {'weight' : 'bold',
    'size'   : 18}
    plt.rc('font', **font)

    plt.figure(num=None, figsize=(16, 9), dpi=80)
    plt.plot(time, yplot, 'b-', label='data')

    popt, pcov = curve_fit(func, time, yplot)

    residuals = yplot - func(time, *popt)
    ss_res = np.sum(residuals**2)

    ss_tot = np.sum((yplot-np.mean(yplot))**2)
    r_squared = 1 - (ss_res / ss_tot)

    Tp = popt[2] - 2/popt[3]
    Beta_m = (popt[1] - popt[0]) / 2 / (popt[2] - Tp)

    plt.plot(time, func(time, *popt), 'r-',
             label='fit: a={}, k={}, m={}, b={}, Tp={}, \u03B2={}, R^2={}'.\
    		 format(round(popt[0], 2), round(popt[1], 2), \
    		 round(popt[2], 2), round(popt[3], 2), round(Tp,2), round(Beta_m, 2), \
    		 round(r_squared, 2)))

    plt.xlabel('Time(mins)', fontsize = 18, fontweight = 'bold')
    plt.ylabel('Signal(mvs)', fontsize = 18, fontweight = 'bold')
    plt.legend(loc='upper left')

    plt.show()
'''