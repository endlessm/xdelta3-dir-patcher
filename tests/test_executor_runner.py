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
from multiprocessing import cpu_count

class TestExecutorRunner(unittest.TestCase):
    # Dashes are standard for exec scipts but not allowed for modules in Python. We
    # use the script standard since we will be running that file as a script most
    # often.
    patcher = imp.load_source("xdelta3-dir-patcher", "xdelta3-dir-patcher")

    def setUp(self):
        self.test_class = self.patcher.ExecutorRunner

    def tearDown(self):
        pass

    def test_all_tasks_are_excuted_with_params_passed_in(self):
        test_object = self.test_class()

        values_ran = []
        def task_method(number, letter):
            values_ran.append((number, letter))

        test_object.add_task(task_method, (1, 'a'))
        test_object.add_task(task_method, (2, 'b'))
        test_object.add_task(task_method, (3, 'c'))

        test_object.join_all()

        self.assertIn((1, 'a'), values_ran)
        self.assertIn((2, 'b'), values_ran)
        self.assertIn((3, 'c'), values_ran)

    def test_if_nothing_was_ran_dont_crash_on_time_calc(self):
        test_object = self.test_class()

        # Implicit test - no exception
        test_object.join_all()

    @unittest.skipIf(cpu_count() <= 3, \
                     'This test requires 3 or more virtal CPUs')
    def test_tasks_are_run_in_parallel(self):
        test_object = self.test_class()

        finish_order = []
        def task_method(number, letter):
            sleep(number)
            finish_order.append(number)

        test_object.add_task(task_method, (0.8,  'b'))
        test_object.add_task(task_method, (0.4, 'a'))
        test_object.add_task(task_method, (1.2, 'c'))

        test_object.join_all()

        self.assertEquals([0.4, 0.8, 1.2], finish_order)

    def test_after_join_all_tasks_cant_be_added(self):
        test_object = self.test_class()

        def task_method(number, letter):
            pass

        test_object.add_task(task_method, (1, 'a'))

        test_object.join_all()

        try:
            test_object.add_task(task_method, (1, 'a'))

            raise Exception()
        except RuntimeError as re:
            pass
        except Exception as e:
            self.fail('Unexpected exception thrown')

    def test_if_runner_fails_join_all_fails(self):
        test_object = self.test_class()

        def task_method(number, letter):
            sleep(1)

            if number == 9:
                raise RuntimeError('Big crash!')

        test_object.add_task(task_method, (1, 'a'))
        test_object.add_task(task_method, (9, 'b'))

        try:
            test_object.join_all()

            raise Exception()
        except RuntimeError as re:
            self.assertEquals(str(re), 'Big crash!')
        except Exception as e:
            self.fail('Unexpected exception thrown')
