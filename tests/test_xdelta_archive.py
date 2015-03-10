import imp
import unittest

from mock import Mock
from os  import path

TEST_FILE_PREFIX = path.join('tests', 'test_files', 'fs_impl')

# Dashes are standard for exec scipts but not allowed for modules in Python. We
# use the script standard since we will be running that file as a script most
# often.
patcher = imp.load_source("xdelta3-dir-patcher", "xdelta3-dir-patcher")

class TestXDeltaArchive(unittest.TestCase):
    TEST_FILE_PREFIX = path.join('tests', 'test_files', 'archive_instance')

    def setUp(self):
        self.test_class = patcher.XDeltaArchive

    def tearDown(self):
        pass

    def get_archive_type(self, suffix):
        return path.join(self.TEST_FILE_PREFIX,
                         'old_version1%s' % suffix)

    def test_get_archive_class_returns_tar_for_correct_files(self):

        with self.test_class(self.get_archive_type('.tgz')) as archive_instance:
            self.assertEquals(archive_instance.__class__,
                              patcher.XDelta3TarImpl)

    def test_get_archive_class_returns_zip_for_correct_files(self):
        with self.test_class(self.get_archive_type('.zip')) as archive_instance:
            self.assertEquals(archive_instance.__class__,
                              patcher.XDelta3ZipImpl)

    def test_get_archive_class_returns_zip_for_correct_files(self):
        with self.test_class(self.get_archive_type('')) as archive_instance:
            self.assertEquals(archive_instance.__class__,
                              patcher.XDelta3FsImpl)

    def test_get_archive_class_fails_if_not_supported(self):
        bad_archive = path.join(self.TEST_FILE_PREFIX, 'not_an_archive.foo')

        with self.assertRaises(RuntimeError) as error:
            self.test_class(bad_archive)

            # Sanity check
            self.assertTrue(False)

        exception = error.exception
        self.assertEqual(str(exception),
                         'Error! Archive %s bad or not supported!' % bad_archive)

