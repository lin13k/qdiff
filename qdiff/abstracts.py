from django.db import connections


class AbstractDatabaseAccessUnit(object):
    '''
    This abstract class is used by database reader and writer
    '''

    def __init__(self, config_dict):
        self.config_dict = config_dict
        if 'id' in config_dict:
            self.label = config_dict['id']
        else:
            self.label = 'db_' + str(hash(str(sorted(config_dict.items()))))

    def register(self):
        connections._databases[self.label] = self.config_dict
        del connections.databases

    def getCursor(self):
        try:
            if self.label not in connections:
                self.register()
            c = connections[self.label].cursor()
        except Exception as e:
            self.destroy()
            raise e
        return c

    def destroy(self):
        connections._databases.pop(self.label)
        del connections.databases
