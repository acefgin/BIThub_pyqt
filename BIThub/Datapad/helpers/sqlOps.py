import os, sys
import paramiko, sqlalchemy
import pandas as pd
     
from PyQt5.QtWidgets import QApplication, QListWidget
from PyQt5.QtCore import pyqtSignal

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
    
    def getIdList(self, dfDict):
        runsTb = dfDict['Runs']
        assayTb = dfDict['AssayDefinitions']
        self.runsInfo = runsTb.join(assayTb[['Id', 'Name', 'Version']].set_index('Id'), on='AssayDefinitionId', lsuffix='_r', rsuffix='_a')
        
    def getRunBySampleId(self, sampleId):
        run = self.runQuery(sampleId)
        return run
    
    def runQuery(self, sampleId):
        runsTb, targetTb, readsTb = self.dfDict['Runs'], self.dfDict['TargetResults'], self.dfDict['Readings']
        lysisTb, assayTb = self.dfDict['LysisReadings'], self.dfDict['AssayDefinitions']
        
        runId = runsTb.loc[runsTb['SampleId'] == sampleId]['Id'].values[0]
        barcode = runsTb.loc[runsTb['SampleId'] == sampleId]['Barcode'].values[0]
        createdDate = runsTb.loc[runsTb['SampleId'] == sampleId]['CreatedDate'].values[0]
        comments = runsTb.loc[runsTb['SampleId'] == sampleId]['Comments'].values[0]
        assayId = runsTb.loc[runsTb['SampleId'] == sampleId]['AssayDefinitionId'].values[0]
        OverallResult = runsTb.loc[runsTb['SampleId'] == sampleId]['Result'].values[0]
        
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
        # self.getDd2Df()
        # self.loadItemFromDF()
        # self.getItemsForCombobox()

        self.itemDoubleClicked.connect(self.onClicked)
    
    def getDd2Df(self):
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
        
        db_name = "cxl.db"
        table_name = ['Runs', 'TargetResults', 'Readings', 'LysisReadings','AssayDefinitions']

        engine = sqlalchemy.create_engine("sqlite:///%s" % db_name, execution_options={"sqlite_raw_colnames": True})
        for table in table_name:
            df = pd.read_sql_table(table, engine)
            self.dfDict[table] = df

    def loadItemFromDF(self):
        self.bitRuns = BIT_Runs(self.dfDict)
        
        for runId, sampleId in self.bitRuns.runsInfo[['Id', 'SampleId']].values:
            self.fullList.append(f'{runId}-{sampleId}')
            self.addItem(f'{runId}-{sampleId}')
    
    def updateListItem(self, key, value):
        query = {}
        query[key] = value
        print(query)
        curItems = []
        if value == 'All':
            curItems = self.fullList
        else:
            for runId, sampleId in self.bitRuns.runsInfo.loc[self.bitRuns.runsInfo[key] == value][['runId', 'sampleId']].values:
                curItems.append(f'{runId}-{sampleId}')
        self.clear()

        for item in curItems:
            self.addItem(item["TestId"])

    def getItemsForCombobox(self):
        self.keyList = ['Result', 'Name', 'CreatedDate']
        self.cbboxItemsSets = []
        for key in self.keyList:
            if key == 'Result':
                itemList = []
                for rlt in self.bitRuns.runsInfo[key].unique():
                    if rlt == POS:
                        itemList.append('POS')
                    elif rlt == NEG:
                        itemList.append('NEG')
                    elif rlt == UNDEFINED:
                        itemList.append('UNDEFINED')
                    elif rlt == INVALID:
                        itemList.append('INVALID')
                self.cbboxItemsSets.append(itemList)
            self.cbboxItemsSets.append(self.bitRuns.runsInfo[key].unique())
    
    def onClicked(self, lstItem):
        idStr = lstItem.text().split('-')[-1]
        selectedTest = self.bitRuns.getRunBySampleId(idStr)
        self.onClickSignal.emit(selectedTest)
        
    
if __name__ == '__main__':
    # getDb()
    # dfDict = sql2Dataframes()
    
    app = QApplication(sys.argv)

    demo = dbItemListWidget()
    # demo.loadItemFromDF(dfDict)
    
    demo.show()

    sys.exit(app.exec_())