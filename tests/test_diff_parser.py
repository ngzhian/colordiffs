import unittest

from colordiffs.diff import (
    Diff, parse_diff_output, split_diffs, DiffChunk
)

SINGLE_DIFF = [
    "diff --git a/.vimrc b/.vimrc",
    "index fa90906..313a9b4 100644",
    "--- a/.vimrc",
    "+++ b/.vimrc",
    "@@ -1,1 +1,2 @@ class Klass",
    " line 1",
    "+line 2",
    "@@ -11,1 +11,1 @@ class Klass",
    "-line 1",
    "+line 2",
]

MULTIPLE_DIFF = [
    "diff --git a/.vimrc b/.vimrc",
    "index fa90906..313a9b4 100644",
    "--- a/.vimrc",
    "+++ b/.vimrc",
    "@@ -1,1 +1,2 @@ class Klass",
    " line 1",
    "+line 2",
    "diff --git a/.vimrc2 b/.vimrc2",
    "index fa90906..313a9b4 100644",
    "--- a/.vimrc2",
    "+++ b/.vimrc2",
    "@@ -1,1 +1,2 @@ class Klass",
    " line 1",
    "+line 2",
]


class TestColorDdiffs(unittest.TestCase):
    def test_can_parse_single_diff(self):
        diff = [
            "diff --git a/.vimrc b/.vimrc",
            "index fa90906..313a9b4 100644",
            "--- a/.vimrc",
            "+++ b/.vimrc",
            "@@ -1,1 +1,2 @@ class Klass",
            " line 1",
            "+line 2",
        ]
        d = Diff(diff)
        self.assertEqual(['fa90906', '313a9b4'], d.commits)

    def test_can_parse_multiple_diff(self):
        diffs = parse_diff_output(MULTIPLE_DIFF)
        self.assertTrue(2, len(diffs))

    def test_emit_diffs(self):
        diffs = list(split_diffs(SINGLE_DIFF))
        self.assertEqual(1, len(diffs))

        diffs = list(split_diffs(MULTIPLE_DIFF))
        self.assertEqual(2, len(diffs))


class TestDiff(unittest.TestCase):
    def test_commits(self):
        diff = Diff(SINGLE_DIFF)
        diff.parse_commits()
        self.assertEqual(['fa90906', '313a9b4'], diff.commits)

    def test_filename(self):
        diff = Diff(SINGLE_DIFF)
        self.assertEqual('.vimrc', diff.file_a)
        self.assertEqual('.vimrc', diff.file_b)

    def test_chunks(self):
        diff = Diff(SINGLE_DIFF)
        chunks = list(diff.parse_chunks())
        self.assertEqual(
            ['@@ -1,1 +1,2 @@ class Klass', ' line 1', '+line 2'],
            chunks[0].spec
        )
        self.assertEqual(
            ['@@ -11,1 +11,1 @@ class Klass', '-line 1', '+line 2'],
            chunks[1].spec
        )


class DiffChunkTestCase(unittest.TestCase):
    def test_parse(self):
        spec = [
            "@@ -11,7 +11,8 @@ class Klass",
            "-line 1",
            "+line 2",
        ]
        chunk = DiffChunk(spec)
        self.assertEqual(11, chunk.a_hunk.start_line)
        self.assertEqual(7, chunk.a_hunk.num_lines)
        self.assertEqual(11, chunk.b_hunk.start_line)
        self.assertEqual(8, chunk.b_hunk.num_lines)

    def test_output(self):
        a = ["line 1a", "line 2a", ]
        b = ["line 1a", "line 2b", "line 3b"]
        spec = [
        "@@ -1,2 +1,3 @@ class Klass",
        " line 1a",
        "-line 2a",
        "+line 2b",
        "+line 3b"]
        dc = DiffChunk(spec)
        self.assertEqual(
            [' line 1a', '-line 2a', '+line 2b', '+line 3b'],
            dc.output_instructions
        )


if __name__ == '__main__':
    unittest.main()
