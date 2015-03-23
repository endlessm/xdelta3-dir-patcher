from filecmp import dircmp, cmpfiles
from os import path, readlink, walk
from subprocess import STDOUT, CalledProcessError, check_output

class TestHelpers(object):
    # Helpers
    @staticmethod
    def compare_trees(test_class, first, second):
        diff = dircmp(first, second)

        test_class.assertEquals([], diff.diff_files)

        # Need special code to compare links
        if len(diff.common_funny) > 0:
            for filename in diff.common_funny:
                first_file = path.join(first, filename)
                second_file = path.join(second, filename)
                if path.islink(first_file) and path.islink(second_file):
                    test_class.assertEquals(readlink(first_file),
                                      readlink(second_file))
                else:
                    test_class.fail('common_funny files was not empty!')

        test_class.assertEquals([], diff.left_only)
        test_class.assertEquals([], diff.right_only)

        files_to_compare = []
        for root, directories, files in walk(first):
            for cmp_file in files:
                files_to_compare.append(path.join(root, cmp_file))

        # Strip target file prefixes
        files_to_compare = [name[len(first)+1:] for name in files_to_compare]

        _, mismatch, error = cmpfiles(first, second, files_to_compare)

        test_class.assertEquals([], mismatch)

    @staticmethod
    def get_content(filename):
        content = None
        with open(filename, 'rb') as file_handle:
            content = file_handle.read()

        return content


    # This method should be almost the exact same as subprocess.check_output
    # except that it will also print any errors that it encounters during the
    # running of the program to help with debugging.
    @staticmethod
    def check_output2(command):
        try:
            print("Command:")
            print("****")
            print(' '.join(command))
            print("****")

            output = check_output(command, stderr = STDOUT,
                                  universal_newlines = True);
        except CalledProcessError as cpe:
            print("FAIL:", cpe.returncode, cpe.output)

            raise(cpe)
        else:
            print("Output:")
            print(output)

        return output
