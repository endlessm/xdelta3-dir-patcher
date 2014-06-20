import imp
import unittest
from filecmp import dircmp
from mock import Mock
from shutil import rmtree, copytree
from subprocess import CalledProcessError, check_output, STDOUT
from tempfile import mkdtemp
from os import path, remove, walk

# Dashes are standard for exec scipts but not allowed for modules in Python. We
# use the script standard since we will be running that file as a script most
# often.
patcher = imp.load_source("xdelta3-dir-patcher", "xdelta3-dir-patcher")

class TestXDelta3DirPatcher(unittest.TestCase):
    EXECUTABLE="xdelta3-dir-patcher"

    def setUp(self):
        self.temp_dir = mkdtemp(prefix="%s_" % self.__class__.__name__)
        self.temp_dir2 = mkdtemp(prefix="%s_" % self.__class__.__name__)

    def tearDown(self):
        rmtree(self.temp_dir)
        rmtree(self.temp_dir2)

    # Full-spec integration tests
    def test_apply_patch_works(self):
        old_path = path.join('tests', 'test_files', 'old_version1')
        delta_path = path.join('tests', 'test_files', 'patch1.xdelta.tgz')
        output = check_output(["./%s" % self.EXECUTABLE, "apply", old_path, delta_path, self.temp_dir, "--ignore-euid"] )

        new_path = path.join('tests', 'test_files', 'new_version1')

        diff = dircmp(self.temp_dir, new_path)

        self.assertEquals([], diff.diff_files)
        self.assertEquals([], diff.common_funny)
        self.assertEquals([], diff.left_only)
        self.assertEquals([], diff.right_only)

    def test_apply_patch_works_with_old_files_present_in_target(self):
        old_path = path.join('tests', 'test_files', 'old_version1')

        rmtree(self.temp_dir)
        copytree(old_path, self.temp_dir)

        delta_path = path.join('tests', 'test_files', 'patch1.xdelta.tgz')
        output = check_output(["./%s" % self.EXECUTABLE, "apply", self.temp_dir, delta_path, "--ignore-euid"] )

        new_path = path.join('tests', 'test_files', 'new_version1')
        diff = dircmp(self.temp_dir, new_path)

        self.assertEquals([], diff.diff_files)
        self.assertEquals([], diff.common_funny)
        self.assertEquals([], diff.left_only)
        self.assertEquals([], diff.right_only)

    def test_diff_works(self):
        # Implicit dependency on previous apply integration test
        old_path = path.join('tests', 'test_files', 'old_version1')
        new_path = path.join('tests', 'test_files', 'new_version1')
        generated_delta_path = path.join(self.temp_dir2, 'patch.xdelta')

        check_output(["./%s" % self.EXECUTABLE, "diff", old_path, new_path, generated_delta_path] )
        check_output(["./%s" % self.EXECUTABLE, "apply", old_path, generated_delta_path, self.temp_dir, "--ignore-euid"] )

        diff = dircmp(self.temp_dir, new_path)

        self.assertEquals([], diff.diff_files)
        self.assertEquals([], diff.common_funny)
        self.assertEquals([], diff.left_only)
        self.assertEquals([], diff.right_only)

    # Integration tests
    def test_version_is_correct(self):
        output = check_output(["./%s" % self.EXECUTABLE, '--version'],
                              stderr=STDOUT,
                              universal_newlines=True)
        self.assertEqual(output, "%s v0.1\n" % self.EXECUTABLE)

    def test_help_is_available(self):
        self.assertIsNotNone(check_output(["./%s" % self.EXECUTABLE, '-h']))
        self.assertIsNotNone(check_output(["./%s" % self.EXECUTABLE, '--help']))

    def test_debugging_is_available(self):
        output = check_output(["./%s" % self.EXECUTABLE, '--debug'])
        self.assertNotIn("unrecognized arguments", output)

    def test_help_is_printed_if_no_action_command(self):
        output = check_output(["./%s" % self.EXECUTABLE])
        self.assertIn("usage: ", output)

    def test_apply_is_allowed_as_action_command(self):
        try:
            check_output(["./%s" % self.EXECUTABLE, "apply"],
                         stderr=STDOUT)
        except CalledProcessError as e:
            self.assertIn("usage: ", e.output)
            self.assertNotIn("invalid choice: ", e.output)
        else: self.fail()

    def test_apply_usage_is_printed_if_not_enough_args(self):
        try:
            check_output(["./%s" % self.EXECUTABLE, "apply"],
                         stderr=STDOUT)
        except CalledProcessError as e:
            self.assertIn("the following arguments are required: ", e.output)
        else: self.fail()

    def test_apply_usage_is_not_printed_if_args_are_correct(self):
        old_path = path.join('tests', 'test_files', 'old_version1')
        delta_path = path.join('tests', 'test_files', 'patch1.xdelta.tgz')
        output = check_output(["./%s" % self.EXECUTABLE, "apply", old_path, delta_path, self.temp_dir, "--ignore-euid"] )
        self.assertNotIn("usage: ", output)

    def test_apply_usage_is_not_printed_if_args_are_correct2(self):
        old_path = path.join('tests', 'test_files', 'old_version1')

        rmtree(self.temp_dir)
        copytree(old_path, self.temp_dir)

        delta_path = path.join('tests', 'test_files', 'patch1.xdelta.tgz')
        output = check_output(["./%s" % self.EXECUTABLE, "apply", self.temp_dir, delta_path, "--ignore-euid"] )
        self.assertNotIn("usage: ", output)

    def test_diff_usage_is_printed_if_not_enough_args(self):
        try:
            check_output(["./%s" % self.EXECUTABLE, "diff"],
                         stderr=STDOUT)
        except CalledProcessError as e:
            self.assertIn("the following arguments are required: ", e.output)
        else: self.fail()

    def test_diff_is_allowed_as_action_command(self):
        try:
            check_output(["./%s" % self.EXECUTABLE, "diff"],
                         stderr=STDOUT)
        except CalledProcessError as e:
            self.assertIn("usage: ", e.output)
            self.assertNotIn("invalid choice: ", e.output)
        else: self.fail()

    def test_diff_usage_is_not_printed_if_args_are_correct(self):
        old_path = path.join('tests', 'test_files', 'old_version1')
        new_path = path.join('tests', 'test_files', 'new_version1')
        delta_path = path.join(self.temp_dir, 'foo.tgz')
        output = check_output(["./%s" % self.EXECUTABLE, "diff", old_path, new_path, delta_path] )
        self.assertNotIn("usage: ", output)

    def test_other_actions_are_not_allowed(self):
        try:
            check_output(["./%s" % self.EXECUTABLE, "foobar"],
                         stderr=STDOUT)
        except CalledProcessError as e:
            self.assertIn("usage: ", e.output)
            self.assertIn("invalid choice: ", e.output)
        else: self.fail()

    # Unit tests
    def test_run_calls_diff_with_correct_arguments_if_action_is_diff(self):
        args = patcher.AttributeDict()
        args.action = 'diff'
        args.old_dir = 'old'
        args.new_dir = 'new'
        args.patch_bundle = 'target'

        test_object = patcher.XDelta3DirPatcher(args)
        test_object.diff = Mock()

        test_object.run()

        test_object.diff.assert_called_once_with('old', 'new', 'target')

    def test_run_calls_apply_with_correct_arguments_if_action_is_apply(self):
        args = patcher.AttributeDict()
        args.action = 'apply'
        args.old_dir = 'old'
        args.patch_bundle = 'patch'
        args.ignore_euid = True
        args.target_dir = 'target'

        test_object = patcher.XDelta3DirPatcher(args)
        test_object.apply = Mock()

        test_object.run()

        test_object.apply.assert_called_once_with('old', 'patch', 'target')

    def test_run_calls_apply_with_correct_arguments_if_action_is_apply_and_no_target_specified(self):
        args = patcher.AttributeDict()
        args.action = 'apply'
        args.old_dir = 'old'
        args.patch_bundle = 'patch'
        args.ignore_euid = True
        args.target_dir = None

        test_object = patcher.XDelta3DirPatcher(args)
        test_object.apply = Mock()

        test_object.run()

        test_object.apply.assert_called_once_with('old', 'patch', 'old')

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

        test_class.apply("old", "patch", "target")

        test_class.run_command.assert_called_once_with(['xdelta3', '-f', '-d', '-s', 'old', 'patch', 'target'])

        test_class.run_command = original_run_command

    def test_xdelta_impl_apply_uses_correct_system_arguments_when_old_file_is_not_there(self):
        test_class = patcher.XDelta3Impl
        original_run_command = test_class.run_command
        test_class.run_command = Mock()

        test_class.apply(None, "patch", "target")

        test_class.run_command.assert_called_once_with(['xdelta3', '-f', '-d', 'patch', 'target'])

        test_class.run_command = original_run_command

