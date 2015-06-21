import re
from .formats import green_bg, red_bg, discreet


__all__ = ['Diff']


def parse_diff_output(text):
    diffs = [Diff(d) for d in split_diffs(text)]
    return diffs


def split_diffs(text):
    """Split up a diff output into an interator of diffs"""
    arr = []
    for t in text:
        if t.startswith('diff') and len(arr) != 0:
            yield arr
            arr = [t]
        else:
            arr.append(t)
    yield arr


class Diff():
    def __init__(self, diff):
        self.diff = diff
        self.commits = []
        self.chunks = []
        self.parse_diff()

    def parse_diff(self):
        self.header = self.diff[0].strip()
        index = self.diff[1].strip()
        if index.startswith('index'):
            self.index = index
            self.line_a = self.diff[2].strip()
            self.line_b = self.diff[3].strip()
            self.spec = self.diff[4:]
        else:
            self.file_mode = self.diff[1].strip()
            self.index = self.diff[2].strip()
            self.line_a = self.diff[3].strip()
            self.line_b = self.diff[4].strip()
            self.spec = self.diff[5:]

        self.commits = self.parse_commits()
        self.file_a, self.file_b = self.parse_filenames()
        self.dcs = [DiffChunk(c) for c in self.parse_chunks()]

    def parse_commits(self):
        splits = re.split('\.\.| ', self.index)
        if len(splits) == 3:
            _, old, new = splits
        else:
            _, old, new, _ = splits
        return [old, new]

    def parse_filenames(self):
        _, _, file1, file2 = self.header.split(' ')
        return file1[2:].strip(), file2[2:].strip()

    def parse_chunks(self):
        return list(self.iter_chunks())

    def iter_chunks(self):
        part = []
        for no, line in enumerate(self.spec):
            if line.startswith('@@') and len(part) != 0:
                yield part
                part = [line]
            else:
                part.append(line)
        yield part


class DiffChunk():
    def __init__(self, spec):
        """spec is a list of lines"""
        self._spec = spec
        self.parse_spec()

    def parse_spec(self):
        self.diff_line = self._spec[0]
        self.output_instructions = self._spec[1:]

        _, line_spec, _ = self.diff_line.split('@@')
        a_spec, b_spec = line_spec.strip().split(' ')

        a_start, a_more = a_spec.split(',')
        self.a_hunk = DiffHunk(a_start[1:], a_more)

        b_start, b_more = b_spec.split(',')
        self.b_hunk = DiffHunk(b_start[1:], b_more)


class DiffHunk():
    def __init__(self, start_line, num_lines):
        self.start_line = int(start_line)
        self.curr_offset = -1
        self.num_lines = int(num_lines)

    def get_current_line(self, colorized):
        """
        >>> dh = DiffHunk(1, 3, ['a', 'b', 'c'])
        >>> dh.get_current_line()
        'a'
        >>> dh.get_current_line()
        'b'
        >>> dh.get_current_line()
        'c'
        """
        if self.curr_offset >= self.num_lines:
            raise Exception()
        self.curr_offset += 1
        # line numbers are 1-based, however indexes are 0-based
        return colorized[self.start_line + self.curr_offset - 1]
