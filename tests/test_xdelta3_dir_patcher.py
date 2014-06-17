import unittest
from subprocess import CalledProcessError, check_output, STDOUT

# Dashes are standard for exec scipts but not allowed for modules in Python. We
# use the script standard since we will be running that file as a script most
# often.
__import__("xdelta3-dir-patcher")

class TestXDelta3DirPatcher(unittest.TestCase):
    EXECUTABLE="xdelta3-dir-patcher.py"

    # Integration tests
    def test_version_is_correct(self):
        output = check_output(["./%s" % self.EXECUTABLE, '--version'],
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
        output = check_output(["./%s" % self.EXECUTABLE, "apply", "foo", "bar", "baz"] )
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
        output = check_output(["./%s" % self.EXECUTABLE, "diff", "foo", "bar", "baz"] )
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
    def test_foo(self):
        pass
