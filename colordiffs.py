import os
import re
import subprocess

from pygments import highlight
from pygments.console import ansiformat
from pygments.console import codes, dark_colors, light_colors, esc
from pygments.formatters import TerminalFormatter
from pygments.lexer import Lexer
from pygments.lexers import guess_lexer, guess_lexer_for_filename
from pygments.token import Text
from pygments.util import ClassNotFound


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
                print o


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


def colordiffs(diff):
    """Diff is a list of lines from a diff output"""
    old_commit, new_commit = grab_commits(diff)
    file1, file2 = grab_filename(diff)

    old_code = colorize(
        file_contents_at_commit(old_commit, file1), file1)
    new_code = colorize(
        file_contents_at_commit(new_commit, file2), file2)
    return old_code, new_code


def colorize(code, filename=None):
    try:
        if filename is not None:
            lexer = guess_lexer_for_filename(filename, code)
        else:
            lexer = guess_lexer(code)
    except ClassNotFound:
        lexer = NoneLexer()

    formatter = TerminalFormatter()
    result = highlight(code, lexer, formatter)
    return result

class NoneLexer(Lexer):
    def analyse_text(text):
        return 1

    def get_tokens_unprocessed(sef, text):
        return [(0, Text, text)]



def file_contents_at_commit(git_obj, filename):
    # if obj.startswith('f'):
    #     return 'print %s\nprint 1\n' % obj
    # if obj.startswith('3'):
    #     return 'print %s\nprint 1\nprint 2\n' % obj
    f = open(os.devnull, 'w')
    try:
        # this is probably HEAD, just use cat to get file contents
        output = subprocess.check_output(
            ['git', 'show', git_obj], stderr=f)
    except subprocess.CalledProcessError:
        output = subprocess.check_output(
            ['cat', filename])
    f.close()
    return output


def grab_filename(diff):
    """
    >>> diff = [
    ... "diff --git a/.vimrc b/.vimrc",
    ... "index fa90906..313a9b4 100644"]
    >>> grab_filename(diff)
    ('.vimrc', '.vimrc')
    """
    filenames = diff[0]
    _, _, file1, file2 = filenames.split(' ')
    return file1[2:].strip(), file2[2:].strip()


def grab_commits(diff):
    """
    >>> diff = [
    ... "diff --git a/.vimrc b/.vimrc",
    ... "index fa90906..313a9b4 100644"]
    >>> grab_commits(diff)
    ('fa90906', '313a9b4')
    """
    commits = diff[1]
    _, old, new, __ = re.split('\.\.| ', commits)
    return old, new


def main(diff):
    diff = diff or [
        "diff --git a/.vimrc b/.vimrc",
        "index fa90906..313a9b4 100644",
        "--- a/.vimrc",
        "+++ b/.vimrc",
        "@@ -1,2 +1,3 @@ class Klass",
        " line 1a",
        "-line 2a",
        "+line 2b",
        "+line 3b",
    ]
    a, b = colordiffs(diff)
    a = a.split('\n')
    if a[-1] == '':
        a = a[:-1]
    b = b.split('\n')
    if b[-1] == '':
        b = b[:-1]
    a_diff = Diff(diff, a, b)
    a_diff.output()

def patch_codes():
    dark_bg = [s + '_bg' for s in dark_colors]
    light_bg = [s + '_bg' for s in light_colors]

    x = 40
    for d, l in zip(dark_bg, light_bg):
        codes[d] = esc + "%im" % x
        codes[l] = esc + "%i;01m" % x
        x += 1

# helpers to ansi escape text


def green_bg(text):
    return ansiformat('green', text)


def red_bg(text):
    return ansiformat('red', text)


def discreet(text):
    return ansiformat('faint', ansiformat('lightgray', text))


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        import doctest
        doctest.testmod()
    else:
        patch_codes()
        lines = [line for line in sys.stdin]
        if lines:
            main(lines)
