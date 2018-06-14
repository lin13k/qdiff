from qdiff.exceptions import NotImplementedException
from qdiff.abstracts import AbstractDatabaseAccessUnit
from tableschema import Table
from django.conf import settings


class DataReader:

    def getRow(self):
        raise NotImplementedException("readRow method is not implemented")

    def getRowsList(self):
        raise NotImplementedException("getIterator method is not implemented")

    def close(self):
        raise NotImplementedException("close method is not implemented")

    def getColumns(self):
        raise NotImplementedException("getColumns method is not implemented")

    def getSchema(self):
        raise NotImplementedException("getSchema method is not implemented")


class DatabaseReader(AbstractDatabaseAccessUnit, DataReader):

    def __init__(self, config_dict, query_sql):
        # TODO valid the config_dict
        super(DatabaseReader, self).__init__(config_dict)
        self.query_sql = query_sql

    def getColumns(self):
        columns = []
        try:
            if not hasattr(self, 'cursor'):
                self.cursor = self.getCursor()
                self.cursor.execute(self.query_sql)
        except Exception as e:
            self.cursor.close()
            raise e
        for columnDesc in self.cursor.description:
            columns.append(columnDesc[0])
        return columns

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

    def getSchema(self):
        try:
            tmpCursor = self.getCursor()
            tmpCursor.execute(self.query_sql)
            i = settings.SCHEMA_INFER_LIMIT
            tmpList = []
            row = tmpCursor.fetchone()
            while i > 0 and row is not None:
                tmpList.append(row)
                row = tmpCursor.fetchone()
                i -= 1
            tmpList = [self.getColumns()] + tmpList
            t = Table(tmpList)
            t.infer()
            t.schema.descriptor[
                'missingValues'] = settings.SCHEMA_DATABASE_MISSING_VALUES
            return t.infer(confidence=settings.SCHEMA_INFER_CONFIDENCE)
            # schema = Schema({'missingValues': ['', 'None', 'null']})
            # return schema.infer(
            #     tmpList, headers=self.getColumns(),
            #     confidence=settings.SCHEMA_INFER_CONFIDENCE)

        except Exception as e:
            tmpCursor.close()
            raise e

    def close(self):
        try:
            self.cursor.close()
        except Exception as e:
            pass

    def __repr__(self):
        return (settings.SOURCE_TYPE_DATABASE_PREFIX +
                self.config_dict['NAME'] + '@' +
                self.config_dict['HOST'])


class CsvReader(DataReader):

    def __init__(self, filePath):
        self._filePath = filePath
        self._table = Table(filePath)

    def close(self):
        pass

    def getColumns(self):
        if not self._table.headers:
            self._table.infer(
                settings.SCHEMA_INFER_LIMIT)
        return self._table.headers

    def requery(self):
        self._table = Table(self._filePath)

    def getRow(self):
        i = self._table.iter(cast=True)
        return next(i)

    def getRowsList(self):
        self._table.infer()
        self._table.schema.descriptor[
            'missingValues'] = settings.SCHEMA_CSV_MISSING_VALUES
        self._table.schema.commit()
        i = self._table.iter(cast=True)

        return list(map(tuple, i))

    def getSchema(self):
        t = Table(self._filePath)
        t.infer()
        t.schema.descriptor[
            'missingValues'] = settings.SCHEMA_CSV_MISSING_VALUES
        t.schema.commit()
        return t.infer(
            settings.SCHEMA_INFER_LIMIT,
            confidence=settings.SCHEMA_INFER_CONFIDENCE)

    def __repr__(self):
        return (settings.SOURCE_TYPE_CSV_PREFIX +
                self._filePath)
