from filecmp import dircmp, cmpfiles
from os import path, readlink, walk

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

