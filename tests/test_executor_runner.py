import imp
import unittest

from mock import Mock
from time import sleep
from os import cpu_count

# Dashes are standard for exec scipts but not allowed for modules in Python. We
# use the script standard since we will be running that file as a script most
# often.
patcher = imp.load_source("xdelta3-dir-patcher", "xdelta3-dir-patcher")

class TestXDelta3DirPatcherZipImpl(unittest.TestCase):
    def setUp(self):
        self.test_class = patcher.ExecutorRunner

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
