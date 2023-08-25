#import matplotlib.pyplot as plt
import numpy as np
import os, csv, glob

def labelSteps(datas, startPt = 30, rateTh = 0.3, width_LB = 15, avgRate_LB = 0.8):
	
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

def results_processing(datas):
	volDiffs = np.zeros(5)
	results = np.zeros(5)
	diff_threshold = 0.8
	threshold = 12
	for i in range(5):
		# Define sensor reading raise as maximum sum of consecutive diff subarray of size 100
		volDiffs[i] = consecutiveSum(np.diff(smooth(datas[i])), 100)
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
	return np.round(y, decimals = 3)

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
				y1 = np.array([float(i) for i in y1])
				y1 = smooth(y1)
				y1_diff = np.diff(y1)
			if idx == 12:
				y2 = row[7:]
				rlt.append(row[6])
				y2 = np.array([float(i) for i in y2])
				y2 = smooth(y2)
				y2_diff = np.diff(y2)
			if idx == 13:
				y3 = row[7:]
				rlt.append(row[6])
				y3 = np.array([float(i) for i in y3])
				y3 = smooth(y3)
				y3_diff = np.diff(y3)
			if idx == 14:
				y4 = row[7:]
				rlt.append(row[6])
				y4 = np.array([float(i) for i in y4])
				y4 = smooth(y4)
				y4_diff = np.diff(y4)
			if idx == 15:
				y5 = row[7:]
				rlt.append(row[6])
				y5 = np.array([float(i) for i in y5])
				y5 = smooth(y5)
				y5_diff = np.diff(y5)

			idx += 1

	y1_steps, y1_Diff, y1_cp = labelSteps(y1)
	y2_steps, y2_Diff, y2_cp = labelSteps(y2)
	y3_steps, y3_Diff, y3_cp = labelSteps(y3)
	y4_steps, y4_Diff, y4_cp = labelSteps(y4)
	y5_steps, y5_Diff, y5_cp = labelSteps(y5)

	plt.figure(num=None, figsize=(24, 12), dpi=80)

	ax = plt.subplot(211)
	ax.plot(x, y1[4:-4], color = 'r', linewidth=2, label='PC')
	ax.plot(x, y2[4:-4], color = '#35ff35', linewidth=2, label='N1')
	ax.plot(x, y3[4:-4], color = '#3535ff', linewidth=2, label='N2')
	ax.plot(x, y4[4:-4], color = '#35ffff', linewidth=2, label='M1')
	ax.plot(x, y5[4:-4], color = '#ff35ff', linewidth=2, label='M2')
	ax.set_ylabel('Signal (mvs)', fontsize = 20, fontweight = 'bold')
	plt.title('{}: derivative'.format(os.path.splitext(os.path.split(filename)[1])[0]), fontsize = 20, fontweight = 'bold')
	box = ax.get_position()
	ax.set_position([box.x0*0.35, box.y0, box.width * 1.2, box.height])
	ax.grid(linestyle = '-.')
	ax.legend(loc='lower right',  ncol=5)
	rlt_text = 'Diffs = PC:{}, N1:{}, N2:{}, M1:{}, M2:{}'.format\
	(rlt[0], rlt[1], rlt[2], rlt[3], rlt[4])
	ax.text(-2.5, 800, rlt_text)
	#ax.legend(loc='upper left')
	ax.axis([-5,30,20,1000])
	#plt.tight_layout()

	bx = plt.subplot(212)
	#plt.title('{}: derivative'.format(os.path.splitext(os.path.split(filename)[1])[0]), fontsize = 20, fontweight = 'bold')
	bx.plot(x[:-1], y1_diff[4:-4], color = 'r', linewidth=2, label='PC_diff')
	bx.plot(x[:-1], y2_diff[4:-4], color = '#35ff35', linewidth=2, label='N1_diff')
	bx.plot(x[:-1], y3_diff[4:-4], color = '#3535ff', linewidth=2, label='N2_diff')
	bx.plot(x[:-1], y4_diff[4:-4], color = '#35ffff', linewidth=2, label='M1_diff')
	bx.plot(x[:-1], y5_diff[4:-4], color = '#ff35ff', linewidth=2, label='M2_diff')
	bx.axis([-5,30,-8,16])
	bx.set_ylabel('Signal diff (mvs)', fontsize = 20, fontweight = 'bold')
	bx.set_xlabel('Time (mins)', fontsize = 20, fontweight = 'bold')
	box = bx.get_position()
	bx.set_position([box.x0*0.35, box.y0, box.width * 1.2, box.height])
	bx.grid(linestyle = '-.')
	bx.legend(loc='lower right',  ncol=5)
	step_text = 'PC:diff[{}]-cp[{}]-{}\nN1:diff[{}]-cp[{}]-{}\nN2:diff[{}]-cp[{}]-{}\nM1:diff[{}]-cp[{}]-{}\nM2:diff[{}]-cp[{}]-{}\n'.format\
	(y1_Diff, y1_cp, y1_steps, y2_Diff, y2_cp, y2_steps, y3_Diff, y3_cp, \
	y3_steps, y4_Diff, y4_cp, y4_steps, y5_Diff, y5_cp, y5_steps)
	bx.text(-4, 2, step_text)

	plt.savefig(os.path.join(folderPath, '{}_{}.png'.format(os.path.splitext(os.path.split(filename)[1])[0], OverallResult[0])))

if __name__=='__main__':

	csvfoler = os.path.join(os.path.dirname(__file__), 'spike analysis')
	filenames = sorted(glob.glob(os.path.join(csvfoler, '*.csv')))
	for filename in filenames:
		csvPlotter(csvfoler, filename)
