import imp
import unittest
import tarfile

from filecmp import dircmp, cmpfiles
from mock import Mock
from shutil import rmtree, copyfile
from tempfile import mkdtemp
from os import path, chmod, makedirs, walk
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

    def test_can_list_members_correctly(self):
        tar_archive = path.join(self.TEST_FILE_PREFIX, 'new_version1.tgz')
        test_class = patcher.XDelta3TarImpl(tar_archive)

        expected_members = ['binary_file',
                            'long_lorem.txt',
                            'new folder/new file1.txt',
                            'short_lorem.txt',
                            'updated folder/updated file.txt',
                            'updated folder/.hidden_updated_file.txt']

        actual_members = test_class.list_files()

        self.assertEquals(6, len(actual_members))
        for member in expected_members:
            self.assertIn(member, actual_members)

    def test_can_extract_members_correctly(self):
        tar_archive = path.join(self.TEST_FILE_PREFIX, 'new_version1.tgz')
        test_class = patcher.XDelta3TarImpl(tar_archive)

        test_class.expand('new folder/new file1.txt', self.temp_dir)

        actual_content = self.get_content(path.join(self.temp_dir,
                                                    'new folder',
                                                    'new file1.txt'))

        self.assertEquals(b'new file content\n', actual_content)

    def test_impl_can_create_correctly(self):
        tar_archive = path.join(self.temp_dir, 'test_archive.tgz')

        source_dir = path.join(self.TEST_FILE_PREFIX, 'new_version1')

        test_class = patcher.XDelta3TarImpl(tar_archive)

        # Add the files to archive
        test_class.create(source_dir)

        # Ensure that the archive was closed if it was opened
        # so that we can reopen and test that the file was added
        del test_class

        with tarfile.open(tar_archive) as archive_object:
            archive_object.extractall(self.temp_dir2)

        self.compare_trees(source_dir, self.temp_dir2)
