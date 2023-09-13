import gspread
from PyQt5 import QtWidgets

class GSheetObj:
    def  __init__(self, sheetId = '1l6Knw0hzO0a4EiWoqg36BOtKD0eDbt3EQiR9VzNeDSw', curWorkSheet = 'AutoTest log'):
        credentials = {"installed":{"client_id":"REDACTED_CLIENT_ID","project_id":"thylacine-automatic-test-log","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"REDACTED_CLIENT_SECRET","redirect_uris":["http://localhost"]}}
        authorized_user = {"refresh_token": "REDACTED_REFRESH_TOKEN", "token_uri": "https://oauth2.googleapis.com/token", "client_id": "REDACTED_CLIENT_ID", "client_secret": "REDACTED_CLIENT_SECRET", "scopes": ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"], "expiry": "2023-09-12T23:58:43.232085Z"}
        gc, authorized_user = gspread.oauth_from_dict(credentials, authorized_user)
        
        self.wks = gc.open_by_key(sheetId).worksheet(curWorkSheet)
        letterList = [chr(i) for i in range(65, 91)]
        self.headersDict = {header:letterList[i] for i, header in enumerate(self.wks.row_values(1)[:26])}
        self.endRowIndex = len(self.wks.col_values(2))
    
    def logRun(self, run, userinputs):
        testInfo, lysisReads, detectReads = run
        cartrideId = testInfo['Barcode']
        sampleId = testInfo['SampleId']
        print(userinputs)
        date, loc, deviceId = userinputs.split(';')
        
        volDiffs = detectReads['ChVolDiff']
        chRlts = detectReads['ChResult']
        resultCell = []
        for rlt in chRlts:
            if rlt == 1:
                resultCell.append('+')
            else:
                resultCell.append('-')
        resultCell = ','.join(resultCell)
        
        cellValues = {'Date': date, 'Location': loc, 'Device ID': deviceId, 'Cartridge ID': cartrideId, 
                      'Sample ID on Device': sampleId, 'Result': resultCell, 'PD1 mvs ▲': volDiffs[0], 
                      'PD2 mvs ▲': volDiffs[1], 'PD3 mvs ▲': volDiffs[2], 'PD4 mvs ▲': volDiffs[3], 'PD5 mvs ▲': volDiffs[4]}
        
        for key, value in cellValues.items():
            self.wks.update(f'{self.headersDict[key]}{self.endRowIndex+1}', value, value_input_option='USER_ENTERED')
        self.endRowIndex += 1
    
    def autoFill(self):
        startRowIdx = len(self.wks.col_values(1)) + 1
        endRowIdx = self.endRowIndex
        sameDateTestCnt = 1
        curDate = self.wks.acell(f'{self.headersDict["Date"]}{startRowIdx}').value
        for i in range(endRowIdx - startRowIdx + 1):
            date = self.wks.acell(f'{self.headersDict["Date"]}{startRowIdx + i}').value
            deviceId = self.wks.acell(f'{self.headersDict["Device ID"]}{startRowIdx + i}').value
            if date == curDate:
                self.wks.update(f'{self.headersDict["Test #"]}{startRowIdx + i}', sameDateTestCnt, value_input_option='USER_ENTERED')
                sameDateTestCnt += 1
            else:
                curDate = date
                sameDateTestCnt = 1
                self.wks.update(f'{self.headersDict["Test #"]}{startRowIdx + i}', sameDateTestCnt, value_input_option='USER_ENTERED')
            
            testId = f'{date}_{deviceId}_{sameDateTestCnt}'
            self.wks.update(f'{self.headersDict["Test ID#"]}{startRowIdx + i}', testId, value_input_option='USER_ENTERED')
        
        

if __name__ == '__main__':


    sh = GSheetObj()
    # cell = sh.wks.find("NCSPI0069")
    # sh.wks.update_cell(cell.row + 1, cell.col + 1, 'PASS')
    # print(sh.headersDict)