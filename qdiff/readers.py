from qdiff.exceptions import NotImplementedException
from django.db import connections
from qdiff.abstracts import AbstractDatabaseAccessUnit


class DataReader:

    def getRow(self):
        raise NotImplementedException("readRow method is not implemented")

    def getRowsList(self):
        raise NotImplementedException("getIterator method is not implemented")

    def close(self):
        raise NotImplementedException("close method is not implemented")


class DatabaseReader(AbstractDatabaseAccessUnit, DataReader):

    def __init__(self, config_dict, query_sql):
        # TODO valid the config_dict
        super(DatabaseReader, self).__init__(config_dict)
        self.query_sql = query_sql

    def getRow(self):
        try:
            if not hasattr(self, 'cursor'):
                self.cursor = self.getCursor()
                self.cursor.execute(self.query_sql)
        except Exception as e:
            self.cursor.close()
            raise e
        return self.cursor.fetchone()

    def getRowsList(self):
        try:
            if not hasattr(self, 'cursor'):
                self.cursor = self.getCursor()
                self.cursor.execute(self.query_sql)
        except Exception as e:
            self.cursor.close()
            raise e
        return self.cursor.fetchall()

    def requery(self):
        self.close()
        self.cursor = self.getCursor()
        self.cursor.execute(self.query_sql)

    def close(self):
        try:
            self.cursor.close()
        except Exception as e:
            pass
