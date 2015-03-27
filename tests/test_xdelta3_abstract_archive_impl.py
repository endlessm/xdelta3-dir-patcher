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
from time import sleep

class TestXDelta3AbstractArchiveImp(unittest.TestCase):
    # Dashes are standard for exec scipts but not allowed for modules in Python. We
    # use the script standard since we will be running that file as a script most
    # often.
    patcher = imp.load_source("xdelta3-dir-patcher", "xdelta3-dir-patcher")

    class MockArchiveImpl(patcher.XDelta3AbstractArchiveImpl):
        def __init__(self, test_class):
            super().__init__()

        @property
        def members(self):
            return "abc"

    def setUp(self):
        self.test_class = self.patcher.XDelta3AbstractArchiveImpl

    def tearDown(self):
        pass

    def test_list_items_is_a_passthrough_to_members_property(self):
        test_object = self.MockArchiveImpl(self)
        self.assertEquals(test_object.list_items(), "abc")
