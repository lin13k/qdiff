from django.test import TestCase
from argparse import ArgumentParser


class ArgParserTestCase(TestCase):
    def setUp(self):
        pass

    def testParsing1(self):

        parser = ArgumentParser()
        parser.add_argument(
            '--rds1', help='Data source for read 1',
            required=True
        )
        parser.add_argument(
            '--rds2', help='Data source for read 2',
            required=True
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
            help='Ignored fields in data source 1', nargs='*',
        )
        parser.add_argument(
            '--ignore2',
            help='Ignored fields in data source 2', nargs='*',
        )

        r = parser.parse_args(
            '--rds1 rds1 --rds2 rds2 --wds1 wds1 --wds2 wds2'.split())
        self.assertEqual(r.rds1, 'rds1')
        self.assertEqual(r.rds2, 'rds2')
        self.assertEqual(r.wds1, 'wds1')
        self.assertEqual(r.wds2, 'wds2')
