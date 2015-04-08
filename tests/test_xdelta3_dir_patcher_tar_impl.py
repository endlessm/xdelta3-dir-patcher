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
import tarfile

from collections import OrderedDict
from mock import Mock
from shutil import rmtree, copyfile
from tempfile import mkdtemp
from multiprocessing import cpu_count
from os import listdir, lstat, path, chmod, makedirs, walk, remove
from stat import S_IRWXU, S_IRWXG, S_IROTH, S_IXOTH, S_IMODE

from .test_helpers import TestHelpers

class TestXDelta3DirPatcherTarImpl(unittest.TestCase):
    # Dashes are standard for exec scipts but not allowed for modules in Python. We
    # use the script standard since we will be running that file as a script most
    # often.
    patcher = imp.load_source("xdelta3-dir-patcher", "xdelta3-dir-patcher")

    ALLOW_PERMISSION_TESTS = True

    TEST_FILE_PREFIX = path.join('tests', 'test_files', 'tar_impl')
    GENERIC_TEST_FILE_PREFIX = path.join('tests', 'test_files', 'dir_patcher')

    def setUp(self):
        self.temp_dir = mkdtemp(prefix="%s_" % self.__class__.__name__)
        chmod(self.temp_dir, S_IRWXU | S_IRWXG | S_IROTH | S_IXOTH)
        self.temp_dir2 = mkdtemp(prefix="%s_" % self.__class__.__name__)
        chmod(self.temp_dir2, S_IRWXU | S_IRWXG | S_IROTH | S_IXOTH)

        self.test_class = self.patcher.XDelta3TarImpl

    def tearDown(self):
        rmtree(self.temp_dir)
        rmtree(self.temp_dir2)

    def get_archive(self, name):
        return path.join(self.TEST_FILE_PREFIX, '%s.tgz' % name)

    def test_can_open_works(self):
        prefix = path.join('tests', 'test_files', 'archive_instance')
        file_pattern = path.join(prefix, 'old_version1%s')

        self.assertFalse(self.test_class.can_open(file_pattern % ''))
        self.assertTrue(self.test_class.can_open(file_pattern % '.tgz'))
        self.assertFalse(self.test_class.can_open(file_pattern % '.zip'))
        self.assertFalse(self.test_class.can_open('abcd'))

    def test_can_list_members_correctly(self):
        archive = self.get_archive('new_version1')
        with self.test_class(archive) as test_object:
            TestHelpers.verify_new_version1_members(self, self.patcher,
                                                    test_object.list_items())

    def test_members_listed_in_order_as_in_archive_and_miss_hierachy(self):
        archive = self.get_archive('missing_hierarchy')

        with self.test_class(archive) as test_object:
            self.assertTrue(isinstance(test_object.list_items(), OrderedDict))

            # Regular keys are not modifiable and also mutable
            # so we do some magic here to ensure that's not the case
            listing = list(test_object.list_items().copy().keys())
            listing.remove(None)

        with tarfile.open(archive) as archive_object:
            expected_listing = archive_object.getnames()

        expected_created_hierarchy = ['foo',
                                      'foo/bar',
                                      'foo/bar/baz',
                                      'foo/bar/baz/foo',
                                      'foo/bar/baz/foo/bar',
                                      'foo/bar/baz/foo/bar/baz']

        self.assertEqual(listing[0:len(expected_listing)], expected_listing)
        self.assertEqual(sorted(listing[len(expected_listing):]),
                         expected_created_hierarchy)

    def test_members_listed_in_order_as_in_archive(self):
        archive = self.get_archive('new_version1')

        with self.test_class(archive) as test_object:
            self.assertTrue(isinstance(test_object.list_items(), OrderedDict))

            # Regular keys are not modifiable and also mutable
            # so we do some magic here to ensure that's not the case
            listing = list(test_object.list_items().copy().keys())
            listing.remove(None)

        with tarfile.open(archive) as archive_object:
            expected_listing = archive_object.getnames()

        self.assertEqual(listing, expected_listing)

    def test_list_members_is_cached(self):
        orig_archive = self.get_archive('new_version1')
        archive = path.join(self.temp_dir, 'new_version1.tgz')
        copyfile(orig_archive, archive)

        with self.test_class(archive) as test_object:
            # Force a load of the index
            TestHelpers.verify_new_version1_members(self, self.patcher,
                                                    test_object.list_items())

            # Remove the archive
            remove(archive)

            # Test invocation
            TestHelpers.verify_new_version1_members(self, self.patcher,
                                                    test_object.list_items())

    def test_list_members_is_cached_on_load(self):
        orig_archive = self.get_archive('new_version1')
        archive = path.join(self.temp_dir, 'new_version1.tgz')
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

    def test_can_extract_members_correctly_that_lack_hierarchy(self):
        archive = self.get_archive('missing_hierarchy')

        with self.test_class(archive) as test_object:
            int_path = 'foo/bar/baz/foo/bar/baz/test.txt'
            test_object.expand(int_path, self.temp_dir)
            actual_content = TestHelpers.get_content(path.join(self.temp_dir,
                                                               *int_path.split(path.sep)))

            self.assertEquals(b'new file content\n', actual_content)

    def test_can_extract_inserted_dir_hierarchy(self):
        archive = self.get_archive('missing_hierarchy')

        with self.test_class(archive) as test_object:
            int_path = 'foo/bar/baz/foo/bar'
            full_path = 'foo/bar/baz/foo/bar/baz/test.txt'
            test_object.expand(int_path, self.temp_dir)
            actual_content = TestHelpers.get_content(path.join(self.temp_dir,
                                                               *full_path.split(path.sep)))

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
        except OSError as e:
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
        archive = path.join(self.temp_dir, 'test_archive.tgz')

        source_dir = path.join(self.TEST_FILE_PREFIX, 'new_version1')

        with self.test_class(archive, True) as test_object:
            # Add the files to archive
            test_object.create(source_dir)

        with tarfile.open(archive) as archive_object:
            archive_object.extractall(self.temp_dir2)

        TestHelpers.compare_trees(self, source_dir, self.temp_dir2)

    def test_symbolic_links_are_handled_correctly(self):
        archive = path.join(self.temp_dir, 'test_archive.tgz')

        source_dir = path.join(self.TEST_FILE_PREFIX, 'symlink')

        with self.test_class(archive, True) as test_object:
            # Add the files to archive
            test_object.create(source_dir)

        with self.test_class(archive) as test_object:
            test_object.expand(None, self.temp_dir2)

        TestHelpers.compare_trees(self, source_dir, self.temp_dir2)

    # XXX: tarfile implementation is not thread-safe after trying it out
    @unittest.skipIf(cpu_count() <= 3, \
                     'This test requires 3 or more virtal CPUs')
    def test_extract_is_thread_locked(self):
        archive = self.get_archive('new_version1')

        self.executor_runner = self.patcher.ExecutorRunner()

        with self.test_class(archive) as test_object:
            # Force a load of the index
            initial_members = test_object.list_items()
            initial_members.pop(None)

            for member in initial_members:
                for i in range(0, 10):
                    self.executor_runner.add_task(test_object.expand,
                                                  (member, self.temp_dir))

            self.executor_runner.join_all()

    # ---------------------------- PERMISSIONS TESTS -----------------------------
    # XXX: Since permissions aren't preserved in git nor are they creatable
    #      in tests, it's not feasible to create robust run-anywhere tests
    #      that can truly be run on any platform which is why these are
    #      conditional based on a very special test environment and a folder
    #      which has content matching tests/test_files/permissions_new.tgz
    #      and permissions that match.

    @unittest.skipUnless(ALLOW_PERMISSION_TESTS, 'Test platform unsupported')
    def test_gid_and_uid_of_added_files_are_correct(self):
        archive = path.join(self.temp_dir, 'permissions_new.tgz')

        expected_permissions = {
                'file_group_change.txt': ( None, 4321 ),
                'file_owner_change.txt': ( 1234, None ),
                'folder_group_change': ( None, 4321 ),
                'folder_owner_change': ( 1234, None ),
                'folder_group_change/inner_file_group_change.txt': ( None, 4321 ),
                'folder_group_change/inner_file_owner_change.txt': ( 1234, None ),
                'folder_group_change/inner_folder_group_change': ( None, 4321 ),
                'folder_group_change/inner_folder_owner_change': ( 1234, None ),
                }

        source_dir = path.join(self.GENERIC_TEST_FILE_PREFIX, 'permissions_new')

        with self.test_class(archive, True) as test_object:
            test_object.create(source_dir)

        checked_items = 0
        with tarfile.open(archive) as archive_object:
            for member in archive_object.getmembers():
                if member.name in expected_permissions:
                    # print('U: %d (%s)' % (member.uid, member.uname))
                    # print('G: %d (%s)' % (member.gid, member.gname))

                    checked_items += 1

                    expected_uid, expected_gid = expected_permissions[member.name]
                    if expected_uid:
                        self.assertEquals(member.uid, expected_uid)
                    if expected_gid:
                        self.assertEquals(member.gid, expected_gid)
                else:
                    print(member.name)

        self.assertEquals(checked_items, len(expected_permissions))

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

        def validate_permissions(member):
            permissions = expected_permissions[member.name]
            print(path.join(source_dir, member.name))

            real_permissions = S_IMODE(lstat(path.join(source_dir,
                                                       member.name)).st_mode)
            self.assertEquals(oct(real_permissions), oct(permissions))

        checked_items = 0
        with tarfile.open(archive) as archive_object:
            for member in archive_object.getmembers():
                if member.name in expected_permissions:
                    validate_permissions(member)
                    checked_items += 1

        self.assertEquals(checked_items, len(expected_permissions))
