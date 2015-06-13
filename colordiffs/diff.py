import re
from .formats import green_bg, red_bg, discreet


__all__ = ['Diff']


class Diff():
    def __init__(self, diff, a, b):
        self.a = a
        self.b = b
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
            self.dcs.append(DiffChunk(chunk, self.a, self.b))

    def parse_commits(self):
        """
        >>> diff = [
        ... "diff --git a/.vimrc b/.vimrc",
        ... "index fa90906..313a9b4 100644",
        ... "--- a/.vimrc",
        ... "+++ b/.vimrc",
        ... "@@ -1,1 +1,2 @@ class Klass",
        ... " line 1",
        ... "+line 2",
        ... ]
        >>> d = Diff(diff, None, None)
        >>> d.commits
        ['fa90906', '313a9b4']
        """
        _, old, new, __ = re.split('\.\.| ', self.index)
        self.commits = [old, new]

    def grab_filename(self):
        """
        >>> diff = [
        ... "diff --git a/.vimrc b/.vimrc",
        ... "index fa90906..313a9b4 100644",
        ... "--- a/.vimrc",
        ... "+++ b/.vimrc",
        ... "@@ -1,1 +1,2 @@ class Klass",
        ... " line 1",
        ... "+line 2",
        ... ]
        >>> d = Diff(diff, None, None)
        >>> d.grab_filename()
        ('.vimrc', '.vimrc')
        """
        _, _, file1, file2 = self.header.split(' ')
        return file1[2:].strip(), file2[2:].strip()

    def read_chunks(self):
        """
        >>> diff = [
        ... "diff --git a/.vimrc b/.vimrc",
        ... "index fa90906..313a9b4 100644",
        ... "--- a/.vimrc",
        ... "+++ b/.vimrc",
        ... "@@ -1,1 +1,2 @@ class Klass",
        ... " line 1",
        ... "+line 2",
        ... "@@ -11,1 +11,1 @@ class Klass",
        ... "-line 1",
        ... "+line 2",
        ... ]
        >>> d = Diff(diff, None, None)
        >>> d.read_chunks()
        >>> d.chunks[0]
        ['@@ -1,1 +1,2 @@ class Klass', ' line 1', '+line 2']
        >>> d.chunks[1]
        ['@@ -11,1 +11,1 @@ class Klass', '-line 1', '+line 2']
        """
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

    def output(self):
        print(discreet(self.header))
        print(discreet(self.index))
        print(discreet(self.line_a))
        print(discreet(self.line_b))
        for dc in self.dcs:
            for o in dc.output():
                print(o)


class DiffChunk():
    def __init__(self, spec, a, b):
        """spec is a list of lines"""
        self._spec = spec
        self.a = a
        self.b = b
        self.parse_spec()

    def parse_spec(self):
        """
        >>> spec = [
        ... "@@ -11,7 +11,8 @@ class Klass",
        ... " line 1",
        ... "+line 2"]
        >>> dc = DiffChunk(spec, [], [])
        >>> dc.output_instructions
        [' line 1', '+line 2']
        >>> dc.a_hunk.start_line
        11
        >>> dc.a_hunk.num_lines
        7
        >>> dc.b_hunk.start_line
        11
        >>> dc.b_hunk.num_lines
        8
        """
        self.diff_line = self._spec[0]
        self.output_instructions = self._spec[1:]

        _, line_spec, _ = self.diff_line.split('@@')
        a_spec, b_spec = line_spec.strip().split(' ')

        a_start, a_more = a_spec.split(',')
        self.a_hunk = DiffHunk(a_start[1:], a_more, self.a)

        b_start, b_more = b_spec.split(',')
        self.b_hunk = DiffHunk(b_start[1:], b_more, self.b)

    def output(self):
        """
        >>> a = ["line 1a", "line 2a", ]
        >>> b = ["line 1a", "line 2b", "line 3b"]
        >>> spec = [
        ... "@@ -1,2 +1,3 @@ class Klass",
        ... " line 1a",
        ... "-line 2a",
        ... "+line 2b",
        ... "+line 3b"]
        >>> dc = DiffChunk(spec, a, b)
        >>> dc.output_instructions
        [' line 1a', '-line 2a', '+line 2b', '+line 3b']
        >>> dc.output()
        ['@@ -1,2 +1,3 @@ class Klass', ' line 1a', '-line 2a', '+line 2b', '+line 3b']
        """
        results = [discreet(self.diff_line)]
        for instr in self.output_instructions:
            if instr[0] == ' ':
                results.append(' ' + self.a_hunk.get_current_line())
                self.b_hunk.get_current_line()  # for side effect
            if instr[0] == '-':
                results.append(red_bg('-') + self.a_hunk.get_current_line())
            if instr[0] == '+':
                results.append(green_bg('+') + self.b_hunk.get_current_line())
        return results


class DiffHunk():
    def __init__(self, start_line, num_lines, colorized):
        self.start_line = int(start_line)
        self.curr_offset = -1
        self.num_lines = int(num_lines)
        self.colorized = colorized

    def get_current_line(self):
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
        return self.colorized[self.start_line + self.curr_offset - 1]