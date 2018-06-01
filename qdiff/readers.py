from qdiff.Exceptions import NotImplementedException
from django.db import connections


class DataReader:

    def readRow(self):
        raise NotImplementedException("readRow method is not implemented")

    def getIterator(self):
        raise NotImplementedException("getIterator method is not implemented")

    def close(self):
        raise NotImplementedException("close method is not implemented")


class DatabaseReader(DataReader):

    def __init__(self, configDict, query_sql):
        # TODO valid the configDict
        self.configDict = configDict
        self.label = 'db_' + str(hash(tuple(sorted(configDict.items()))))
        self.query_sql = query_sql

    def register(self):
        connections._databases[self.label] = self.configDict
        del connections.databases

    def readRow(self):
        if self.label not in connections:
            self.register()
        if not hasattr(self, 'iterator'):
            self.iterator = self.getIterator()
        return next(self.iterator)

    def getIterator(self):
        if self.label not in connections:
            self.register()
        self.cursor = connections[self.label].cursor()
        try:
            self.cursor.execute(self.query_sql)
        except Exception as e:
            self.cursor.close()
            raise e
        return self.cursor.fetchall()

    def close(self):
        try:
            self.cursor.close()
        except Exception as e:
            pass
