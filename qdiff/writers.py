from csv import writer


class DBWriter:
    def __init__(self, connection, tableName):
        self.connection = connection
        # TODO purify the tableName
        self.tableName = tableName

    def getColumns(self):
        columns = []
        with self.connection.cursor() as cursor:
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
        with self.connection.cursor() as cursor:
            cursor.executemany(self.insert_statement, rows)


CSVWriter = writer
