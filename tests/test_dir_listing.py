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

class TestDirListing(unittest.TestCase):
    # Dashes are standard for exec scipts but not allowed for modules in Python. We
    # use the script standard since we will be running that file as a script most
    # often.
    patcher = imp.load_source("xdelta3-dir-patcher", "xdelta3-dir-patcher")

    class FakeSubdir(patcher.DirListing):
        def __init__(self, version):
            super().__init__()

            self.version = version

    class FakeMember(object):
        def __init__(self, version):
            self.version = version

    def setUp(self):
        self.test_class = self.patcher.DirListing

    def tearDown(self):
        pass

    # Helpers
    def add_mock_file(self, test_object, version):
        data = self.FakeMember(version)
        link_target = "target%s" % version if (version % 2 == 0) else None
        return test_object.add_file("name%s" % version,
                                    data,
                                    1 + version,
                                    "username%s" % version,
                                    10 + version,
                                    "groupname%s" % version,
                                    100 + version,
                                    version % 2 == 0,
                                    link_target)

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
            self.assertEquals(file_obj.is_link, version % 2 == 0)
            if file_obj.is_link:
                file_obj.link_target = "target%s" % version
            self.assertEquals(file_obj.data.version, version)

            self.assertEquals(file_obj.is_file, True)
            self.assertEquals(file_obj.is_dir, False)

    # Tests
    def test_starts_with_no_directories_nor_files(self):
        test_object = self.test_class()

        self.assertEqual([], test_object.dirs)
        self.assertEqual([], test_object.files)

    def test_starts_with_some_predefined_props(self):
        test_object = self.test_class()

        self.assertEqual(None, test_object.name)
        self.assertEqual(False, test_object.is_link)
        self.assertEqual(None, test_object.data)

    def test_can_be_initialized_with_optional_name(self):
        test_object = self.test_class('foobar')

        self.assertEqual('foobar', test_object.name)

    def test_adding_files_works(self):
        test_object = self.test_class()

        self.add_mock_file(test_object, 1)
        self.add_mock_file(test_object, 2)

        self.verify_mock_files(test_object, [1, 2])

    def test_adding_file_returns_that_object(self):
        test_object = self.test_class()

        file_obj = self.add_mock_file(test_object, 1)
        self.assertEquals(file_obj, test_object.files[-1])

        file_obj = self.add_mock_file(test_object, 2)
        self.assertEquals(file_obj, test_object.files[-1])

    def test_adding_dirs_works(self):
        test_object = self.test_class()

        subdir1 = self.FakeSubdir(1)
        subdir2 = self.FakeSubdir(2)

        expected_subdirs = [ subdir1, subdir2 ]

        test_object.add_subdir(subdir1)
        test_object.add_subdir(subdir2)

        self.assertEqual(len(expected_subdirs), len(test_object.dirs))
        self.assertEqual(expected_subdirs, test_object.dirs)

    def test_set_object_attributes_works(self):
        test_object = self.test_class()

        data = self.FakeMember(999)

        test_object.set_metadata("name",
                                 data,
                                 1,
                                 "username",
                                 10,
                                 "groupname",
                                 100,
                                 True)

        self.assertEquals(test_object.name, "name")
        self.assertEquals(test_object.permissions, 1)
        self.assertEquals(test_object.uname, "username")
        self.assertEquals(test_object.uid, 10)
        self.assertEquals(test_object.gname, "groupname")
        self.assertEquals(test_object.gid, 100)
        self.assertEquals(test_object.is_link, True)
        self.assertEquals(test_object.data.version, 999)

        self.assertEquals(test_object.is_file, False)
        self.assertEquals(test_object.is_dir, True)
