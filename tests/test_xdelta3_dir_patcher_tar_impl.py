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

from filecmp import dircmp, cmpfiles
from mock import Mock
from shutil import rmtree, copyfile
from tempfile import mkdtemp
from os import cpu_count, path, chmod, makedirs, walk, remove
from stat import S_IRWXU, S_IRWXG, S_IROTH, S_IXOTH

# Dashes are standard for exec scipts but not allowed for modules in Python. We
# use the script standard since we will be running that file as a script most
# often.
patcher = imp.load_source("xdelta3-dir-patcher", "xdelta3-dir-patcher")

class TestXDelta3DirPatcherTarImpl(unittest.TestCase):
    TEST_FILE_PREFIX = path.join('tests', 'test_files', 'tar_impl')

    def setUp(self):
        self.temp_dir = mkdtemp(prefix="%s_" % self.__class__.__name__)
        chmod(self.temp_dir, S_IRWXU | S_IRWXG | S_IROTH | S_IXOTH)
        self.temp_dir2 = mkdtemp(prefix="%s_" % self.__class__.__name__)
        chmod(self.temp_dir2, S_IRWXU | S_IRWXG | S_IROTH | S_IXOTH)

        self.test_class = patcher.XDelta3TarImpl

    def tearDown(self):
        rmtree(self.temp_dir)
        rmtree(self.temp_dir2)

    # Helpers
    def compare_trees(self, first, second):
        diff = dircmp(first, second)

        self.assertEquals([], diff.diff_files)
        self.assertEquals([], diff.common_funny)
        self.assertEquals([], diff.left_only)
        self.assertEquals([], diff.right_only)

        files_to_compare = []
        for root, directories, files in walk(first):
            for cmp_file in files:
                files_to_compare.append(path.join(root, cmp_file))

        # Strip target file prefixes
        files_to_compare = [name[len(first)+1:] for name in files_to_compare]

        _, mismatch, error = cmpfiles(first, second, files_to_compare)

        self.assertEquals([], mismatch)
        self.assertEquals([], error)

    def get_content(self, filename):
        content = None
        with open(filename, 'rb') as file_handle:
            content = file_handle.read()

        return content

    def get_archive(self, name):
        return path.join(self.TEST_FILE_PREFIX, '%s.tgz' % name)

    def expected_new_version1_members(self):
        return ['binary_file',
                'long_lorem.txt',
                'new folder/',
                'new folder/new file1.txt',
                'short_lorem.txt',
                'updated folder/',
                'updated folder/updated file.txt',
                'updated folder/.hidden_updated_file.txt']

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
            actual_members = test_object.list_files()

            self.assertEquals(len(self.expected_new_version1_members()),
                              len(actual_members))

            for member in self.expected_new_version1_members():
                self.assertIn(member, actual_members)

    def test_list_members_is_cached(self):
        orig_archive = self.get_archive('new_version1')
        archive = path.join(self.temp_dir, 'new_version1.tgz')
        copyfile(orig_archive, archive)

        with self.test_class(archive) as test_object:
            # Force a load of the index
            initial_members = test_object.list_files()
            self.assertEquals(len(self.expected_new_version1_members()),
                              len(initial_members))

            # Remove the archive
            remove(archive)

            # Test invocation
            actual_members = test_object.list_files()

            self.assertEquals(len(self.expected_new_version1_members()),
                              len(actual_members))
            for member in self.expected_new_version1_members():
                self.assertIn(member, actual_members)

    def test_can_extract_members_correctly(self):
        archive = self.get_archive('new_version1')

        with self.test_class(archive) as test_object:
            test_object.expand('new folder/new file1.txt', self.temp_dir)
            actual_content = self.get_content(path.join(self.temp_dir,
                                                        'new folder',
                                                        'new file1.txt'))

            self.assertEquals(b'new file content\n', actual_content)

    def test_can_be_manually_opened_and_closed(self):
        archive = self.get_archive('new_version1')

        test_object = self.test_class(archive)

        test_object.expand('new folder/new file1.txt', self.temp_dir)
        actual_content = self.get_content(path.join(self.temp_dir,
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

        self.compare_trees(source_dir, self.temp_dir2)

    # XXX: tarfile implementation is not thread-safe after trying it out
    @unittest.skipIf(cpu_count() <= 3, \
                     'This test requires 3 or more virtal CPUs')
    def test_extract_is_thread_locked(self):
        archive = self.get_archive('new_version1')

        self.executor_runner = patcher.ExecutorRunner()

        with self.test_class(archive) as test_object:
            # Force a load of the index
            initial_members = test_object.list_files()

            for member in initial_members:
                for i in range(0, 10):
                    self.executor_runner.add_task(test_object.expand,
                                                  (member, self.temp_dir))

            self.executor_runner.join_all()
