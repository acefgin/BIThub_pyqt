import os, sqlite3
import paramiko, sqlalchemy
import pandas as pd

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)
     
from PyQt5.QtWidgets import QApplication, QListWidget
from PyQt5.QtCore import pyqtSignal

from helpers.detectMethods import BITdetectMethods
from helpers.gsOps import GSheetObj

# A wrapper of paramiko.SSHClient to execute command with sudo
class SshClient:
    TIMEOUT = 4

    def __init__(self, host, port, username, password, key=None, passphrase=None):
        self.username = username
        self.password = password
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if key is not None:
            key = paramiko.RSAKey.from_private_key(StringIO(key), password=passphrase)
        self.client.connect(host, port, username=username, password=password, pkey=key, timeout=self.TIMEOUT)

    def close(self):
        if self.client is not None:
            self.client.close()
            self.client = None

    def execute(self, command, sudo=False):
        feed_password = False
        if sudo and self.username != "root":
            command = "sudo -S -p '' %s" % command
            feed_password = self.password is not None and len(self.password) > 0
        stdin, stdout, stderr = self.client.exec_command(command)
        if feed_password:
            stdin.write(self.password + "\n")
            stdin.flush()
        return {'out': stdout.readlines(), 
                'err': stderr.readlines(),
                'retval': stdout.channel.recv_exit_status()}   
        
# custom sftp client to allow directory upload
class MySFTPClient(paramiko.SFTPClient):
    def put_dir(self, source, target):
        ''' Uploads the contents of the source directory to the target path. The
            target directory needs to exists. All subdirectories in source are 
            created under target.
        '''
        for item in os.listdir(source):
            if os.path.isfile(os.path.join(source, item)):
                self.put(os.path.join(source, item), '%s/%s' % (target, item))
            else:
                self.mkdir('%s/%s' % (target, item), ignore_existing=True)
                self.put_dir(os.path.join(source, item), '%s/%s' % (target, item))
    def get_dir(self, remote_dir, local_dir):
        os.path.exists(local_dir) or os.makedirs(local_dir)
        dir_items = self.listdir_attr(remote_dir)
        for item in dir_items:
            # assuming the local system is Windows and the remote system is Linux
            # os.path.join won't help here, so construct remote_path manually
            remote_path = remote_dir + '/' + item.filename
            name = item.filename.split(' ')[0] + '.csv'
            local_path = os.path.join(local_dir, name)
            if stat.S_ISDIR(item.st_mode):
                self.get_dir(remote_path, local_path)
            else:
                self.get(remote_path, local_path)
        

    def mkdir(self, path, mode=511, ignore_existing=False):
        ''' Augments mkdir by adding an option to not fail if the folder exists  '''
        try:
            super(MySFTPClient, self).mkdir(path, mode)
        except IOError:
            if ignore_existing:
                pass
            else:
                raise

def getDb():
    host = '169.254.21.151'
    username = 'torizon'
    password = 'torizon1'
    ssh = SshClient(host, 22, username, password)
    dbPath = 'cxldnabit_web:/sqlite/cxl.db'
    stdin, stdout, stderr = ssh.client.exec_command(f'docker cp {dbPath} /var/rootdirs/home/torizon')
    exit_status = stdout.channel.recv_exit_status() 
    
    # config sftp
    dirSource = '/var/rootdirs/home/torizon/cxl.db'
    target = os.path.join(os.getcwd(), 'cxl.db')
    sftp = MySFTPClient.from_transport(ssh.client.get_transport())
    if exit_status == 0:
        sftp.get(dirSource, target)
    else:
        print('Failed to copy db file')
    ssh.client.exec_command('rm /var/rootdirs/home/torizon//cxl.db')

def sql2Dataframes():
    db_name = "cxl.db"
    table_name = ['Runs', 'TargetResults', 'Readings', 'LysisReadings','AssayDefinitions']
    dfDict = {}

    engine = sqlalchemy.create_engine("sqlite:///%s" % db_name, execution_options={"sqlite_raw_colnames": True})
    for table in table_name:
        df = pd.read_sql_table(table, engine)
        dfDict[table] = df
    return dfDict


USER_CANCELLED = 0
POS = 1
NEG = 2
UNDEFINED = 3
INVALID = 4

