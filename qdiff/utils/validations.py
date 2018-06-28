from django.conf import settings
import re
import json


class Validator:
    """docstring for Validator"""

    def __init__(self, summary, rds1, rds2,
                 sql1=None, sql2=None, ignore1=None, ignore2=None,
                 wds1=None, wds2=None):
        super(Validator, self).__init__()
        self.summary = summary
        self.rds1 = rds1
        self.rds2 = rds2
        self.sql1 = sql1
        self.sql2 = sql2
        self.ignore1 = ignore1
        self.ignore2 = ignore2
        self.wds1 = wds1
        self.wds2 = wds2
        self.report = []

    def validate(self):
        if self.summary is None or len(self.summary) == 0:
            self.report.append('Summary is required')
        if self.rds1 is None or len(self.rds1) == 0:
            self.report.append('read data source 1 is required')
        if self.rds2 is None or len(self.rds2) == 0:
            self.report.append('read data source 2 is required')

        # for each datasource field
        #   header check
        #   if db:
        #       format check
        #       field check
        datasources = {}
        if self.rds1:
            datasources['read data source 1'] = self.rds1
        if self.rds2:
            datasources['read data source 2'] = self.rds2

        if self.wds1:
            datasources['write data source 1'] = self.wds1
        if self.wds2:
            datasources['write data source 2'] = self.wds2
        for name, source in datasources.items():
            self.headerCheck(name, source)
            if (source[:len(settings.SOURCE_TYPE_DATABASE_PREFIX)].lower().
                    startswith(settings.SOURCE_TYPE_DATABASE_PREFIX.lower())):
                obj = self.jsonFormatCheck(name, source)
                if obj:
                    self.fieldCheck(name, obj, settings.SOURCE_REQUIRED_FIELDS)

                # check SQL existence
                if name == 'read data source 1' and self.sql1 is None:
                    self.report.append(
                        'The parameter sql1 is missing. '
                        'Querying SQL is necassary for database source.')
                if name == 'read data source 2' and self.sql2 is None:
                    self.report.append(
                        'The parameter sql2 is missing. '
                        'Querying SQL is necassary for database source.')

        # TODO validate SQL
        # TODO validate ignored fields
        return self.report

    def headerCheck(self, name, string):
        validPrefixes = settings.SOURCE_TYPE_PREFIXES
        if not re.match('^(' + '|'.join(validPrefixes) + ')', string):
            self.report.append(
                '%s:%s is leading with invalid header' % (name, string))

    def jsonFormatCheck(self, name, string):
        validPrefixes = settings.SOURCE_TYPE_PREFIXES
        r = re.match('(' + '|'.join(validPrefixes) + ')', string)
        obj = None
        try:
            obj = json.loads(string[len(r.group(0)):])
        except Exception as e:
            self.report.append(
                '%s:%s is not a valid json string, %s' %
                (name, string[len(r.group(0)):], e))
        return obj

    def fieldCheck(self, name, obj, fieldList):
        for requriedField in fieldList:
            if requriedField not in obj:
                self.report.append('%s: must have field %s' %
                                   (name, requriedField))
