import pymongo, json, gridfs, os, sys

from json import JSONDecoder
from functools import partial

from pprint import pprint
from pymongo import InsertOne, DeleteMany, ReplaceOne, UpdateOne

class remoteDbObj():
    def __init__(self, address):
        self.client = pymongo.MongoClient(address) 
        # client = pymongo.MongoClient('mongodb+srv://cifeng:cxldnabit@cluster0.kathwyh.mongodb.net/test')

    def connectDB(self, dbName, collectionName):

        self.db = self.client[dbName]
        self.collection = self.db[collectionName]
    
    def queryDB(self, collection, query):
        return collection.find_one(query)

    def putImage(self, collection, filepath):
        fs = gridfs.GridFS(collection)

        with open(filepath, 'rb') as f:
            contents = f.read()
        file = os.path.splitext(os.path.basename(filepath))[0]
        fs.put(contents, filename=file)

    def json_parse(fileobj, decoder=JSONDecoder(), buffersize=2048):
        buffer = ''
        for chunk in iter(partial(fileobj.read, buffersize), ''):
            buffer += chunk
            while buffer:
                try:
                    result, index = decoder.raw_decode(buffer)
                    yield result
                    buffer = buffer[index:].lstrip()
                except ValueError:
                    # Not enough data to decode, read more
                    break

    def write2Remote(self, jsonFile, dbName, collectionName):
        db = self.client[dbName]
        collection = db[collectionName]
        requesting = []

        with open(jsonFile, 'r') as f:
            myDicts = json.load(f)
            # print(type(myDicts))
            for myDict in myDicts:
                requesting.append(InsertOne(myDict))

        result = collection.bulk_write(requesting)   


# run exe with python script
# cwd = os.path.dirname(dbFilePath)
# cmd_str = f'.\\rET.exe {dbFilePath}'
# subprocess.run(cmd_str, shell=True)

if __name__ == '__main__':
    address = 'mongodb://localhost:27017'
    mongoDbRemote = remoteDbObj(address)