class BIT_Runs:
    def __init__(self, dfDict):
        self.dfDict = dfDict
        self.runsInfo = None
        self.getIdList(dfDict)
        self.CHANNELNUM = 5
        self.gs = None
        try:
            self.gs = GSheetObj()
            print(self.gs)
        except Exception as e:
            print(f"Google Sheets disabled: {e}")
    
    def getIdList(self, dfDict):
        runsTb = dfDict['Runs']
        assayTb = dfDict['AssayDefinitions']
        self.runsInfo = runsTb.join(assayTb[['Id', 'Name', 'Version']].set_index('Id'), on='AssayDefinitionId', lsuffix='_r', rsuffix='_a')
        self.runsInfo.reset_index()
        for index, row in self.runsInfo.iterrows():
            if row['Result'] == 0:
                self.runsInfo.drop(index, inplace=True)
        
        self.fullIdList = self.runsInfo['Id'].values
    
    def exportRuns(self, runIdList = None , exportPath = None):
        if runIdList is None:
            runIdList = self.fullIdList
        if exportPath is None:
            exportPath = os.getcwd()
            
        for runId in runIdList:
            
            run = self.getRun(runId)
            
            plt, plotTitle = self.plotter(run)
            self.csvBuilder(run, exportPath, plotTitle)
            
            savePath = os.path.join(exportPath, 'plots')
            if not os.path.isdir(savePath):
                os.mkdir(savePath)
            plt.savefig(os.path.join(savePath, f'{plotTitle}.png'))
    
    def logRun2GSheet(self, runId, userinputs):
        if self.gs is None:
            print("Google Sheets is not available")
            return False
        run = self.getRun(runId)
        self.gs.logRun(run, userinputs)
        return True
            
    def csvBuilder(self, run, exportPath, title):
        testInfo, lysisReads, detectReads = run
        
        savePath = os.path.join(exportPath, 'csvs')
        if not os.path.isdir(savePath):
            os.mkdir(savePath)
        
        csvFileName = f'{title}.csv'
        csvFile = os.path.join(savePath, csvFileName)
        
        with open(csvFile,'w', newline = '') as file:
            header = ''
            data = ''
            
            for key, value in testInfo.items():
                header += f'{key},'
                data += f'{value},'
            header = header[:-1] + '\n'
            data = data[:-1] + '\n'
            file.write(header)
            file.write(data)
            file.write('\n')
            
            file.write('LysisType,LysisReadings\n')
            file.write('Time,'+','.join(map(str, lysisReads[0]))+'\n')
            file.write('Temp,'+','.join(map(str, lysisReads[1]))+'\n')
            file.write('\n')
            file.write('Well,Type,TargetName,Result,VoltageDifference,Readings\n')
            file.write(',Time,,,,'+','.join(map(str, detectReads['Time']))+'\n')
            file.write(',CartTemp,,,,'+','.join(map(str, detectReads['CartTemp']))+'\n')
            file.write(',AdcTemp,,,,'+','.join(map(str, detectReads['AdcTemp']))+'\n')
            for i in range(self.CHANNELNUM):
                well = detectReads['Well'][i]
                targetName = detectReads['Target'][i]
                result = 'Amplified' if detectReads['ChResult'][i] == 1 else 'NotAmplified'
                voltageDifference = detectReads['ChVolDiff'][i]
                signal = detectReads['Signals'][i]
                file.write(f'{well},Target,{targetName},{result},{voltageDifference},'+','.join(map(str, signal))+'\n')
    
    def plotter(self, run):
        plt.style.use('seaborn-v0_8-bright')

        plt.rc('axes', linewidth=2)
        font = {'weight' : 'bold',
        'size'   : 21}
        plt.rc('font', **font)
        testInfo, lysisReads, detectReads = run
        bitMath = BITdetectMethods()
        
        time = detectReads['Time']
        signalList = detectReads['Signals']

        x = time / 60000 - 5
        yMin, yMax = 0, 500

        sampleId, barcode, ChLabel, OverallResult = testInfo['SampleId'], testInfo['Barcode'], detectReads['Target'], testInfo['OverallResult']
        
        assayName = testInfo['Assay.Name']

        featList = np.zeros((5,4))

        if len(signalList) != 0:

            for i in range(self.CHANNELNUM):
                _, diff, cp, stepWidth, avgRate = bitMath.labelSteps(signalList[i])
                    
                if diff == 0 and len(signalList[i]) >= 50:
                    diff = round(bitMath.consecutiveSum(np.diff(signalList[i]), 50), 1)
                featList[i] = [diff, cp, stepWidth, avgRate]

        plt.figure(num=None, figsize=(24, 6), dpi=60)
        ax = plt.subplot(111)
        penList = ['r', '#35ff35', '#3535ff', '#35ffff', '#ff35ff']
        for i in range(self.CHANNELNUM):
            ax.plot(x, signalList[i], color = penList[i], linewidth=2, label=ChLabel[i])

        plt.xlabel('Time (mins)', fontsize = 19, fontweight = 'bold')
        plt.ylabel('Signal (mvs)', fontsize = 19, fontweight = 'bold')
        
        if assayName != 'Dev_Mode':
            title = f'{sampleId}-{barcode}-{OverallResult}'
        else:
            title = f'{sampleId}-{barcode}-{assayName}'
        plt.title(title, fontsize = 20, fontweight = 'bold')
        box = ax.get_position()
        ax.set_position([box.x0*0.35, box.y0, box.width * 1.2, box.height])
        ax.grid(linestyle = '-.')
        ax.legend(loc='upper right',  ncol=1)
        
        # Print diffs data in plot
        diffs_text = f'Diffs(mvs) = Ch1:{featList[0][0]}, Ch2:{featList[1][0]}, Ch3:{featList[2][0]}, Ch4:{featList[3][0]}, Ch5:{featList[4][0]}'
        Tqs_text = f'Tqs(mins) = Ch1:{featList[0][1]}, Ch2:{featList[1][1]}, Ch3:{featList[2][1]}, Ch4:{featList[3][1]}, Ch5:{featList[4][1]}'
        avgRate_text = f'avgRate(C/10sec) = Ch1:{featList[0][3]}, Ch2:{featList[1][3]}, Ch3:{featList[2][3]}, Ch4:{featList[3][3]}, Ch5:{featList[4][3]}'
        
        text_location = int(0.9 * yMax)
        lineSpace = int((yMax - yMin)* 0.1)
        plt.text(-4, text_location, diffs_text)
        plt.text(-4, text_location - lineSpace, Tqs_text)
        plt.text(-4, text_location - 2 * lineSpace, avgRate_text)

        plt.axis([-5,30, yMin, yMax])
        ax.xaxis.set_major_locator(MultipleLocator(5))
        ax.xaxis.set_major_formatter('{x:.0f}')
        ax.xaxis.set_minor_locator(MultipleLocator(2.5))

        major_locator = (yMax - yMin) / 10
        ax.yaxis.set_major_locator(MultipleLocator(major_locator))
        ax.yaxis.set_major_formatter('{x:.0f}')
        ax.yaxis.set_minor_locator(MultipleLocator(major_locator / 2))

        return plt, title
                    
    def getRun(self, runId):
        # runId type is INT
        run = self.runQuery(int(runId))
        return run
    
    def runQuery(self, runId):
        runsTb, targetTb, readsTb = self.dfDict['Runs'], self.dfDict['TargetResults'], self.dfDict['Readings']
        lysisTb, assayTb = self.dfDict['LysisReadings'], self.dfDict['AssayDefinitions']
        
        targetRow = runsTb.loc[runsTb['Id'] == runId]
        
        sampleId, barcode, createdDate, comments, assayId, OverallResult = targetRow[['SampleId', 'Barcode', 'CreatedDate', 'Comments', 'AssayDefinitionId', 'Result']].values[0]
        
        overallResultStr = None
        
        if OverallResult == POS:
            overallResultStr = 'POS'
        elif OverallResult == NEG:
            overallResultStr = 'NEG'
        elif OverallResult == UNDEFINED:
            overallResultStr = 'UNDEFINED'
        elif OverallResult == INVALID:
            overallResultStr = 'INVALID'
        
        assayName = assayTb.loc[assayTb['Id'] == assayId]['Name'].values[0]
        assayVersion = assayTb.loc[assayTb['Id'] == assayId]['Version'].values[0]
        
        lysisTime = lysisTb.loc[lysisTb['RunId'] == runId]['TimeOffsetMs'].values
        lysisTemp = lysisTb.loc[lysisTb['RunId'] == runId]['Temperature'].values
        
        # dectect reads
        # target and reuslt
        Wells = targetTb.loc[targetTb['RunId'] == runId]['Well'].values
        ChLabel = targetTb.loc[targetTb['RunId'] == runId]['Name'].values
        ChResult = targetTb.loc[targetTb['RunId'] == runId]['Result'].values
        ChVolDiff = targetTb.loc[targetTb['RunId'] == runId]['VoltageDifference'].values
        
        # temperature
        cartTemp = readsTb.loc[readsTb['RunId'] == runId]['CartTemp'].values
        adcTemp = readsTb.loc[readsTb['RunId'] == runId]['AdcTemp'].values
        
        # PD reads
        detectTime = readsTb.loc[readsTb['RunId'] == runId]['TimeOffsetMs'].values
        chList = ['PD1', 'PD2', 'PD3', 'PD4', 'PD5']
        pdReads = []
        for ch in chList:
            signal = readsTb.loc[readsTb['RunId'] == runId][ch].values
            pdReads.append(signal)


        testInfo = {'SampleId': sampleId, 'Barcode': barcode, 'CreatedDate': createdDate, 'OverallResult': \
            overallResultStr, 'Assay.Name': assayName, 'Assay.Version': assayVersion, 'Comments': comments, 'RunId': runId}
        lysisReads = [lysisTime, lysisTemp]
        detectReads ={'Time': detectTime, 'CartTemp': cartTemp, 'AdcTemp': adcTemp, 'Signals': pdReads, 'Well': Wells, 'Target': ChLabel, 'ChResult': ChResult, 'ChVolDiff': ChVolDiff}
        
        return [testInfo, lysisReads, detectReads]

