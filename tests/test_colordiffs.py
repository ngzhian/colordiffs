import unittest

from colordiffs import colordiffs


def mock_file_contents(test_file):
    def mock(git_obj, filename):
        with open(test_file + '_' + git_obj) as f:
            diff = f.read()
        return diff
    return mock


class TestColorDdiffs(unittest.TestCase):
    def test_case_failingoutput_1(self):
        test_file = './failingoutput_1'

        with open(test_file) as f:
            diff = f.readlines()

        colordiffs.file_contents_at_commit = mock_file_contents(test_file)

        colordiffs.run(diff)

    def test_case_failingoutput_2(self):
        """test case from Jedi's code"""
        test_file = './failcase'
        with open(test_file) as f:
            diff = f.readlines()

        colordiffs.file_contents_at_commit = mock_file_contents(test_file)

        colordiffs.run(diff)

if __name__ == '__main__':
    unittest.main()
