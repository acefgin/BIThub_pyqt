import subprocess, sys
import os, glob, csv

from helpers.jsonWriteMongoDB import *

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
                splitPrapFlag = True

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

def readTestRsult(folderPath, filename):

    LysisTemp = []
    LysisTime = []
    CartTemp = []
    AdcTemp = []
    TargetName = []
    WellResult = []
    ECVolDiffs = []
    SampleId = ''
    CreatedDate = ''
    Barcode = ''

    ReactTime = []
    Well1Readings = []
    Well2Readings = []
    Well3Readings = []
    Well4Readings = []
    Well5Readings = []

    dcoument = {}

    with open(os.path.join(folderPath, filename),'r') as csvfile:
        plots = csv.reader(csvfile, delimiter=',')
        idx = 0
        headerDist = {}

        for row in plots:
            if idx == 0:
                for n, header in enumerate(row):
                    headerDist[header] = n
            if idx == 1:
                SampleId = row[headerDist["SampleId"]]
                Barcode = row[headerDist["Barcode"]]
                CreatedDate = row[headerDist["CreatedDate"]]
            if idx == 4:
                LysisTime = row[3:]
                LysisTime = [round(float(i)/1000, 2) for i in LysisTime if i != '']
            if idx == 5:
                LysisTemp = row[3:]
                LysisTemp = [round(float(i), 2) for i in LysisTemp if i != '']
            if idx == 8:
                ReactTime = row[7:]
                ReactTime = [round(float(i)/1000, 2) for i in ReactTime if i != '']
            if idx == 9:
                CartTemp = row[7:]
                CartTemp = [round(float(i), 2) for i in CartTemp if i != '']
            if idx == 10:
                AdcTemp = row[7:]
                AdcTemp = [round(float(i), 2) for i in AdcTemp if i != '']
            if idx == 11:
                TargetName.append(row[4])
                WellResult.append(row[5])
                ECVolDiffs.append(round(float(row[6]), 2))
                Well1Readings = row[7:]
                Well1Readings = [round(float(i), 2) for i in Well1Readings if i != '']

            if idx == 12:

                TargetName.append(row[4])
                WellResult.append(row[5])
                ECVolDiffs.append(round(float(row[6]), 2))
                Well2Readings = row[7:]   
                Well2Readings = [round(float(i), 2) for i in Well2Readings if i != '']

            if idx == 13:

                TargetName.append(row[4])
                WellResult.append(row[5])
                ECVolDiffs.append(round(float(row[6]), 2))
                Well3Readings = row[7:]
                Well3Readings = [round(float(i), 2) for i in Well3Readings if i != '']

            if idx == 14:

                TargetName.append(row[4])
                WellResult.append(row[5])
                ECVolDiffs.append(round(float(row[6]), 2))
                Well4Readings = row[7:]
                Well4Readings = [round(float(i), 2) for i in Well4Readings if i != '']

            if idx == 15:

                TargetName.append(row[4])
                WellResult.append(row[5])
                ECVolDiffs.append(round(float(row[6]), 2))
                Well5Readings = row[7:]
                Well5Readings = [round(float(i), 2) for i in Well5Readings if i != '']
            
            idx += 1

    dcoument["LysisTemp"] = LysisTemp
    dcoument["LysisTime"] = LysisTime
    dcoument["CartTemp"] = CartTemp
    dcoument["AdcTemp"] = AdcTemp
    dcoument["TargetName"] = TargetName
    dcoument["WellResult"] = WellResult
    dcoument["ECVolDiffs"] = ECVolDiffs
    dcoument["SampleId"] = SampleId
    dcoument["CreatedDate"] = CreatedDate
    dcoument["Barcode"] = Barcode

    dcoument["ReactTime"] = ReactTime
    dcoument["Well1Readings"] = Well1Readings
    dcoument["Well2Readings"] = Well2Readings
    dcoument["Well3Readings"] = Well3Readings
    dcoument["Well4Readings"] = Well4Readings
    dcoument["Well5Readings"] = Well5Readings

    return dcoument

def dateFormatting(dateString):
    text = dateString.split(' ')
    text = text[0].split('/')
    month = text[0]
    day = text[1]
    year = text[2]
    
    return year, month, day

