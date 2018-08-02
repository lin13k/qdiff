from django.test import TestCase
from qdiff.utils.validations import Validator
import sys


class ValidatorTestCase(TestCase):
    def setUp(self):
        pass

    def testValidateLogic1(self):
        v = Validator('s', '', '')
        errs = v.validate()
        self.assertEqual(
            errs,
            ['read data source 1 is required',
             'read data source 2 is required'])

    def testValidateLogic2(self):
        v = Validator('s', 'database:', 'csv:')
        errs = v.validate()
        if sys.version_info > (3,):
            self.assertEqual(
                errs,
                ['read data source 1: is not a valid json string, '
                 'Expecting value: line 1 column 1 (char 0)',
                 'The parameter sql1 is missing. '
                 'Querying SQL is necassary for database source.'])
        else:
            self.assertEqual(
                errs,
                ['read data source 1: is not a valid json string, '
                 'No JSON object could be decoded',
                 'The parameter sql1 is missing. '
                 'Querying SQL is necassary for database source.'])

    def testValidateLogic2_1(self):
        v = Validator('s', 'csv:', 'database:')
        errs = v.validate()
        if sys.version_info > (3,):
            self.assertEqual(
                errs,
                ['read data source 2: is not a valid json string, '
                 'Expecting value: line 1 column 1 (char 0)',
                 'The parameter sql2 is missing. '
                 'Querying SQL is necassary for database source.'])
        else:
            self.assertEqual(
                errs,
                ['read data source 2: is not a valid json string, '
                 'No JSON object could be decoded',
                 'The parameter sql2 is missing. '
                 'Querying SQL is necassary for database source.'])

    def testValidateLogic3(self):
        v = Validator(
            's', 'database:{"DUMMY":"VALUE"}', 'csv:thisiscsv.csv',
            sql1='dummy sql')
        errs = v.validate()
        self.assertEqual(
            errs,
            ['read data source 1: must have field ENGINE',
             'read data source 1: must have field NAME'])

    def testValidateLogic3_1(self):
        v = Validator(
            's', 'csv:thisiscsv.csv', 'database:{"DUMMY":"VALUE"}',
            sql2='dummy sql')
        errs = v.validate()
        self.assertEqual(
            errs,
            ['read data source 2: must have field ENGINE',
             'read data source 2: must have field NAME'])
