import unittest

from colordiffs import colordiffs


def mock_file_contents(git_obj, filename):
    with open('./failingoutput_1' + '_' + git_obj) as f:
        diff = f.read()
    return diff


class TestColorDdiffs(unittest.TestCase):
    def test_case(self):
        with open('./failingoutput_1') as f:
            diff = f.readlines()

        colordiffs.file_contents_at_commit = mock_file_contents

        colordiffs.run(diff)

if __name__ == '__main__':
    unittest.main()
