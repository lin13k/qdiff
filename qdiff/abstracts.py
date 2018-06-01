from django.db import connections


class AbstractDatabaseAccessUnit:
    def __init__(self, config_dict):
        self.config_dict = config_dict
        if 'id' in config_dict:
            self.label = config_dict['id']
        else:
            self.label = 'db_' + str(hash(tuple(sorted(config_dict.items()))))

    def register(self):
        connections._databases[self.label] = self.config_dict
        del connections.databases

    def getCursor(self):
        if self.label not in connections:
            self.register()
        c = connections[self.label].cursor()
        return c
