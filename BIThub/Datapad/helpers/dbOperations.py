import pymongo
import json
import gridfs
import os
import sys      
from PyQt5.QtWidgets import QApplication, QWidget, QListWidget, QListWidgetItem
from PyQt5.QtCore import pyqtSignal

def connectDB(dbName, collectionName):
    # client = pymongo.MongoClient('mongodb+srv://cifeng:cxldnabit@cluster0.kathwyh.mongodb.net/test')
    client = pymongo.MongoClient('mongodb://localhost:27017') 
    db = client[dbName]
    collection = db[collectionName]
    return client, collection

def putImage(collection, filepath):
    fs = gridfs.GridFS(collection)

    with open(filepath, 'rb') as f:
        contents = f.read()
    file = os.path.splitext(os.path.basename(filepath))[0]
    fs.put(contents, filename=file)

def queryDB(collection, query):
    return collection.find_one(query)

class dbItemListWidget(QListWidget):
    onClickSignal = pyqtSignal(dict)
    def __init__(self, parent=None):
        super(dbItemListWidget, self).__init__(parent)
        self.resize(500, 500)
        self.setStyleSheet('font-size: 16px;')
        self.connectDB()
        self.loadItemFromDB()
        self.getItemsForCombobox()

        self.itemDoubleClicked.connect(self.onClicked)
    
    def __del__(self):
        self.client.close()
    
    def connectDB(self, dbName = 'testDB', collectionName = 'test'):
        # self.client = pymongo.MongoClient('mongodb+srv://cifeng:cxldnabit@cluster0.kathwyh.mongodb.net/test')
        self.client = pymongo.MongoClient('mongodb://localhost:27017') 
        
        db = self.client[dbName]
        self.testLogCol = db[collectionName]

    def loadItemFromDB(self):
        self.totalTestItems = self.testLogCol.find()
        
        for test in self.totalTestItems:
            self.addItem(test["TestId"])
    
    def updateListItem(self, key, value):
        query = {}
        query[key] = value
        print(query)
        if value == 'All':
            curItems = self.testLogCol.find()
        else:
            curItems = self.testLogCol.find(query)
        self.clear()

        for item in curItems:
            self.addItem(item["TestId"])

    def getItemsForCombobox(self):
        self.keyList = ["Input", "Location", "AsExpected"]
        self.cbboxItemsSets = []
        for key in self.keyList:
            self.cbboxItemsSets.append(self.testLogCol.distinct(key))
    
    def onClicked(self, lstItem):
        TestId = lstItem.text()
        selectedTest = self.testLogCol.find_one({"TestId": TestId})
        
        self.onClickSignal.emit(selectedTest)
        
    
if __name__ == '__main__':
    client, testLogs = connectDB('thy_testsDB', 's2r_testlog')
    
    # print(testLog["Well1"])

    app = QApplication(sys.argv)

    demo = dbItemListWidget()
    demo.loadItemFromDB(testLogs)
    
    demo.show()

    sys.exit(app.exec_())