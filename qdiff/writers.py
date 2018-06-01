from csv import writer
from qdiff.abstracts import AbstractDatabaseAccessUnit


class DatabaseWriter(AbstractDatabaseAccessUnit):
    def __init__(self, config_dict, tableName):
        super(DatabaseWriter, self).__init__(config_dict)

        # TODO purify the tableName
        self.tableName = tableName
        # TODO should get header from outside

    def getColumns(self):
        columns = []
        with self.getCursor() as cursor:
            cursor.execute("SELECT * FROM %s LIMIT 1;" % (self.tableName))
            for columnDesc in cursor.description:
                columns.append(columnDesc[0])
        return columns

    def getInsertStatement(self):
        if not hasattr(self, 'columns'):
            self.columns = self.getColumns()
        statement = 'INSERT INTO %s ' % self.tableName
        statement += '(' + (', '.join(self.columns)) + ') '
        statement += 'VALUES (' + ', '.join(['%s' for i in self.columns]) + ')'
        return statement

    def writeAll(self, rows):
        if not hasattr(self, 'insert_statement'):
            self.insert_statement = self.getInsertStatement()
        with self.getCursor() as cursor:
            cursor.executemany(self.insert_statement, rows)


class CsvWriter:

    def __init__(self, *args, **kwargs):
        headers = kwargs.pop('headers', None)
        self.writer = writer(*args, **kwargs)
        if headers:
            self.headers = headers

    def writeAll(self, rows):
        if hasattr(self, 'headers'):
            self.writer.writerow(self.headers)
        for row in rows:
            self.writer.writerow(row)


class ConsoleWriter:

    def writeAll(self, rows):
        self.rows = rows
        for row in rows:
            print(row)
