import matplotlib.pyplot as plt
import os, csv, glob
#from scipy.optimize import curve_fit
#import numpy as np

def results_processing(datas):
	volDiffs = np.zeros(5)
	results = np.zeros(5)
	threshold = 12
	for i in range(5):
		# Define sensor reading raise as maximum sum of consecutive diff subarray of size 50
		volDiffs[i] = consecutiveSum(np.diff(smooth(datas[i])), 50)
	results = np.greater_equal(volDiffs, threshold)

	volDiffsItem = "Voltage difference,{},{},{},{},{}\n".format(round(volDiffs[0], 1),\
		round(volDiffs[1], 1),round(volDiffs[2], 1),round(volDiffs[3], 1),round(volDiffs[4], 1))
	print(volDiffsItem)

	resultsItem = "Result,{},{},{},{},{}\n".format(results[0],\
		results[1],results[2],results[3],results[4])
	print(resultsItem)

def smooth(x,window_len=10,window='hanning'):
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
	y = np.round(y, decimals = 3)
	return y[window_len/2 - 1:- (window_len/2)]


def consecutiveSum(arr, window_len):
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



def csvPlotter(folderPath, filename):

	plt.style.use('seaborn-bright')

	plt.rc('axes', linewidth=2)
	font = {'weight' : 'bold',
	'size'   : 16}
	plt.rc('font', **font)

	x = []
	y1 = []
	y2 = []
	y3 = []
	y4 = []
	y5 = []
	rlt = []
	OverallResult = []

	with open(os.path.join(folderPath, filename),'r') as csvfile:
		plots = csv.reader(csvfile, delimiter=',')
		idx = 0

		for row in plots:
			if idx == 1:
				OverallResult.append(row[4])
			if idx == 8:
				x = row[7:]
				x = [float(i)/1000/60 - 5 for i in x]
			if idx == 11:
				y1 = row[7:]
				rlt.append(row[6])
				y1 = [float(i) for i in y1]
			if idx == 12:
				y2 = row[7:]
				rlt.append(row[6])
				y2 = [float(i) for i in y2]
			if idx == 13:
				y3 = row[7:]
				rlt.append(row[6])
				y3 = [float(i) for i in y3]
			if idx == 14:
				y4 = row[7:]
				rlt.append(row[6])
				y4 = [float(i) for i in y4]
			if idx == 15:
				y5 = row[7:]
				rlt.append(row[6])
				y5 = [float(i) for i in y5]

			idx += 1

	plt.figure(num=None, figsize=(24, 6), dpi=80)
	ax = plt.subplot(111)
	ax.plot(x, y1, color = 'r', linewidth=2, label='PC')
	ax.plot(x, y2, color = '#35ff35', linewidth=2, label='N1')
	ax.plot(x, y3, color = '#3535ff', linewidth=2, label='N2')
	ax.plot(x, y4, color = '#35ffff', linewidth=2, label='M1')
	ax.plot(x, y5, color = '#ff35ff', linewidth=2, label='M2')
	plt.xlabel('Time (mins)', fontsize = 20, fontweight = 'bold')
	plt.ylabel('Signal (mvs)', fontsize = 20, fontweight = 'bold')
	plt.title('{}: Raw signal readings'.format(os.path.splitext(os.path.split(filename)[1])[0]), fontsize = 20, fontweight = 'bold')
	box = ax.get_position()
	ax.set_position([box.x0*0.35, box.y0, box.width * 1.2, box.height])
	ax.grid(linestyle = '-.')
	ax.legend(loc='lower right',  ncol=5)
	rlt_text = 'Diffs = PC:{}, N1:{}, N2:{}, M1:{}, M2:{}'.format\
	(rlt[0], rlt[1], rlt[2], rlt[3], rlt[4])
	plt.text(-2.5, 140, rlt_text)
	#ax.legend(loc='upper left')
	plt.axis([-5,30,20,180])
	#plt.tight_layout()
	plt.savefig(os.path.join(folderPath, '{}_{}.png'.format(os.path.splitext(os.path.split(filename)[1])[0], OverallResult[0])))

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
if __name__=='__main__':

	csvfoler = os.path.join(os.path.dirname(__file__), 'RDR_csv')
	filenames = sorted(glob.glob(os.path.join(csvfoler, 'RDR_*.csv')))
	for filename in filenames:
		csvPlotter(csvfoler, filename)
