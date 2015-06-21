import unittest

from colordiffs import colordiffs


def mock_file_contents(test_file):
    def mock(git_obj, filename):
        if git_obj == '0000000':
            return ''
        with open(test_file + '_' + git_obj) as f:
            diff = f.read()
        return diff
    return mock


class TestColorDiffs(unittest.TestCase):
    def test_case_failingoutput_1(self):
        test_file = './failingoutput_1'

        with open(test_file) as f:
            diff = f.readlines()

        colordiffs.file_contents_at_commit = mock_file_contents(test_file)

        colordiffs.run(diff)

    def test_case_failcase(self):
        """test case from Jedi's code"""
        test_file = './failcase'
        with open(test_file) as f:
            diff = f.readlines()

        colordiffs.file_contents_at_commit = mock_file_contents(test_file)

        colordiffs.run(diff)

    def test_case_failcase_2(self):
        """Tests a diff that removes a file"""
        test_file = './failcase_2'
        with open(test_file) as f:
            diff = f.readlines()

        colordiffs.file_contents_at_commit = mock_file_contents(test_file)

        colordiffs.run(diff)

if __name__ == '__main__':
    unittest.main()
