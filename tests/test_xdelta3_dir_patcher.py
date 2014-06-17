import unittest
from subprocess import check_output

# Dashes are standard for exec scipts but not allowed for modules in Python. We
# use the script standard since we will be running that file as a script most
# often.
__import__("xdelta3-dir-patcher")

class TestXdelta3DirPatcher(unittest.TestCase):
    EXECUTABLE="xdelta3-dir-patcher.py"

    def test_version_is_correct(self):
        output = check_output(["./%s" % self.EXECUTABLE, '--version'])
        self.assertEqual(output, "%s v0.1\n" % self.EXECUTABLE)
