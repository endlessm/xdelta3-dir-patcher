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
from shutil import rmtree, copytree
from subprocess import CalledProcessError, STDOUT
from tempfile import mkdtemp
from os import path, remove, walk, chmod
from stat import S_IRWXU, S_IRWXG, S_IROTH, S_IXOTH

from .test_helpers import TestHelpers

class TestXDelta3DirPatcher(unittest.TestCase):
    # Dashes are standard for exec scipts but not allowed for modules in Python. We
    # use the script standard since we will be running that file as a script most
    # often.
    patcher = imp.load_source("xdelta3-dir-patcher", "xdelta3-dir-patcher")

    EXECUTABLE="xdelta3-dir-patcher"
    TEST_FILE_PREFIX = path.join('tests', 'test_files', 'dir_patcher')

    def setUp(self):
        self.temp_dir = mkdtemp(prefix="%s_" % self.__class__.__name__)
        chmod(self.temp_dir, S_IRWXU | S_IRWXG | S_IROTH | S_IXOTH)
        self.temp_dir2 = mkdtemp(prefix="%s_" % self.__class__.__name__)
        chmod(self.temp_dir2, S_IRWXU | S_IRWXG | S_IROTH | S_IXOTH)

        self.test_class = self.patcher.XDelta3DirPatcher
        self.xdelta_test_class = self.patcher.XDelta3Impl

    def tearDown(self):
        rmtree(self.temp_dir)
        rmtree(self.temp_dir2)

    def get_file_from_archive(self, archive, name):
        with tarfile.open(archive, 'r:gz') as archive_file:
            named_member = archive_file.getmember(name)

            named_file = archive_file.extractfile(named_member)
            file_content = named_file.read()
            named_file.close()

        return file_content

    # Full-spec integration tests
    def test_apply_patch_works(self):
        old_path = path.join(self.TEST_FILE_PREFIX, 'old_version1')
        delta_path = path.join(self.TEST_FILE_PREFIX, 'patch1.xdelta.tgz')
        output = TestHelpers.check_output2(["./%s" % self.EXECUTABLE,
                                            "--debug",
                                            "apply",
                                            old_path,
                                            delta_path,
                                            self.temp_dir,
                                            "--ignore-euid"] )

        new_path = path.join(self.TEST_FILE_PREFIX, 'new_version1')

        TestHelpers.compare_trees(self, self.temp_dir, new_path)

    def test_apply_patch_works_with_root_dir_specified(self):
        old_path = path.join(self.TEST_FILE_PREFIX, 'old_version1')
        delta_path = path.join(self.TEST_FILE_PREFIX, 'patch2.xdelta.tgz')
        output = TestHelpers.check_output2(["./%s" % self.EXECUTABLE,
                                            "--debug",
                                            "apply",
                                            "-d", "inner_dir",
                                            old_path,
                                            delta_path,
                                            self.temp_dir,
                                            "--ignore-euid"])

        new_path = path.join(self.TEST_FILE_PREFIX, 'new_version1')

        TestHelpers.compare_trees(self, self.temp_dir, new_path)


    def test_apply_patch_creates_target_dir(self):
        old_path = path.join(self.TEST_FILE_PREFIX, 'old_version1')
        delta_path = path.join(self.TEST_FILE_PREFIX, 'patch1.xdelta.tgz')

        rmtree(self.temp_dir)
        output = TestHelpers.check_output2(["./%s" % self.EXECUTABLE,
                                            "--debug",
                                            "apply",
                                            old_path,
                                            delta_path,
                                            self.temp_dir,
                                            "--ignore-euid"])

        new_path = path.join(self.TEST_FILE_PREFIX, 'new_version1')

        TestHelpers.compare_trees(self, self.temp_dir, new_path)

    def test_apply_patch_works_with_old_files_present_in_target(self):
        old_path = path.join(self.TEST_FILE_PREFIX, 'old_version1')

        rmtree(self.temp_dir)
        copytree(old_path, self.temp_dir)

        delta_path = path.join(self.TEST_FILE_PREFIX, 'patch1.xdelta.tgz')
        output = TestHelpers.check_output2(["./%s" % self.EXECUTABLE,
                                            "--verbose",
                                            "apply",
                                            self.temp_dir,
                                            delta_path,
                                            "--ignore-euid"])

        new_path = path.join(self.TEST_FILE_PREFIX, 'new_version1')
        TestHelpers.compare_trees(self, self.temp_dir, new_path)

    def test_apply_patch_works_with_old_files_present_in_target_with_root_patch_dir(self):
        old_path = path.join(self.TEST_FILE_PREFIX, 'old_version1')

        rmtree(self.temp_dir)
        copytree(old_path, self.temp_dir)

        delta_path = path.join(self.TEST_FILE_PREFIX, 'patch2.xdelta.tgz')
        output = TestHelpers.check_output2(["./%s" % self.EXECUTABLE,
                                            "--debug",
                                            "apply",
                                            "-d", "inner_dir",
                                            self.temp_dir,
                                            delta_path,
                                            "--ignore-euid"] )

        new_path = path.join(self.TEST_FILE_PREFIX, 'new_version1')
        TestHelpers.compare_trees(self, self.temp_dir, new_path)

    def test_apply_works_with_symbolic_links_present(self):
        old_path = path.join(self.TEST_FILE_PREFIX, 'old_version_symlinks1')
        delta_path = path.join(self.TEST_FILE_PREFIX, 'patch_symlinks1.xdelta.tgz')

        output = TestHelpers.check_output2(["./%s" % self.EXECUTABLE,
                                            "--debug",
                                            "apply",
                                            old_path,
                                            delta_path,
                                            self.temp_dir,
                                            "--ignore-euid"])

        new_path = path.join(self.TEST_FILE_PREFIX, 'new_version_symlinks1')
        TestHelpers.compare_trees(self, self.temp_dir, new_path)

    def test_diff_works(self):
        # Implicit dependency on previous apply integration test
        old_path = path.join(self.TEST_FILE_PREFIX, 'old_version1')
        new_path = path.join(self.TEST_FILE_PREFIX, 'new_version1')
        generated_delta_path = path.join(self.temp_dir2, 'patch.xdelta')

        TestHelpers.check_output2(["./%s" % self.EXECUTABLE,
                                   "--debug",
                                   "diff",
                                   old_path,
                                   new_path,
                                   generated_delta_path])

        print('-' * 70)

        TestHelpers.check_output2(["./%s" % self.EXECUTABLE,
                                   "--debug",
                                   "apply",
                                   old_path,
                                   generated_delta_path,
                                   self.temp_dir,
                                   "--ignore-euid"])

        TestHelpers.compare_trees(self, self.temp_dir, new_path)

    def test_diff_works_with_both_files_as_arguments(self):
        # Implicit dependency on apply integration test
        old_path = path.join(self.TEST_FILE_PREFIX, 'old_version1')
        old_bundle = path.join(self.TEST_FILE_PREFIX, 'old_version1.tgz')
        new_path = path.join(self.TEST_FILE_PREFIX, 'new_version1')
        new_bundle = path.join(self.TEST_FILE_PREFIX, 'new_version1.tgz')
        generated_delta_path = path.join(self.temp_dir2, 'patch.xdelta')

        TestHelpers.check_output2(["./%s" % self.EXECUTABLE,
                                   "--debug",
                                   "diff",
                                   old_bundle,
                                   new_bundle,
                                   generated_delta_path])

        TestHelpers.check_output2(["./%s" % self.EXECUTABLE,
                                   "--debug",
                                   "apply",
                                   old_path,
                                   generated_delta_path,
                                   self.temp_dir,
                                   "--ignore-euid"])

        TestHelpers.compare_trees(self, self.temp_dir, new_path)

    def test_diff_adds_the_metadata_file(self):
        # Implicit dependency on apply integration test
        old_path = path.join(self.TEST_FILE_PREFIX, 'old_version1')
        old_bundle = path.join(self.TEST_FILE_PREFIX, 'old_version1.tgz')
        new_path = path.join(self.TEST_FILE_PREFIX, 'new_version1')
        new_bundle = path.join(self.TEST_FILE_PREFIX, 'new_version1.tgz')
        generated_delta_path = path.join(self.temp_dir2, 'patch.xdelta')

        metadata_path = path.join(self.TEST_FILE_PREFIX, 'metadata1.txt')

        TestHelpers.check_output2(["./%s" % self.EXECUTABLE,
                                   "--debug",
                                   "diff",
                                   "--metadata", metadata_path,
                                   old_bundle,
                                   new_bundle,
                                   generated_delta_path])

        metadata = self.get_file_from_archive(generated_delta_path, '.info')

        self.assertEquals(TestHelpers.get_content(metadata_path), metadata)

    def test_diff_works_with_staging_directory_set(self):
        # Implicit dependency on apply integration test
        old_path = path.join(self.TEST_FILE_PREFIX, 'old_version1')
        old_bundle = path.join(self.TEST_FILE_PREFIX, 'old_version1.tgz')
        new_path = path.join(self.TEST_FILE_PREFIX, 'new_version1')
        new_bundle = path.join(self.TEST_FILE_PREFIX, 'new_version1.tgz')
        generated_delta_path = path.join(self.temp_dir2, 'patch.xdelta')

        staging_dir = mkdtemp(prefix="%s_" % self.__class__.__name__)

        try:
            TestHelpers.check_output2(["./%s" % self.EXECUTABLE,
                                       "--debug",
                                       "--staging-dir", staging_dir,
                                       "diff",
                                       old_bundle,
                                       new_bundle,
                                       generated_delta_path] )
        finally:
            rmtree(staging_dir)

        TestHelpers.check_output2(["./%s" % self.EXECUTABLE,
                                   "--debug",
                                   "apply",
                                   old_path,
                                   generated_delta_path,
                                   self.temp_dir,
                                   "--ignore-euid"] )

        TestHelpers.compare_trees(self, self.temp_dir, new_path)

    def test_diff_works_with_old_file_as_arguments(self):
        # Implicit dependency on apply integration test
        old_path = path.join(self.TEST_FILE_PREFIX, 'old_version1')
        old_bundle = path.join(self.TEST_FILE_PREFIX, 'old_version1.tgz')
        new_path = path.join(self.TEST_FILE_PREFIX, 'new_version1')
        generated_delta_path = path.join(self.temp_dir2, 'patch.xdelta')

        TestHelpers.check_output2(["./%s" % self.EXECUTABLE,
                                   "--debug",
                                   "diff",
                                   old_bundle,
                                   new_path,
                                   generated_delta_path])

        TestHelpers.check_output2(["./%s" % self.EXECUTABLE,
                                   "--debug",
                                   "apply",
                                   old_path,
                                   generated_delta_path,
                                   self.temp_dir,
                                   "--ignore-euid"])

        TestHelpers.compare_trees(self, self.temp_dir, new_path)

    def test_diff_works_with_new_file_as_arguments(self):
        # Implicit dependency on apply integration test
        old_path = path.join(self.TEST_FILE_PREFIX, 'old_version1')
        new_path = path.join(self.TEST_FILE_PREFIX, 'new_version1')
        new_bundle = path.join(self.TEST_FILE_PREFIX, 'new_version1.tgz')
        generated_delta_path = path.join(self.temp_dir2, 'patch.xdelta')

        TestHelpers.check_output2(["./%s" % self.EXECUTABLE,
                                   "--debug",
                                   "diff",
                                   old_path,
                                   new_bundle,
                                   generated_delta_path])

        TestHelpers.check_output2(["./%s" % self.EXECUTABLE,
                                   "--debug",
                                   "apply",
                                   old_path,
                                   generated_delta_path,
                                   self.temp_dir,
                                   "--ignore-euid"])

        TestHelpers.compare_trees(self, self.temp_dir, new_path)

    def test_diff_works_with_symbolic_links_present(self):
        # Implicit dependency on previous apply integration test
        old_path = path.join(self.TEST_FILE_PREFIX, 'old_version_symlinks1')
        new_path = path.join(self.TEST_FILE_PREFIX, 'new_version_symlinks1')

        generated_delta_path = path.join(self.temp_dir2, 'patch_symlinks.xdelta')

        TestHelpers.check_output2(["./%s" % self.EXECUTABLE,
                                   "--debug",
                                   "diff",
                                   old_path,
                                   new_path,
                                   generated_delta_path])

        TestHelpers.check_output2(["./%s" % self.EXECUTABLE,
                                   "--debug",
                                   "apply",
                                   old_path,
                                   generated_delta_path,
                                   self.temp_dir,
                                   "--ignore-euid"])

        TestHelpers.compare_trees(self, self.temp_dir, new_path)

    # Integration tests
    def test_version_is_correct(self):
        output = TestHelpers.check_output2(["./%s" % self.EXECUTABLE,
                                            '--version'])
        self.assertEqual(output, "%s v0.6.4\n" % self.EXECUTABLE)

    def test_help_is_available(self):
        self.assertIsNotNone(TestHelpers.check_output2(["./%s" % self.EXECUTABLE,
                                                        '-h']))
        self.assertIsNotNone(TestHelpers.check_output2(["./%s" % self.EXECUTABLE,
                                                        '--help']))

    def test_debugging_is_available(self):
        output = TestHelpers.check_output2(["./%s" % self.EXECUTABLE,
                                            '--debug'])
        self.assertNotIn("unrecognized arguments", output)

    def test_help_is_printed_if_no_action_command(self):
        output = TestHelpers.check_output2(["./%s" % self.EXECUTABLE])
        self.assertIn("usage: ", output)

    def test_apply_is_allowed_as_action_command(self):
        try:
            output = TestHelpers.check_output2(["./%s" % self.EXECUTABLE,
                                                'apply'])
        except CalledProcessError as e:
            self.assertIn("usage: ", e.output)
            self.assertNotIn("invalid choice: ", e.output)
        else: self.fail()

    def test_apply_usage_is_printed_if_not_enough_args(self):
        try:
            output = TestHelpers.check_output2(["./%s" % self.EXECUTABLE,
                                                'apply'])
        except CalledProcessError as e:
            self.assertIn("the following arguments are required: ",
                          e.output)
        else: self.fail()

    def test_apply_usage_is_not_printed_if_args_are_correct(self):
        old_path = path.join(self.TEST_FILE_PREFIX, 'old_version1')
        delta_path = path.join(self.TEST_FILE_PREFIX, 'patch1.xdelta.tgz')
        output = TestHelpers.check_output2(["./%s" % self.EXECUTABLE,
                                            "apply",
                                            old_path,
                                            delta_path,
                                            self.temp_dir,
                                            "--ignore-euid"])

        self.assertNotIn("usage: ", output)

    def test_apply_usage_is_not_printed_if_args_are_correct2(self):
        old_path = path.join(self.TEST_FILE_PREFIX, 'old_version1')

        rmtree(self.temp_dir)
        copytree(old_path, self.temp_dir)

        delta_path = path.join(self.TEST_FILE_PREFIX, 'patch1.xdelta.tgz')
        output = TestHelpers.check_output2(["./%s" % self.EXECUTABLE,
                                            "apply",
                                            self.temp_dir,
                                            delta_path,
                                            "--ignore-euid"])

        self.assertNotIn("usage: ", output)

    def test_diff_usage_is_printed_if_not_enough_args(self):
        try:
            TestHelpers.check_output2(["./%s" % self.EXECUTABLE,
                                       'diff'])
        except CalledProcessError as e:
            self.assertIn("the following arguments are required: ",
                          e.output)
        else: self.fail()

    def test_diff_is_allowed_as_action_command(self):
        try:
            TestHelpers.check_output2(["./%s" % self.EXECUTABLE,
                                       'diff'])
        except CalledProcessError as e:
            self.assertIn("usage: ", e.output)
            self.assertNotIn("invalid choice: ", e.output)
        else: self.fail()

    def test_diff_usage_is_not_printed_if_args_are_correct(self):
        old_path = path.join(self.TEST_FILE_PREFIX, 'old_version1')
        new_path = path.join(self.TEST_FILE_PREFIX, 'new_version1')
        delta_path = path.join(self.temp_dir, 'foo.tgz')

        output = TestHelpers.check_output2(["./%s" % self.EXECUTABLE,
                                       'diff',
                                       old_path,
                                       new_path,
                                       delta_path])

        self.assertNotIn("usage: ", output)

    def test_other_actions_are_not_allowed(self):
        try:
            TestHelpers.check_output2(["./%s" % self.EXECUTABLE,
                                       'foobar'])
        except CalledProcessError as e:
            self.assertIn("usage: ", e.output)
            self.assertIn("invalid choice: ", e.output)
        else: self.fail()

    # Unit tests
    def test_run_calls_diff_with_correct_arguments_if_action_is_diff(self):
        args = self.patcher.AttributeDict()
        args.action = 'diff'
        args.old_version = 'old'
        args.new_version = 'new'
        args.patch_bundle = 'target'
        args.metadata = 'metadata'
        args.staging_dir = 'staging_dir'
        args.debug = False

        test_object = self.test_class(args)
        test_object.diff = Mock()

        test_object.run()

        test_object.diff.assert_called_once_with('old', 'new', 'target',
                                                 'metadata',
                                                 'staging_dir')

    def test_run_calls_apply_with_correct_arguments_if_action_is_apply(self):
        args = self.patcher.AttributeDict()
        args.action = 'apply'
        args.old_dir = 'old'
        args.patch_bundle = 'patch'
        args.ignore_euid = True
        args.target_dir = 'target'
        args.staging_dir = 'foo'
        args.root_patch_dir = None

        test_object = self.test_class(args)
        test_object.apply = Mock()

        test_object.run()

        test_object.apply.assert_called_once_with('old', 'patch', 'target',
                                                  None, 'foo')

    def test_run_calls_apply_with_correct_arguments_if_action_is_apply_and_root_is_specified(self):
        args = self.patcher.AttributeDict()
        args.action = 'apply'
        args.old_dir = 'old'
        args.patch_bundle = 'patch'
        args.ignore_euid = True
        args.target_dir = 'target'
        args.root_patch_dir = 'foobar'
        args.staging_dir = 'bar'

        test_object = self.test_class(args)
        test_object.apply = Mock()

        test_object.run()

        test_object.apply.assert_called_once_with('old', 'patch', 'target',
                                                  'foobar',
                                                  'bar')

    def test_run_calls_apply_with_correct_arguments_if_action_is_apply_and_no_target_specified(self):
        args = self.patcher.AttributeDict()
        args.action = 'apply'
        args.old_dir = 'old'
        args.patch_bundle = 'patch'
        args.ignore_euid = True
        args.target_dir = None
        args.root_patch_dir = None
        args.staging_dir = 'staging_dir'

        test_object = self.test_class(args)
        test_object.apply = Mock()

        test_object.run()

        test_object.apply.assert_called_once_with('old', 'patch', 'old', None,
                                                  'staging_dir')

    def test_check_euid_does_not_break_if_ignoring_euid(self):
        # Implicit: Does not throw error
        self.test_class.check_euid(True)

    def test_check_euid_does_not_break_if_not_ignoring_euid_and_euid_is_0(self):
        mock_method = Mock(return_value = 0)
        # Implicit: Does not throw error
        self.test_class.check_euid(False, mock_method)

    def test_check_euid_breaks_if_not_ignoring_euid_and_euid_is_not_0(self):
        mock_method = Mock(return_value = 123)
        try:
            self.test_class.check_euid(False, mock_method)
        except:
            # Expected exception
            pass
        else:
            fail("Should have thrown exception")

    def test_check_that_the_correct_staging_dir_is_used_for_all_transient_files(self):
        staging_dir = mkdtemp(prefix="%s_" % self.__class__.__name__)
        target_dir = mkdtemp(prefix="%s_" % self.__class__.__name__)

        old_bundle = path.join(self.TEST_FILE_PREFIX, 'old_version1.tgz')
        new_bundle = path.join(self.TEST_FILE_PREFIX, 'new_version1.tgz')
        generated_delta_path = path.join(self.temp_dir2, 'patch.xdelta')

        class MockXDImplStagingTest():
            @staticmethod
            def diff(old_file, new_file, target_file, debug = False):
                if old_file:
                  self.assertTrue(old_file.startswith(staging_dir))

                self.assertTrue(new_file.startswith(staging_dir))
                self.assertTrue(target_file.startswith(staging_dir))

                # passthrough since other methods depend on actual output
                self.xdelta_test_class().diff(old_file, new_file, target_file,
                                              debug)

        args = self.patcher.AttributeDict()
        args.action = 'diff'
        args.debug = True
        args.verbose = True
        args.metadata = None
        args.old_version = old_bundle
        args.new_version = new_bundle
        args.patch_bundle = generated_delta_path
        args.target_dir = target_dir
        args.staging_dir = staging_dir

        self.test_class(args, delta_impl = MockXDImplStagingTest).run()

    def test_remove_deleted_items_works_correctly_on_empty_dirs(self):
        old_path = path.join(self.TEST_FILE_PREFIX, 'nested_deletion')
        rmtree(self.temp_dir)
        copytree(old_path, self.temp_dir)

        self.test_class.remove_item(self.temp_dir, 'empty_deleted_dir', True)

        self.assertFalse(path.exists(path.join(self.temp_dir, 'empty_deleted_dir')))

    def test_remove_deleted_items_works_correctly_on_files(self):
        old_path = path.join(self.TEST_FILE_PREFIX, 'nested_deletion')
        rmtree(self.temp_dir)
        copytree(old_path, self.temp_dir)

        deleted_path = path.join(self.temp_dir,
                                 'deleted folder',
                                 'deleted internal file1.txt')

        self.test_class.remove_item(self.temp_dir,
                                    deleted_path,
                                    True)

        self.assertFalse(path.exists(deleted_path))

    def test_remove_deleted_items_doesnt_break_on_non_empty_dirs(self):
        old_path = path.join(self.TEST_FILE_PREFIX, 'nested_deletion')
        rmtree(self.temp_dir)
        copytree(old_path, self.temp_dir)

        deleted_path = path.join(self.temp_dir,
                                 'updated folder')


        # Implicit no-exception test
        self.test_class.remove_item(self.temp_dir,
                                    deleted_path,
                                    True)

    # ------------------- XDeltaImpl tests
    def test_xdelta_impl_run_command_invokes_the_command(self):
        # TODO: implement the test
        pass

    def test_xdelta_impl_diff_uses_correct_system_arguments(self):
        original_run_command = self.xdelta_test_class.run_command
        self.xdelta_test_class.run_command = Mock()

        self.xdelta_test_class.diff("old", "new", "target")

        self.xdelta_test_class.run_command \
                              .assert_called_once_with(['xdelta3',
                                                        '-f',
                                                        '-e',
                                                        '-s',
                                                        'old',
                                                        'new',
                                                        'target'])

        self.xdelta_test_class.run_command = original_run_command

    def test_xdelta_impl_diff_uses_correct_system_arguments_when_old_file_is_not_there(self):
        original_run_command = self.xdelta_test_class.run_command
        self.xdelta_test_class.run_command = Mock()

        self.xdelta_test_class.diff(None, "new", "target")

        self.xdelta_test_class.run_command \
                              .assert_called_once_with(['xdelta3',
                                                        '-f',
                                                        '-e',
                                                        'new',
                                                        'target'])

        self.xdelta_test_class.run_command = original_run_command

    def test_xdelta_impl_apply_uses_correct_system_arguments(self):
        original_run_command = self.xdelta_test_class.run_command
        self.xdelta_test_class.run_command = Mock()

        self.xdelta_test_class.apply("old", "patch", "target", None)

        self.xdelta_test_class.run_command \
                              .assert_called_once_with(['xdelta3',
                                                        '-f',
                                                        '-d',
                                                        '-s',
                                                        'old',
                                                        'patch',
                                                        'target'])

        self.xdelta_test_class.run_command = original_run_command

    def test_xdelta_impl_apply_uses_correct_system_arguments_when_old_file_is_not_there(self):
        original_run_command = self.xdelta_test_class.run_command
        self.xdelta_test_class.run_command = Mock()

        self.xdelta_test_class.apply(None, "patch", "target", None)

        self.xdelta_test_class.run_command \
                              .assert_called_once_with(['xdelta3',
                                                        '-f',
                                                        '-d',
                                                        'patch',
                                                        'target'])

        self.xdelta_test_class.run_command = original_run_command
