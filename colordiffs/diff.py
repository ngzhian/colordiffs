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
        self.index = self.diff[1].strip()
        self.line_a = self.diff[2].strip()
        self.line_b = self.diff[3].strip()

        self.spec = self.diff[4:]

        self.parse_commits()
        self.grab_filename()
        self.read_chunks()

        self.dcs = []
        for chunk in self.chunks:
            self.dcs.append(DiffChunk(chunk))

    def parse_commits(self):
        _, old, new, __ = re.split('\.\.| ', self.index)
        self.commits = [old, new]

    def grab_filename(self):
        _, _, file1, file2 = self.header.split(' ')
        return file1[2:].strip(), file2[2:].strip()

    def read_chunks(self):
        started = False
        start_no = 0
        chunks = []
        for no, line in enumerate(self.spec):
            if line.startswith('@@'):
                if not started:
                    started = True
                    start_no = no
                    continue
                chunk = self.spec[start_no:no]
                chunks.append(chunk)
                start_no = no
        chunk = self.spec[start_no:]
        chunks.append(chunk)
        self.chunks = chunks

    def output(self, colorized_a, colorized_b):
        print(discreet(self.header))
        print(discreet(self.index))
        print(discreet(self.line_a))
        print(discreet(self.line_b))
        for dc in self.dcs:
            for o in dc.output(colorized_a, colorized_b):
                print(o)


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

    def output(self, colorized_a, colorized_b):
        results = [discreet(self.diff_line)]
        for instr in self.output_instructions:
            if instr[0] == ' ':
                results.append(' ' + self.a_hunk.get_current_line(colorized_a))
                self.b_hunk.get_current_line(colorized_b)  # for side effect
            if instr[0] == '-':
                results.append(red_bg('-') + self.a_hunk.get_current_line(colorized_a))
            if instr[0] == '+':
                results.append(green_bg('+') + self.b_hunk.get_current_line(colorized_b))
        return results


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
