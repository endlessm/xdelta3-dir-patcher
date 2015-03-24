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

from mock import Mock

# Dashes are standard for exec scipts but not allowed for modules in Python. We
# use the script standard since we will be running that file as a script most
# often.
patcher = imp.load_source("xdelta3-dir-patcher", "xdelta3-dir-patcher")

class FakeMember(object):
    def __init__(self, version):
        self.version = version

class TestDirListing(unittest.TestCase):
    def setUp(self):
        self.test_class = patcher.DirListing

    def tearDown(self):
        pass

    # Helpers
    def add_mock_file(self, test_object, version):
        data = FakeMember(version)
        test_object.add_file("name%s" % version,
                             data,
                             1 + version,
                             "username%s" % version,
                             10 + version,
                             "groupname%s" % version,
                             100 + version)

    def verify_mock_files(self, test_object, versions):
        self.assertEqual(len(versions), len(test_object.files))

        for version in versions:
            file_obj = test_object.files[version - 1]

            self.assertEquals(file_obj.name, "name%s" % version)
            self.assertEquals(file_obj.permissions, 1 + version)
            self.assertEquals(file_obj.uname, "username%s" % version)
            self.assertEquals(file_obj.uid, 10 + version)
            self.assertEquals(file_obj.gname, "groupname%s" % version)
            self.assertEquals(file_obj.gid, 100 + version)
            self.assertEquals(file_obj.data.version, version)

    # Tests

    def test_starts_with_no_directories_nor_files(self):
        test_object = self.test_class()

        self.assertEqual([], test_object.dirs)
        self.assertEqual([], test_object.files)

    def test_adding_files_works(self):
        test_object = self.test_class()

        self.add_mock_file(test_object, 1)
        self.add_mock_file(test_object, 2)

        self.verify_mock_files(test_object, [1, 2])
