from qdiff.Exceptions import NotImplementedException
from django.db import connections


class DataReader:

    def getRow(self):
        raise NotImplementedException("readRow method is not implemented")

    def getRowsList(self):
        raise NotImplementedException("getIterator method is not implemented")

    def close(self):
        raise NotImplementedException("close method is not implemented")


class DatabaseReader(DataReader):

    def __init__(self, config_dict, query_sql):
        # TODO valid the config_dict
        self.config_dict = config_dict
        if 'id' in config_dict:
            self.label = config_dict['id']
        else:
            self.label = 'db_' + str(hash(tuple(sorted(config_dict.items()))))
        self.query_sql = query_sql

    def getCursor(self):
        c = connections[self.label].cursor()
        c.execute(self.query_sql)
        return c

    def register(self):
        connections._databases[self.label] = self.config_dict
        del connections.databases

    def getRow(self):
        if self.label not in connections:
            self.register()
        try:
            if not hasattr(self, 'cursor'):
                self.cursor = self.getCursor()
        except Exception as e:
            self.cursor.close()
            raise e
        return self.cursor.fetchone()

    def getRowsList(self):
        if self.label not in connections:
            self.register()
        try:
            if not hasattr(self, 'cursor'):
                self.cursor = self.getCursor()
        except Exception as e:
            self.cursor.close()
            raise e
        return self.cursor.fetchall()

    def close(self):
        try:
            self.cursor.close()
        except Exception as e:
            pass
