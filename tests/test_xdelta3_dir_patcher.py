import imp
import unittest
import tarfile

from filecmp import dircmp, cmp
from mock import Mock
from shutil import rmtree, copytree
from subprocess import CalledProcessError, check_output, STDOUT
from tempfile import mkdtemp
from os import path, remove, walk, chmod
from stat import S_IRWXU, S_IRWXG, S_IROTH, S_IXOTH

# Dashes are standard for exec scipts but not allowed for modules in Python. We
# use the script standard since we will be running that file as a script most
# often.
patcher = imp.load_source("xdelta3-dir-patcher", "xdelta3-dir-patcher")

class TestXDelta3DirPatcher(unittest.TestCase):
    EXECUTABLE="xdelta3-dir-patcher"

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

    # Full-spec integration tests
    def test_apply_patch_works(self):
        old_path = path.join('tests', 'test_files', 'old_version1')
        delta_path = path.join('tests', 'test_files', 'patch1.xdelta.tgz')
        output = check_output(["./%s" % self.EXECUTABLE, "apply", old_path, delta_path, self.temp_dir, "--ignore-euid"] )

        new_path = path.join('tests', 'test_files', 'new_version1')

        self.compare_trees(self.temp_dir, new_path)

    def test_apply_patch_works_with_root_dir_specified(self):
        old_path = path.join('tests', 'test_files', 'old_version1')
        delta_path = path.join('tests', 'test_files', 'patch2.xdelta.tgz')
        output = check_output(["./%s" % self.EXECUTABLE,
                               "apply",
                               "-d", "inner_dir",
                               old_path,
                               delta_path,
                               self.temp_dir,
                               "--ignore-euid"] )

        new_path = path.join('tests', 'test_files', 'new_version1')

        self.compare_trees(self.temp_dir, new_path)


    def test_apply_patch_creates_target_dir(self):
        old_path = path.join('tests', 'test_files', 'old_version1')
        delta_path = path.join('tests', 'test_files', 'patch1.xdelta.tgz')

        rmtree(self.temp_dir)
        output = check_output(["./%s" % self.EXECUTABLE, "apply", old_path, delta_path, self.temp_dir, "--ignore-euid"] )

        new_path = path.join('tests', 'test_files', 'new_version1')

        self.compare_trees(self.temp_dir, new_path)

    def test_apply_patch_works_with_old_files_present_in_target(self):
        old_path = path.join('tests', 'test_files', 'old_version1')

        rmtree(self.temp_dir)
        copytree(old_path, self.temp_dir)

        delta_path = path.join('tests', 'test_files', 'patch1.xdelta.tgz')
        output = check_output(["./%s" % self.EXECUTABLE, "apply", self.temp_dir, delta_path, "--ignore-euid"] )

        new_path = path.join('tests', 'test_files', 'new_version1')
        self.compare_trees(self.temp_dir, new_path)

    def test_apply_patch_works_with_old_files_present_in_target_with_root_patch_dir(self):
        old_path = path.join('tests', 'test_files', 'old_version1')

        rmtree(self.temp_dir)
        copytree(old_path, self.temp_dir)

        delta_path = path.join('tests', 'test_files', 'patch2.xdelta.tgz')
        output = check_output(["./%s" % self.EXECUTABLE,
                               "apply",
                               "-d", "inner_dir",
                               self.temp_dir,
                               delta_path,
                               "--ignore-euid"] )

        new_path = path.join('tests', 'test_files', 'new_version1')
        self.compare_trees(self.temp_dir, new_path)

    def test_apply_works_with_symbolic_links_present(self):
        old_path = path.join('tests', 'test_files', 'old_version_symlinks1')
        delta_path = path.join('tests', 'test_files', 'patch_symlinks1.xdelta.tgz')

        check_output(["./%s" % self.EXECUTABLE, "apply", old_path, delta_path, self.temp_dir, "--ignore-euid"] )

        new_path = path.join('tests', 'test_files', 'new_version_symlinks1')
        self.compare_trees(self.temp_dir, new_path)

    def test_diff_works(self):
        # Implicit dependency on previous apply integration test
        old_path = path.join('tests', 'test_files', 'old_version1')
        new_path = path.join('tests', 'test_files', 'new_version1')
        generated_delta_path = path.join(self.temp_dir2, 'patch.xdelta')

        check_output(["./%s" % self.EXECUTABLE, "diff", old_path, new_path, generated_delta_path] )
        check_output(["./%s" % self.EXECUTABLE, "apply", old_path, generated_delta_path, self.temp_dir, "--ignore-euid"] )

        self.compare_trees(self.temp_dir, new_path)

    def test_diff_works_with_both_files_as_arguments(self):
        # Implicit dependency on apply integration test
        old_path = path.join('tests', 'test_files', 'old_version1')
        old_bundle = path.join('tests', 'test_files', 'old_version1.tgz')
        new_path = path.join('tests', 'test_files', 'new_version1')
        new_bundle = path.join('tests', 'test_files', 'new_version1.tgz')
        generated_delta_path = path.join(self.temp_dir2, 'patch.xdelta')

        check_output(["./%s" % self.EXECUTABLE, "diff", old_bundle, new_bundle, generated_delta_path] )
        check_output(["./%s" % self.EXECUTABLE, "apply", old_path, generated_delta_path, self.temp_dir, "--ignore-euid"] )

        self.compare_trees(self.temp_dir, new_path)

    def test_diff_adds_the_metadata_file(self):
        # Implicit dependency on apply integration test
        old_path = path.join('tests', 'test_files', 'old_version1')
        old_bundle = path.join('tests', 'test_files', 'old_version1.tgz')
        new_path = path.join('tests', 'test_files', 'new_version1')
        new_bundle = path.join('tests', 'test_files', 'new_version1.tgz')
        generated_delta_path = path.join(self.temp_dir2, 'patch.xdelta')

        metadata_path = path.join('tests', 'test_files', 'metadata1.txt')

        check_output(["./%s" % self.EXECUTABLE,
                      "diff",
                      "--metadata", metadata_path,
                      old_bundle,
                      new_bundle,
                      generated_delta_path] )

        metadata = self.get_file_from_archive(generated_delta_path, '.info')

        self.assertEquals(self.get_content(metadata_path), metadata)

    def test_diff_works_with_staging_directory_set(self):
        # Implicit dependency on apply integration test
        old_path = path.join('tests', 'test_files', 'old_version1')
        old_bundle = path.join('tests', 'test_files', 'old_version1.tgz')
        new_path = path.join('tests', 'test_files', 'new_version1')
        new_bundle = path.join('tests', 'test_files', 'new_version1.tgz')
        generated_delta_path = path.join(self.temp_dir2, 'patch.xdelta')

        staging_dir = mkdtemp(prefix="%s_" % self.__class__.__name__)

        try:
            check_output(["./%s" % self.EXECUTABLE, "diff",
                          "--staging-dir", staging_dir,
                          old_bundle,
                          new_bundle,
                          generated_delta_path] )
        finally:
            rmtree(staging_dir)

        check_output(["./%s" % self.EXECUTABLE, "apply", old_path,
                      generated_delta_path,
                      self.temp_dir,
                      "--ignore-euid"] )

        self.compare_trees(self.temp_dir, new_path)

    def test_diff_works_with_old_file_as_arguments(self):
        # Implicit dependency on apply integration test
        old_path = path.join('tests', 'test_files', 'old_version1')
        old_bundle = path.join('tests', 'test_files', 'old_version1.tgz')
        new_path = path.join('tests', 'test_files', 'new_version1')
        generated_delta_path = path.join(self.temp_dir2, 'patch.xdelta')

        check_output(["./%s" % self.EXECUTABLE, "diff", old_bundle, new_path, generated_delta_path] )
        check_output(["./%s" % self.EXECUTABLE, "apply", old_path, generated_delta_path, self.temp_dir, "--ignore-euid"] )

        self.compare_trees(self.temp_dir, new_path)

    def test_diff_works_with_new_file_as_arguments(self):
        # Implicit dependency on apply integration test
        old_path = path.join('tests', 'test_files', 'old_version1')
        new_path = path.join('tests', 'test_files', 'new_version1')
        new_bundle = path.join('tests', 'test_files', 'new_version1.tgz')
        generated_delta_path = path.join(self.temp_dir2, 'patch.xdelta')

        check_output(["./%s" % self.EXECUTABLE, "diff", old_path, new_bundle, generated_delta_path] )
        check_output(["./%s" % self.EXECUTABLE, "apply", old_path, generated_delta_path, self.temp_dir, "--ignore-euid"] )

        self.compare_trees(self.temp_dir, new_path)

    def test_diff_works_with_symbolic_links_present(self):
        # Implicit dependency on previous apply integration test
        old_path = path.join('tests', 'test_files', 'old_version_symlinks1')
        new_path = path.join('tests', 'test_files', 'new_version_symlinks1')

        generated_delta_path = path.join(self.temp_dir2, 'patch_symlinks.xdelta')

        check_output(["./%s" % self.EXECUTABLE, "diff", old_path, new_path, generated_delta_path] )
        check_output(["./%s" % self.EXECUTABLE, "apply", old_path, generated_delta_path, self.temp_dir, "--ignore-euid"] )

        self.compare_trees(self.temp_dir, new_path)

    # Integration tests
    def test_version_is_correct(self):
        output = check_output(["./%s" % self.EXECUTABLE, '--version'],
                              stderr=STDOUT,
                              universal_newlines=True)
        self.assertEqual(output, "%s v0.6\n" % self.EXECUTABLE)

    def test_help_is_available(self):
        self.assertIsNotNone(check_output(["./%s" % self.EXECUTABLE, '-h']))
        self.assertIsNotNone(check_output(["./%s" % self.EXECUTABLE, '--help']))

    def test_debugging_is_available(self):
        output = check_output(["./%s" % self.EXECUTABLE, '--debug'])
        self.assertNotIn("unrecognized arguments", output.decode('utf-8'))

    def test_help_is_printed_if_no_action_command(self):
        output = check_output(["./%s" % self.EXECUTABLE])
        self.assertIn("usage: ", output.decode('utf-8'))

    def test_apply_is_allowed_as_action_command(self):
        try:
            check_output(["./%s" % self.EXECUTABLE, "apply"],
                         stderr=STDOUT)
        except CalledProcessError as e:
            self.assertIn("usage: ", e.output.decode('utf-8'))
            self.assertNotIn("invalid choice: ", e.output.decode('utf-8'))
        else: self.fail()

    def test_apply_usage_is_printed_if_not_enough_args(self):
        try:
            check_output(["./%s" % self.EXECUTABLE, "apply"],
                         stderr=STDOUT)
        except CalledProcessError as e:
            self.assertIn("the following arguments are required: ",
                          e.output.decode('utf-8'))
        else: self.fail()

    def test_apply_usage_is_not_printed_if_args_are_correct(self):
        old_path = path.join('tests', 'test_files', 'old_version1')
        delta_path = path.join('tests', 'test_files', 'patch1.xdelta.tgz')
        output = check_output(["./%s" % self.EXECUTABLE, "apply", old_path, delta_path, self.temp_dir, "--ignore-euid"] )
        self.assertNotIn("usage: ", output.decode('utf-8'))

    def test_apply_usage_is_not_printed_if_args_are_correct2(self):
        old_path = path.join('tests', 'test_files', 'old_version1')

        rmtree(self.temp_dir)
        copytree(old_path, self.temp_dir)

        delta_path = path.join('tests', 'test_files', 'patch1.xdelta.tgz')
        output = check_output(["./%s" % self.EXECUTABLE, "apply", self.temp_dir, delta_path, "--ignore-euid"] )
        self.assertNotIn("usage: ",
                         output.decode('utf-8'))

    def test_diff_usage_is_printed_if_not_enough_args(self):
        try:
            check_output(["./%s" % self.EXECUTABLE, "diff"],
                         stderr=STDOUT)
        except CalledProcessError as e:
            self.assertIn("the following arguments are required: ",
                          e.output.decode ('utf-8'))
        else: self.fail()

    def test_diff_is_allowed_as_action_command(self):
        try:
            check_output(["./%s" % self.EXECUTABLE, "diff"],
                         stderr=STDOUT)
        except CalledProcessError as e:
            self.assertIn("usage: ", e.output.decode('utf-8'))
            self.assertNotIn("invalid choice: ", e.output.decode('utf-8'))
        else: self.fail()

    def test_diff_usage_is_not_printed_if_args_are_correct(self):
        old_path = path.join('tests', 'test_files', 'old_version1')
        new_path = path.join('tests', 'test_files', 'new_version1')
        delta_path = path.join(self.temp_dir, 'foo.tgz')
        output = check_output(["./%s" % self.EXECUTABLE, "diff", old_path, new_path, delta_path] )
        self.assertNotIn("usage: ", output.decode('utf-8'))

    def test_other_actions_are_not_allowed(self):
        try:
            check_output(["./%s" % self.EXECUTABLE, "foobar"],
                         stderr=STDOUT)
        except CalledProcessError as e:
            self.assertIn("usage: ", e.output.decode('utf-8'))
            self.assertIn("invalid choice: ", e.output.decode('utf-8'))
        else: self.fail()

    # Unit tests
    def test_run_calls_diff_with_correct_arguments_if_action_is_diff(self):
        args = patcher.AttributeDict()
        args.action = 'diff'
        args.old_version = 'old'
        args.new_version = 'new'
        args.patch_bundle = 'target'
        args.metadata = 'metadata'
        args.staging_dir = 'staging_dir'
        args.debug = False

        test_object = patcher.XDelta3DirPatcher(args)
        test_object.diff = Mock()

        test_object.run()

        test_object.diff.assert_called_once_with('old', 'new', 'target',
                                                 'metadata',
                                                 'staging_dir')

    def test_run_calls_apply_with_correct_arguments_if_action_is_apply(self):
        args = patcher.AttributeDict()
        args.action = 'apply'
        args.old_dir = 'old'
        args.patch_bundle = 'patch'
        args.ignore_euid = True
        args.target_dir = 'target'
        args.root_patch_dir = None

        test_object = patcher.XDelta3DirPatcher(args)
        test_object.apply = Mock()

        test_object.run()

        test_object.apply.assert_called_once_with('old', 'patch', 'target', None)

    def test_run_calls_apply_with_correct_arguments_if_action_is_apply_and_root_is_specified(self):
        args = patcher.AttributeDict()
        args.action = 'apply'
        args.old_dir = 'old'
        args.patch_bundle = 'patch'
        args.ignore_euid = True
        args.target_dir = 'target'
        args.root_patch_dir = 'foobar'

        test_object = patcher.XDelta3DirPatcher(args)
        test_object.apply = Mock()

        test_object.run()

        test_object.apply.assert_called_once_with('old', 'patch', 'target', 'foobar')


    def test_run_calls_apply_with_correct_arguments_if_action_is_apply_and_no_target_specified(self):
        args = patcher.AttributeDict()
        args.action = 'apply'
        args.old_dir = 'old'
        args.patch_bundle = 'patch'
        args.ignore_euid = True
        args.target_dir = None
        args.root_patch_dir = None

        test_object = patcher.XDelta3DirPatcher(args)
        test_object.apply = Mock()

        test_object.run()

        test_object.apply.assert_called_once_with('old', 'patch', 'old', None)

    def test_check_euid_does_not_break_if_ignoring_euid(self):
        # Implicit: Does not throw error
        patcher.XDelta3DirPatcher.check_euid(True)

    def test_check_euid_does_not_break_if_not_ignoring_euid_and_euid_is_0(self):
        mock_method = Mock(return_value = 0)
        # Implicit: Does not throw error
        patcher.XDelta3DirPatcher.check_euid(False, mock_method)

    def test_check_euid_breaks_if_not_ignoring_euid_and_euid_is_not_0(self):
        mock_method = Mock(return_value = 123)
        try:
            patcher.XDelta3DirPatcher.check_euid(False, mock_method)
        except:
            # Expected exception
            pass
        else:
            fail("Should have thrown exception")

    def test_check_that_the_correct_staging_dir_is_used_for_all_transient_files(self):
        staging_dir = mkdtemp(prefix="%s_" % self.__class__.__name__)
        target_dir = mkdtemp(prefix="%s_" % self.__class__.__name__)

        old_bundle = path.join('tests', 'test_files', 'old_version1.tgz')
        new_bundle = path.join('tests', 'test_files', 'new_version1.tgz')
        generated_delta_path = path.join(self.temp_dir2, 'patch.xdelta')

        class MockXDImplStagingTest:
            @staticmethod
            def diff(old_file, new_file, target_file, debug = False):
                if old_file:
                  self.assertTrue(old_file.startswith(staging_dir))

                self.assertTrue(new_file.startswith(staging_dir))
                self.assertTrue(target_file.startswith(staging_dir))

                # passthrough since other methods depend on actual output
                patcher.XDelta3Impl().diff(old_file, new_file, target_file, debug)

        args = patcher.AttributeDict()
        args.action = 'diff'
        args.debug = True
        args.metadata = None
        args.old_version = old_bundle
        args.new_version = new_bundle
        args.patch_bundle = generated_delta_path
        args.target_dir = target_dir
        args.staging_dir = staging_dir

        patcher.XDelta3DirPatcher(args, delta_impl = MockXDImplStagingTest).run()

    def test_expand_archive_works(self):
        archive = path.join('tests', 'test_files', 'old_version1.tgz')
        old_dir = path.join('tests', 'test_files', 'old_version1')

        result_dir = patcher.XDelta3DirPatcher.expand_archive(archive)

        self.compare_trees(result_dir, old_dir)

        # Clean up
        rmtree(result_dir)

    # ------------------- Test for archive implementation picking
    def test_get_archive_instance_returns_tar_for_correct_files(self):
        tar_archive = path.join('tests', 'test_files', 'old_version1.tgz')
        impl_instance = patcher.XDelta3DirPatcher.get_archive_instance(tar_archive)

        self.assertEquals(impl_instance.__class__,
                          patcher.XDelta3TarImpl)

    def test_get_archive_instance_returns_zip_for_correct_files(self):
        zip_archive = path.join('tests', 'test_files', 'old_version1.zip')
        impl_instance = patcher.XDelta3DirPatcher.get_archive_instance(zip_archive)

        self.assertEquals(impl_instance.__class__,
                          patcher.XDelta3ZipImpl)

    def test_get_archive_instance_fails_if_not_supported(self):
        bad_archive = path.join('tests', 'test_files', 'not_an_archive.foo')

        with self.assertRaises(RuntimeError) as error:
            patcher.XDelta3DirPatcher.get_archive_instance(bad_archive)

            # Sanity check
            self.assertTrue(False)

        exception = error.exception
        self.assertEqual(str(exception),
                         'Error! Archive %s bad or not supported!' % bad_archive)

    # ------------------- XDeltaImpl tests
    def test_xdelta_impl_run_command_invokes_the_command(self):
        # TODO: implement the test
        pass

    def test_xdelta_impl_diff_uses_correct_system_arguments(self):
        test_class = patcher.XDelta3Impl
        original_run_command = test_class.run_command
        test_class.run_command = Mock()

        test_class.diff("old", "new", "target")

        test_class.run_command.assert_called_once_with(['xdelta3', '-f', '-e', '-s', 'old', 'new', 'target'])

        test_class.run_command = original_run_command

    def test_xdelta_impl_diff_uses_correct_system_arguments_when_old_file_is_not_there(self):
        test_class = patcher.XDelta3Impl
        original_run_command = test_class.run_command
        test_class.run_command = Mock()

        test_class.diff(None, "new", "target")

        test_class.run_command.assert_called_once_with(['xdelta3', '-f', '-e', 'new', 'target'])

        test_class.run_command = original_run_command

    def test_xdelta_impl_apply_uses_correct_system_arguments(self):
        test_class = patcher.XDelta3Impl
        original_run_command = test_class.run_command
        test_class.run_command = Mock()

        test_class.apply("old", "patch", "target", None)

        test_class.run_command.assert_called_once_with(['xdelta3', '-f', '-d', '-s', 'old', 'patch', 'target'])

        test_class.run_command = original_run_command

    def test_xdelta_impl_apply_uses_correct_system_arguments_when_old_file_is_not_there(self):
        test_class = patcher.XDelta3Impl
        original_run_command = test_class.run_command
        test_class.run_command = Mock()

        test_class.apply(None, "patch", "target", None)

        test_class.run_command.assert_called_once_with(['xdelta3', '-f', '-d', 'patch', 'target'])

        test_class.run_command = original_run_command

