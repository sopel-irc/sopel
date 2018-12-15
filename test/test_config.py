# coding=utf-8
from __future__ import unicode_literals, division, print_function, absolute_import

import os
import tempfile
import unittest
from sopel import config
from sopel.config import types


class FakeConfigSection(types.StaticSection):
    valattr = types.ValidatedAttribute('valattr')
    listattr = types.ListAttribute('listattr')
    choiceattr = types.ChoiceAttribute('choiceattr', ['spam', 'egg', 'bacon'])
    af_fileattr = types.FilenameAttribute('af_fileattr', relative=False, directory=False)
    ad_fileattr = types.FilenameAttribute('ad_fileattr', relative=False, directory=True)
    rf_fileattr = types.FilenameAttribute('rf_fileattr', relative=True, directory=False)
    rd_fileattr = types.FilenameAttribute('rd_fileattr', relative=True, directory=True)


class ConfigFunctionalTest(unittest.TestCase):
    @classmethod
    def read_config(cls):
        configo = config.Config(cls.filename)
        configo.define_section('fake', FakeConfigSection)
        return configo

    @classmethod
    def setUpClass(cls):
        cls.filename = tempfile.mkstemp()[1]
        with open(cls.filename, 'w') as fileo:
            fileo.write(
                "[core]\n"
                "owner=dgw\n"
                "homedir={}".format(os.path.expanduser('~/.sopel'))
            )

        cls.config = cls.read_config()

        cls.testfile = open(os.path.expanduser('~/.sopel/test.tmp'), 'w+').name
        cls.testdir = os.path.expanduser('~/.sopel/test.d/')
        os.mkdir(cls.testdir)

    @classmethod
    def tearDownClass(cls):
        os.remove(cls.filename)
        os.remove(cls.testfile)
        os.rmdir(cls.testdir)

    def test_validated_string_when_none(self):
        self.config.fake.valattr = None
        self.assertEqual(self.config.fake.valattr, None)

    def test_listattribute_when_empty(self):
        self.config.fake.listattr = []
        self.assertEqual(self.config.fake.listattr, [])

    def test_listattribute_with_one_value(self):
        self.config.fake.listattr = ['foo']
        self.assertEqual(self.config.fake.listattr, ['foo'])

    def test_listattribute_with_multiple_values(self):
        self.config.fake.listattr = ['egg', 'sausage', 'bacon']
        self.assertEqual(self.config.fake.listattr, ['egg', 'sausage', 'bacon'])

    def test_listattribute_with_value_containing_comma(self):
        self.config.fake.listattr = ['spam, egg, sausage', 'bacon']
        self.assertEqual(self.config.fake.listattr, ['spam', 'egg', 'sausage', 'bacon'])

    def test_choiceattribute_when_none(self):
        self.config.fake.choiceattr = None
        self.assertEqual(self.config.fake.choiceattr, None)

    def test_choiceattribute_when_not_in_set(self):
        with self.assertRaises(ValueError):
            self.config.fake.choiceattr = 'sausage'

    def test_choiceattribute_when_valid(self):
        self.config.fake.choiceattr = 'bacon'
        self.assertEqual(self.config.fake.choiceattr, 'bacon')

    def test_fileattribute_valid_absolute_file_path(self):
        self.config.fake.af_fileattr = self.testfile
        self.assertEqual(self.config.fake.af_fileattr, self.testfile)

    def test_fileattribute_valid_absolute_dir_path(self):
        testdir = self.testdir
        self.config.fake.ad_fileattr = testdir
        self.assertEqual(self.config.fake.ad_fileattr, testdir)

    def test_fileattribute_given_relative_when_absolute(self):
        with self.assertRaises(ValueError):
            self.config.fake.af_fileattr = '../testconfig.tmp'

    def test_fileattribute_given_absolute_when_relative(self):
        self.config.fake.rf_fileattr = self.testfile
        self.assertEqual(self.config.fake.rf_fileattr, self.testfile)

    def test_fileattribute_given_dir_when_file(self):
        with self.assertRaises(ValueError):
            self.config.fake.af_fileattr = self.testdir

    def test_fileattribute_given_file_when_dir(self):
        with self.assertRaises(ValueError):
            self.config.fake.ad_fileattr = self.testfile