def writeMongoDBFromDb(filePath):
    dbFilePath = filePath
    cwd = os.path.dirname(dbFilePath)
    cmd_str = f'.\\rET.exe {dbFilePath}'
    subprocess.run(cmd_str, shell=True)
    
    fileList = sorted(glob.glob(os.path.join(cwd, '*.csv')))
    filePath = fileList[0]
    
    deviceNum = '001'
    csvName = os.path.splitext(os.path.basename(filePath))[0]
    nameTxt = csvName.split("_")
    devicePrefix = 'NABITA{}'.format(deviceNum)
    datetimePrefix = '{}'.format(nameTxt[1])
    
    resultFolder = '{}_{}'.format(devicePrefix, datetimePrefix)
    savePath = os.path.join(cwd, resultFolder)
    if not os.path.isdir(savePath):
        os.mkdir(savePath)
    fileSplitter(filePath, devicePrefix, savePath)
    filenames = sorted(glob.glob(os.path.join(savePath, '*.csv')))
    jsonFile = "test.json"
    with open(jsonFile,'w') as file:

        idx = 1
        objList = []
        for filename in filenames:
            nameString = os.path.splitext(os.path.basename(filename))[0]
            print(str(idx) + ":" + nameString)
            text = nameString.split('-')
            deviceId = text[0]
            idx += 1
            # testDocument = testlogCollection[idxLookUp[testID]]
            resultDocument = readTestRsult(savePath, filename)
            createdDate = resultDocument['CreatedDate']
            print(createdDate)
            year, month, day = dateFormatting(createdDate)
            resultDocument['TestId'] = f'{year}-{month}-{day}_{deviceId}'
            print(resultDocument['TestId'])
            # Merge(resultDocument, testDocument)
            # objList.append(testDocument)
            objList.append(resultDocument)
            
        json.dump(objList, file, indent = 2)
    writeMongoDB(jsonFile)


if __name__=='__main__':
    
    # dbFilePath = sys.argv[1]
    # cwd = os.path.dirname(dbFilePath)
    # cmd_str = f'.\\rET.exe {dbFilePath}'
    # subprocess.run(cmd_str, shell=True)
    
    # fileList = sorted(glob.glob(os.path.join(cwd, '*.csv')))
    # filePath = fileList[0]
    
    # deviceNum = '001'
    # csvName = os.path.splitext(os.path.basename(filePath))[0]
    # nameTxt = csvName.split("_")
    # devicePrefix = 'NABITA{}'.format(deviceNum)
    # datetimePrefix = '{}'.format(nameTxt[1])
    
    # resultFolder = '{}_{}'.format(devicePrefix, datetimePrefix)
    # savePath = os.path.join(cwd, resultFolder)
    # if not os.path.isdir(savePath):
    #     os.mkdir(savePath)
    
    # fileSplitter(filePath, devicePrefix, savePath)
    savePath = 'C:\SynologyDrive\\repos\\Thy-resultDashboard\\NABITA001_202305231518'
    
    filenames = sorted(glob.glob(os.path.join(savePath, '*.csv')))
    
    # testlogFile = "S2R_testlog.csv"
    # testlogCollection = readTestlog(testlogFile)
    # idxLookUp = colSearch(testlogCollection)
    jsonFile = "test.json"
	
    with open(jsonFile,'w') as file:

        idx = 1
        objList = []
        for filename in filenames:
            nameString = os.path.splitext(os.path.basename(filename))[0]
            print(str(idx) + ":" + nameString)
            text = nameString.split('-')
            deviceId = text[0]
            idx += 1
            # testDocument = testlogCollection[idxLookUp[testID]]
            resultDocument = readTestRsult(savePath, filename)
            createdDate = resultDocument['CreatedDate']
            print(createdDate)
            year, month, day = dateFormatting(createdDate)
            resultDocument['TestId'] = f'{year}-{month}-{day}_{deviceId}'
            print(resultDocument['TestId'])
            # Merge(resultDocument, testDocument)
            # objList.append(testDocument)
            objList.append(resultDocument)
            
            
        json.dump(objList, file, indent = 2)
    # writeMongoDB(jsonFile)

    