class dbItemListWidget(QListWidget):
    onClickSignal = pyqtSignal(list)
    def __init__(self, parent=None):
        super(dbItemListWidget, self).__init__(parent)
        self.resize(500, 500)
        self.setStyleSheet('font-size: 16px;')
        
        self.dfDict = {}
        self.fullList = []
        self.seletedRunId = []
        self.bitRuns = None

        self.itemDoubleClicked.connect(self.onClicked)
        self.itemSelectionChanged.connect(self.onSelectionChanged)
        
    def onSelectionChanged(self):
        selectedItems = self.selectedItems()
        if len(selectedItems) == 0:
            return
        self.seletedRunId = []
        for item in selectedItems:
            self.seletedRunId.append(item.text().split('-')[0])
        print(self.seletedRunId)
    
    def loadRuns(self):
        # host = '169.254.21.151'
        # username = 'torizon'
        # password = 'torizon1'
        # ssh = SshClient(host, 22, username, password)
        # dbPath = 'cxldnabit_web:/sqlite/cxl.db'
        # stdin, stdout, stderr = ssh.client.exec_command(f'docker cp {dbPath} /var/rootdirs/home/torizon')
        # exit_status = stdout.channel.recv_exit_status() 
        
        # # config sftp
        # dirSource = '/var/rootdirs/home/torizon/cxl.db'
        # target = os.path.join(os.getcwd(), 'cxl.db')
        # sftp = MySFTPClient.from_transport(ssh.client.get_transport())
        # if exit_status == 0:
        #     sftp.get(dirSource, target)
        # else:
        #     print('Failed to copy db file')
        # ssh.client.exec_command('rm /var/rootdirs/home/torizon//cxl.db')
        
        # db_name = "cxl.db"
        
        # offline test
        db_name = "cxl_N002.db"
        
        table_name = ['Runs', 'TargetResults', 'Readings', 'LysisReadings','AssayDefinitions']

        engine = sqlalchemy.create_engine("sqlite:///%s" % db_name, execution_options={"sqlite_raw_colnames": True})
        for table in table_name:
            df = pd.read_sql_table(table, engine)
            self.dfDict[table] = df
        self.bitRuns = BIT_Runs(self.dfDict)

    def getListItems(self):
        
        for runId, sampleId, overallResult, assayName in self.bitRuns.runsInfo[['Id', 'SampleId', 'Result', 'Name']].values:
            resultText = self.resultInterpret(overallResult)
            if assayName == 'Dev_Mode':
                self.fullList.append(f'{runId}-{sampleId}-{assayName}')
                self.addItem(f'{runId}-{sampleId}-{assayName}')
            else:
                self.fullList.append(f'{runId}-{sampleId}-{resultText}')
                self.addItem(f'{runId}-{sampleId}-{resultText}')
    
    def updateListItem(self, key, value):
        query = {}
        query[key] = value
        # print(query)
        curItems = self.getItemsList()
        self.clear()
        if value == 'All':
            for item in self.fullList:
                self.addItem(item)
            return
        if key == 'Result':
            value = self.resultInterpret(value)

        for runId, sampleId, overallResult, assayName in self.bitRuns.runsInfo.loc[self.bitRuns.runsInfo[key] == value][['Id', 'SampleId', 'Result', 'Name']].values:
            
            resultText = self.resultInterpret(overallResult)
            if assayName == 'Dev_Mode':
                itemText = f'{runId}-{sampleId}-{assayName}'
                if itemText in curItems:
                    self.addItem(itemText)
            else:
                itemText = f'{runId}-{sampleId}-{resultText}'
                if itemText in curItems:
                    self.addItem(itemText)
    
    def getItemsList(self):
        items = set()
        for i in range(self.count()):
            items.add(self.item(i).text())
        return items
    
    def resultInterpret(self, result):
        if result == POS:
            return 'POS'
        elif result == NEG:
            return 'NEG'
        elif result == UNDEFINED:
            return 'UNDEFINED'
        elif result == INVALID:
            return 'INVALID'
        
        if result == 'POS':
            return POS
        elif result == 'NEG':
            return NEG
        elif result == 'UNDEFINED':
            return UNDEFINED
        elif result == 'INVALID':
            return INVALID

    def getItemsForCombobox(self):
        self.keyList = ['Result', 'Name', 'CreatedDate']
        self.cbboxItemsSets = []
        for key in self.keyList:
            if key == 'Result':
                itemList = []
                for rlt in self.bitRuns.runsInfo[key].unique():
                    rltText = self.resultInterpret(rlt)
                    itemList.append(rltText)
                    
                self.cbboxItemsSets.append(itemList)
                continue
            self.cbboxItemsSets.append(self.bitRuns.runsInfo[key].unique())
    
    def onClicked(self, lstItem):
        idStr = lstItem.text().split('-')[0]
        selectedTest = self.bitRuns.getRun(idStr)
        self.onClickSignal.emit(selectedTest)
        self.clearSelection()
        self.seletedRunId = []

