from django.core.management.base import BaseCommand, CommandError
from qdiff.models import Task
from qdiff.managers import TaskManager
from django.conf import settings
import json
import re
# from qdiff.models import Task


class Command(BaseCommand):

    def add_arguments(selp, parser):
        parser.add_argument(
            '--summary',
            help='Summary for this comparison task',
            required=True,
        )
        parser.add_argument(
            '--rds1', help='Data source for read 1',
            required=True
        )
        parser.add_argument(
            '--sql1', help='Query sql for data source 1,'
            ' only works when data source 1 is database',
            # required=True
        )
        parser.add_argument(
            '--rds2', help='Data source for read 2',
            required=True
        )
        parser.add_argument(
            '--sql2', help='Query sql for data source 2,'
            ' only works when data source 2 is database',
            # required=True
        )
        parser.add_argument(
            '--wds1',
            help='Data source for write 1, any unmatched '
            'record from data source 1 will be written '
            'into this source',
        )
        parser.add_argument(
            '--wds2',
            help='Data source for write 2, any unmatched '
            'record from data source 2 will be written '
            'into this source',
        )
        parser.add_argument(
            '--ignore1',
            help='Ignored fields in data source 1, split with comma',
            # nargs='*',
        )
        parser.add_argument(
            '--ignore2',
            help='Ignored fields in data source 2, split with comma',
            # nargs='*',
        )

    def headerCheck(self, name, string):
        validPrefixes = settings.SOURCE_TYPE_PREFIXES
        if not re.match('^(' + '|'.join(validPrefixes) + ')', string):
            raise CommandError(
                '%s:%s is leading with invalid header' % (name, string))

    def jsonFormatCheck(self, name, string):
        validPrefixes = settings.SOURCE_TYPE_PREFIXES
        r = re.match('(' + '|'.join(validPrefixes) + ')', string)
        obj = None
        try:
            obj = json.loads(string[len(r.group(0)):])
        except Exception as e:
            raise CommandError(
                '%s:%s is not a valid json string, %s' %
                (name, string[len(r.group(0)):], e))
        return obj

    def fieldCheck(self, name, obj, fieldList):
        for requriedField in fieldList:
            if requriedField not in obj:
                raise CommandError('%s: must have field %s' %
                                   (name, requriedField))

    def handle(self, *args, **options):

        # validate the input options
        # header check and json format check
        # fields check, id, engine, etc
        rds1 = options['rds1']
        self.headerCheck('rds1', rds1)
        if rds1.startswith(settings.SOURCE_TYPE_DATABASE_PREFIX):
            obj = self.jsonFormatCheck('rds1', rds1)
            self.fieldCheck('rds1', obj, settings.SOURCE_REQUIRED_FIELDS)
        rds2 = options['rds2']
        self.headerCheck('rds2', rds2)
        if rds2.startswith(settings.SOURCE_TYPE_DATABASE_PREFIX):
            obj = self.jsonFormatCheck('rds2', rds2)
            self.fieldCheck('rds2', obj, settings.SOURCE_REQUIRED_FIELDS)
        wsd1 = options.get('wsd1', None)
        if wsd1:
            self.headerCheck('wsd1', wsd1)
            if wsd1.startswith(settings.SOURCE_TYPE_DATABASE_PREFIX):
                obj = self.jsonFormatCheck('wsd1', wsd1)
                self.fieldCheck('wsd1', obj, settings.SOURCE_REQUIRED_FIELDS)
        wsd2 = options.get('wsd2', None)
        if wsd2:
            self.headerCheck('wsd2', wsd2)
            if wsd2.startswith(settings.SOURCE_TYPE_DATABASE_PREFIX):
                obj = self.jsonFormatCheck('wsd2', wsd2)
                self.fieldCheck('wsd2', obj, settings.SOURCE_REQUIRED_FIELDS)

        # TODO validate the sqls
        # TODO validate the ignored fields
        # TODO validate the summary

        # init the model
        model = Task.objects.create(
            summary=options['summary'],
            left_source=rds1,
            left_query_sql=options['sql1'],
            left_ignore_fields=options['ignore1'],
            right_source=rds2,
            right_query_sql=options['sql2'],
            right_ignore_fields=options['ignore2'],
            # owner=getpass.getuser(),
        )
        # call manager and compare
        manager = TaskManager(model)
        manager.compare()

        # display basic information
        self.stdout.write('Comparing between\n -: %s\n +: %s' % (
            manager.reader1, manager.reader2))
        self.stdout.write(model.result)
        if model.result_detail:
            self.stdout.write(model.result_detail.replace('<@#$>', '\n'))
