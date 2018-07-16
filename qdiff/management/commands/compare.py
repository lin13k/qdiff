from django.core.management.base import BaseCommand, CommandError
from qdiff.models import Task
from qdiff.managers import TaskManager
from django.conf import settings
from qdiff.utils.validations import Validator
from qdiff.utils.model import getMaskedSourceFromString
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

    def handle(self, *args, **options):

        # validate the input options
        v = Validator(
            options.get('summary', None),
            options.get('rds1', None),
            options.get('rds2', None),
            options.get('sql1', None),
            options.get('sql2', None),
            options.get('ignore1', None),
            options.get('ignore2', None),
            options.get('wds1', None),
            options.get('wds2', None))
        errs = v.validate()
        if len(errs) > 0:
            raise CommandError(', '.join(errs))

        # init the model
        model = Task.objects.create(
            summary=options.get('summary', None),
            left_source=getMaskedSourceFromString(options.get('rds1', None)),
            left_query_sql=options.get('sql1', None),
            left_ignore_fields=options.get('ignore1', None),
            right_source=getMaskedSourceFromString(options.get('rds2', None)),
            right_query_sql=options.get('sql2', None),
            right_ignore_fields=options.get('ignore2', None),
        )
        # call manager and compare
        try:
            manager = TaskManager(
                model,
                options.get('rds1', None),
                options.get('rds2', None),
                options.get('wds1', None),
                options.get('wds2', None))
            manager.compare()
        except Exception as e:
            model.result = Task.STATUS_OF_TASK_ERROR
            model.result_detail = str(e)

        # display basic information
        self.stdout.write('Comparing between\n -: %s\n +: %s' % (
            manager.reader1, manager.reader2))
        self.stdout.write(model.result)
        if model.result_detail:
            self.stdout.write(model.result_detail.replace(
                settings.RESULT_SPLITTING_TOKEN, '\n'))
