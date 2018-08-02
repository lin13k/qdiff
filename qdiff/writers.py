from csv import writer
from qdiff.abstracts import AbstractDatabaseAccessUnit


class DatabaseWriter(AbstractDatabaseAccessUnit):
    '''
    Database writer, which can write date into the given table name
    '''

    def __init__(self, configDict, tableName):
        '''
        Positional arguments:
        configDict --  the database configuration dictionary
            ref https://docs.djangoproject.com/en/2.0/ref/settings/#databases
        tableName -- the table name the writer instance targets
        '''
        super(DatabaseWriter, self).__init__(configDict)

        self.tableName = tableName

    def getColumns(self):
        '''return the column names as a list'''
        columns = []
        with self.getCursor() as cursor:
            cursor.execute("SELECT * FROM %s LIMIT 1;" % (self.tableName))
            for columnDesc in cursor.description:
                columns.append(columnDesc[0])
        return columns

    def getInsertStatement(self):
        '''return insert statement as string for the given table'''
        if not hasattr(self, 'columns'):
            self.columns = self.getColumns()
        statement = 'INSERT INTO %s ' % self.tableName
        statement += '(' + (', '.join(self.columns)) + ') '
        statement += 'VALUES (' + ', '.join(['%s' for i in self.columns]) + ')'
        return statement

    def writeAll(self, rows):
        '''
        write rows into database

        Positional arguements
        rows -- two dimentional list
        '''
        if not hasattr(self, 'insert_statement'):
            self.insert_statement = self.getInsertStatement()
        with self.getCursor() as cursor:
            cursor.executemany(self.insert_statement, rows)


class CsvWriter(object):
    '''
    CSV writer wrapper
    '''

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


class ConsoleWriter(object):
    '''
    Console writer wrapper, mainly for testing
    '''

    def writeAll(self, rows):
        self.rows = rows
        for row in rows:
            print(row)
