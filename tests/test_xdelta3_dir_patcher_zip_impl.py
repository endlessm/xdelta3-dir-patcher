#    xdelta3-dir-patcher
#    Copyright (C) 2014-2015 Endless Mobile
#
#   This library is free software; you can redistribute it and/or
#   modify it under the terms of the GNU Lesser General Public
#   License as published by the Free Software Foundation; either
#   version 2.1 of the License, or (at your option) any later version.
#
#   This library is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   Lesser General Public License for more details.
#
#   You should have received a copy of the GNU Lesser General Public
#   License along with this library; if not, write to the Free Software
#   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
#   USA

import imp
import unittest
import zipfile

from mock import Mock
from shutil import rmtree, copyfile
from tempfile import mkdtemp
from os import path, chmod, makedirs, walk, remove
from stat import S_IRWXU, S_IRWXG, S_IROTH, S_IXOTH

from .test_helpers import TestHelpers

class TestXDelta3DirPatcherZipImpl(unittest.TestCase):
    # Dashes are standard for exec scipts but not allowed for modules in Python. We
    # use the script standard since we will be running that file as a script most
    # often.
    patcher = imp.load_source("xdelta3-dir-patcher", "xdelta3-dir-patcher")

    TEST_FILE_PREFIX = path.join('tests', 'test_files', 'zip_impl')

    def setUp(self):
        self.temp_dir = mkdtemp(prefix="%s_" % self.__class__.__name__)
        chmod(self.temp_dir, S_IRWXU | S_IRWXG | S_IROTH | S_IXOTH)
        self.temp_dir2 = mkdtemp(prefix="%s_" % self.__class__.__name__)
        chmod(self.temp_dir2, S_IRWXU | S_IRWXG | S_IROTH | S_IXOTH)

        self.test_class = self.patcher.XDelta3ZipImpl

    def tearDown(self):
        rmtree(self.temp_dir)
        rmtree(self.temp_dir2)

    # Helpers
    def get_archive(self, name):
        return path.join(self.TEST_FILE_PREFIX, '%s.zip' % name)

    def test_can_open_works(self):
        prefix = path.join('tests', 'test_files', 'archive_instance')
        file_pattern = path.join(prefix, 'old_version1%s')

        self.assertFalse(self.test_class.can_open(file_pattern % ''))
        self.assertFalse(self.test_class.can_open(file_pattern % '.tgz'))
        self.assertTrue(self.test_class.can_open(file_pattern % '.zip'))
        self.assertFalse(self.test_class.can_open('abcd'))

    def test_can_list_members_correctly(self):
        archive = self.get_archive('new_version1')
        with self.test_class(archive) as test_object:
            TestHelpers.verify_new_version1_members(self,
                                                    self.patcher,
                                                    test_object.list_items())

    def test_list_members_is_cached(self):
        orig_archive = self.get_archive('new_version1')
        archive = path.join(self.temp_dir, 'new_version1.zip')
        copyfile(orig_archive, archive)

        with self.test_class(archive) as test_object:
            # Force a load of the index
            TestHelpers.verify_new_version1_members(self,
                                                    self.patcher,
                                                    test_object.list_items())

            # Remove the archive
            remove(archive)

            # Test invocation
            TestHelpers.verify_new_version1_members(self,
                                                    self.patcher,
                                                    test_object.list_items())

    def test_list_members_is_cached_on_load(self):
        orig_archive = self.get_archive('new_version1')
        archive = path.join(self.temp_dir, 'new_version1.zip')
        copyfile(orig_archive, archive)

        with self.test_class(archive) as test_object:
            remove(archive)

            # Force a load of the index
            TestHelpers.verify_new_version1_members(self,
                                                    self.patcher,
                                                    test_object.list_items())

    def test_can_extract_members_correctly(self):
        archive = self.get_archive('new_version1')

        with self.test_class(archive) as test_object:
            test_object.expand('new folder/new file1.txt', self.temp_dir)
            actual_content = TestHelpers.get_content(path.join(self.temp_dir,
                                                               'new folder',
                                                               'new file1.txt'))

            self.assertEquals(b'new file content\n', actual_content)

    def test_can_be_manually_opened_and_closed(self):
        archive = self.get_archive('new_version1')

        test_object = self.test_class(archive)

        test_object.expand('new folder/new file1.txt', self.temp_dir)
        actual_content = TestHelpers.get_content(path.join(self.temp_dir,
                                                           'new folder',
                                                           'new file1.txt'))

        self.assertEquals(b'new file content\n', actual_content)

        test_object.close()

    def test_manually_closed_archive_is_not_usable(self):
        archive = self.get_archive('new_version1')

        test_object = self.test_class(archive)
        test_object.close()

        try:
            test_object.expand('new folder/new file1.txt', self.temp_dir)

            raise Exception('Unexpected exception thrown')
        except RuntimeError as e:
            pass

    def test_can_extract_members_correctly_in_already_created_dir(self):
        archive = self.get_archive('new_version1')

        with self.test_class(archive) as test_object:
            test_object.expand('new folder/new file1.txt', self.temp_dir)

            try:
                test_object.expand('new folder/new file1.txt', self.temp_dir)
            except:
                self.fail("Should not have thrown an error on expanding same item")

    def test_can_create_correctly(self):
        archive = path.join(self.temp_dir, 'test_archive.zip')

        source_dir = path.join(self.TEST_FILE_PREFIX, 'new_version1')

        with self.test_class(archive, True) as test_object:
            # Add the files to archive
            test_object.create(source_dir)

        with zipfile.ZipFile(archive) as archive_object:
            archive_object.extractall(self.temp_dir2)

        TestHelpers.compare_trees(self, source_dir, self.temp_dir2)
