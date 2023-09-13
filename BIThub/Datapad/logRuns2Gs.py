from helpers.sqlOps import BIT_Runs

import os, sys, sqlite3
import paramiko, sqlalchemy
import pandas as pd

if __name__ == '__main__':
    
    # offline test
    db_name = "cxl_N002.db"
    
    table_name = ['Runs', 'TargetResults', 'Readings', 'LysisReadings','AssayDefinitions']

    engine = sqlalchemy.create_engine("sqlite:///%s" % db_name, execution_options={"sqlite_raw_colnames": True})
    
    dfDict = {}
    for table in table_name:
        df = pd.read_sql_table(table, engine)
        dfDict[table] = df
    bitRuns = BIT_Runs(dfDict)
    
    runIdLt = [9, 10]
    bitRuns.logRuns2GSheet(runIdLt)