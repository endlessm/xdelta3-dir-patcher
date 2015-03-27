#!/usr/bin/env python3
#
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

from mock import Mock
from shutil import rmtree, copyfile, copytree
from tempfile import mkdtemp
from os import path, chmod, makedirs, walk, lstat
from stat import S_IRWXU, S_IRWXG, S_IROTH, S_IXOTH, S_IMODE

from .test_helpers import TestHelpers

class TestXDelta3DirPatcherFsImpl(unittest.TestCase):
    # Dashes are standard for exec scipts but not allowed for modules in Python. We
    # use the script standard since we will be running that file as a script most
    # often.
    patcher = imp.load_source("xdelta3-dir-patcher", "xdelta3-dir-patcher")

    ALLOW_PERMISSION_TESTS = True

    TEST_FILE_PREFIX = path.join('tests', 'test_files', 'fs_impl')
    GENERIC_TEST_FILE_PREFIX = path.join('tests', 'test_files', 'dir_patcher')

    def setUp(self):
        self.temp_dir = mkdtemp(prefix="%s_" % self.__class__.__name__)
        chmod(self.temp_dir, S_IRWXU | S_IRWXG | S_IROTH | S_IXOTH)
        self.temp_dir2 = mkdtemp(prefix="%s_" % self.__class__.__name__)
        chmod(self.temp_dir2, S_IRWXU | S_IRWXG | S_IROTH | S_IXOTH)

        self.test_class = self.patcher.XDelta3FsImpl

    def tearDown(self):
        rmtree(self.temp_dir)
        rmtree(self.temp_dir2)

    def get_archive(self, name):
        return path.join(self.TEST_FILE_PREFIX, '%s' % name)

    def test_can_open_works(self):
        prefix = path.join('tests', 'test_files', 'archive_instance')
        file_pattern = path.join(prefix, 'old_version1%s')

        self.assertTrue(self.test_class.can_open(file_pattern % ''))
        self.assertFalse(self.test_class.can_open(file_pattern % '.tgz'))
        self.assertFalse(self.test_class.can_open(file_pattern % '.zip'))
        self.assertFalse(self.test_class.can_open('abcd'))

    def test_can_list_members_correctly(self):
        archive = self.get_archive('new_version1')
        with self.test_class(archive) as test_object:
            actual_members = test_object.list_items()

            TestHelpers.verify_new_version1_members(self,
                                                    self.patcher,
                                                    test_object.list_items())

    def test_list_members_is_cached(self):
        archive = self.get_archive('new_version1')
        orig_archive = path.join(self.TEST_FILE_PREFIX, 'new_version1')
        archive = path.join(self.temp_dir, 'new_version1')
        copytree(orig_archive, archive)

        with self.test_class(archive) as test_object:
            # Force a load of the index
            TestHelpers.verify_new_version1_members(self,
                                                    self.patcher,
                                                    test_object.list_items())

            # Remove the archive
            rmtree(archive)

            # Test invocation
            TestHelpers.verify_new_version1_members(self,
                                                    self.patcher,
                                                    test_object.list_items())

    def test_list_members_is_cached_on_load(self):
        archive = self.get_archive('new_version1')
        orig_archive = path.join(self.TEST_FILE_PREFIX, 'new_version1')
        archive = path.join(self.temp_dir, 'new_version1')
        copytree(orig_archive, archive)

        with self.test_class(archive) as test_object:
            rmtree(archive)

            # Force a load of the index
            TestHelpers.verify_new_version1_members(self,
                                                    self.patcher,
                                                    test_object.list_items())

    def test_can_extract_files_correctly(self):
        archive = self.get_archive('new_version1')
        test_object = self.test_class(archive)

        with self.test_class(archive) as test_object:
            test_object.expand('new folder/new file1.txt', self.temp_dir)
            actual_content = TestHelpers.get_content(path.join(self.temp_dir,
                                                        'new folder',
                                                        'new file1.txt'))

            self.assertEquals(b'new file content\n', actual_content)

    def test_can_extract_folders_correctly(self):
        archive = self.get_archive('new_version1')
        test_object = self.test_class(archive)

        folder_name = 'new folder'

        test_object.expand(folder_name, self.temp_dir)

        self.assertTrue(path.isdir(path.join(self.temp_dir, folder_name)))

    def test_can_be_manually_opened_and_closed(self):
        archive = self.get_archive('new_version1')

        test_object = self.test_class(archive)

        test_object.expand('new folder/new file1.txt', self.temp_dir)
        actual_content = TestHelpers.get_content(path.join(self.temp_dir,
                                                           'new folder',
                                                           'new file1.txt'))

        self.assertEquals(b'new file content\n', actual_content)

        test_object.close()

    def test_can_extract_members_correctly_in_already_created_dir(self):
        archive = self.get_archive('new_version1')
        with self.test_class(archive) as test_object:
            test_object.expand('new folder/new file1.txt', self.temp_dir)

            try:
                test_object.expand('new folder/new file1.txt', self.temp_dir)
            except:
                self.fail("Should not have thrown an error on expanding same item")

    def test_can_create_correctly(self):
        archive = path.join(self.temp_dir , 'test_archive')

        source_dir = path.join(self.TEST_FILE_PREFIX, 'new_version1')

        with self.test_class(archive) as test_object:
            # Add the files to archive
            test_object.create(source_dir)

        # Since it's a FS implamantation, we compare it directly to our source
        # files
        TestHelpers.compare_trees(self, source_dir, archive)

    def test_symbolic_links_are_handled_correctly(self):
        archive = path.join(self.temp_dir, 'test_archive')

        source_dir = path.join(self.TEST_FILE_PREFIX, 'symlink')

        with self.test_class(archive, True) as test_object:
            # Add the files to archive
            test_object.create(source_dir)

        with self.test_class(archive) as test_object:
            for item in test_object.list_items():
                test_object.expand(item, self.temp_dir2)

        TestHelpers.compare_trees(self, source_dir, self.temp_dir2)

    # ---------------------------- PERMISSIONS TESTS -----------------------------
    # XXX: Since permissions aren't preserved in git nor are they settable
    #      in tests, it's not feasible to create robust run-anywhere tests
    #      that can truly be run on any platform which is why these are
    #      conditional based on a very special test environment and a folder
    #      which has content matching tests/test_files/permissions_new.tgz
    #      and permissions as indicated in the file.

    @unittest.skipUnless(ALLOW_PERMISSION_TESTS, 'Test platform unsupported')
    def test_gid_and_uid_of_added_files_are_correct(self):
        # No way to test this without root permissions
        pass

    @unittest.skipUnless(ALLOW_PERMISSION_TESTS, 'Test platform unsupported')
    def test_permissions_of_added_files_are_correct(self):
        archive = path.join(self.temp_dir, 'permissions_new')

        expected_permissions = {
                'file_group_change.txt': 0o777,
                'file_permission_change.txt': 0o1625,
                'folder_permission_change': 0o1725,
                'folder_permission_change/inner_file_permission_change.txt': 0o1625,
                }

        source_dir = path.join(self.GENERIC_TEST_FILE_PREFIX, 'permissions_new')

        with self.test_class(archive, True) as test_object:
            test_object.create(source_dir)

        checked_items = 0

        def validate_permissions(obj_path, checked_items):
            rel_path = path.relpath(obj_path, archive)

            if not rel_path in expected_permissions:
                return checked_items

            print(rel_path)
            permissions = oct(expected_permissions[rel_path])
            real_permissions = oct(S_IMODE(lstat(obj_path).st_mode))
            self.assertEquals(real_permissions, permissions)

            return checked_items + 1

        for root, directories, files in walk(archive):
            for filename in files:
                file_path = path.join(root, filename)
                checked_items = validate_permissions(file_path, checked_items)

            for directory in directories:
                dir_path = path.join(root, directory)
                checked_items = validate_permissions(dir_path, checked_items)

        self.assertEquals(checked_items, len(expected_permissions))
