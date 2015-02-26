import imp
import unittest
import tarfile

from filecmp import dircmp, cmp
from mock import Mock
from shutil import rmtree
from tempfile import mkdtemp
from os import path, chmod
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

    def get_content(self, filename):
        content = None
        with open(filename, 'rb') as file_handle:
            content = file_handle.read()

        return content

    def get_file_from_archive(self, archive, name):
        with tarfile.open(archive, 'r:gz') as archive_file:
            named_member = archive_file.getmember(name)

            named_file = archive_file.extractfile(named_member)
            file_content = named_file.read()
            named_file.close()

        return file_content


    def test_tar_impl_can_list_members_correctly(self):
        tar_archive = path.join(self.TEST_FILE_PREFIX, 'new_version1.tgz')
        test_class = patcher.XDelta3TarImpl(tar_archive)

        expected_members = ['binary_file',
                            'long_lorem.txt',
                            'new folder/new file1.txt',
                            'short_lorem.txt',
                            'updated folder/updated file.txt',
                            'updated folder/.hidden_updated_file.txt']


        self.assertEquals(expected_members, test_class.list_files())

    def test_tar_impl_can_extract_members_correctly(self):
        tar_archive = path.join(self.TEST_FILE_PREFIX, 'new_version1.tgz')
        test_class = patcher.XDelta3TarImpl(tar_archive)

        test_class.expand('new folder/new file1.txt', self.temp_dir)

        actual_content = self.get_content(path.join(self.temp_dir,
                                                    'new folder',
                                                    'new file1.txt'))

        self.assertEquals('new file content\n', actual_content)