# copy table from one db to another
def copyTablesBetweenDb(sourceDb, targetDb, tableNames):
    opDb = sqlite3.connect(':memory:')
    opDb.execute(f'ATTACH DATABASE "{sourceDb}" AS source')
    opDb.execute(f'ATTACH DATABASE "{targetDb}" AS target')
    
    for table in tableNames:
        if table == 'Runs':
            opDb.execute(f'INSERT OR IGNORE INTO target.{table}(Id, CreatedDate, UpdatedDate, AssayDefinitionId, Barcode, SampleId, Result, Comments) SELECT * FROM source.{table}')
        else:
            opDb.execute(f'INSERT OR IGNORE INTO target.{table} SELECT * FROM source.{table}')
    opDb.commit()

    opDb.close()
    
def deleteRuns(sqliteDb, runIdList):
    conn = sqlite3.connect(sqliteDb)
    c = conn.cursor()
    for runId in runIdList:
        c.execute(f'DELETE FROM Runs WHERE Id = {runId}')
        c.execute(f'DELETE FROM TargetResults WHERE RunId = {runId}')
        c.execute(f'DELETE FROM Readings WHERE RunId = {runId}')
        c.execute(f'DELETE FROM LysisReadings WHERE RunId = {runId}')
    c.execute('DELETE FROM SmoothedReadings')
        
    conn.commit()
    conn.close()

def addCol2Table(sqliteDb, tableName, colName, colType):
    conn = sqlite3.connect(sqliteDb)
    c = conn.cursor()
    c.execute(f'ALTER TABLE {tableName} ADD COLUMN {colName} {colType}')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    getDb()
    # dfDict = sql2Dataframes()
    
    # app = QApplication(sys.argv)

    # demo = dbItemListWidget()
    # # demo.loadItemFromDF(dfDict)
    
    # demo.show()

    # sys.exit(app.exec_())
    
    # copyTablesBetweenDb('cxl_s.db', 'cxl.db', ['Runs', 'TargetResults', 'Readings', 'LysisReadings','AssayDefinitions', 'SmoothedReadings'])
    # startRunId, endRunId = 150, 161
    # deleteRuns('cxl.db', range(startRunId, endRunId + 1))
    
    
    