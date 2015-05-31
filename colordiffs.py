from itertools import dropwhile, takewhile
import re
import subprocess

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import TerminalFormatter
from pygments.lexers import guess_lexer, guess_lexer_for_filename

def read_chunks(lines):
    """
    >>> lines = [
    ... "prelude",
    ... "@@ -11,7 +11,8 @@ class Klass",
    ... " line 1",
    ... "+line 2",
    ... "@@ -11,7 +11,8 @@ class Klass",
    ... " line 1"]
    >>> read_chunks(lines)
    [['@@ -11,7 +11,8 @@ class Klass', ' line 1', '+line 2'], ['@@ -11,7 +11,8 @@ class Klass', ' line 1']]
    """
    started = False
    start_no = 0
    chunks = []
    for no, line in enumerate(lines):
        if line.startswith('@@'):
            if not started:
                started = True
                start_no = no
                continue
            chunk = lines[start_no:no]
            chunks.append(chunk)
            start_no = no
    chunk = lines[start_no:no+1]
    chunks.append(chunk)
    return chunks

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
        diff_line = self._spec[0]
        self.output_instructions = self._spec[1:]

        _, line_spec, _ = diff_line.split('@@')
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
        [' line 1a', '-line 2a', '+line 2b', '+line 3b']
        """
        results = []
        for instr in self.output_instructions:
            if instr[0] == ' ':
                results.append(' ' + self.a_hunk.get_current_line())
                self.b_hunk.get_current_line()  # for side effect
            if instr[0] == '-':
                results.append('-' + self.a_hunk.get_current_line())
            if instr[0] == '+':
                results.append('+' + self.b_hunk.get_current_line())
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
        file_contents_at_commit(file1, old_commit), file1)
    new_code = colorize(
        file_contents_at_commit(file2, new_commit), file2)
    return old_code, new_code

def colorize(code, filename=None):
    if filename is not None:
        lexer = guess_lexer_for_filename(filename, code)
    else:
        lexer = guess_lexer(code)
    formatter = TerminalFormatter()
    result = highlight(code, lexer, formatter)
    return result

def lines_of_output(output, start, end):
    return output[start-1:end+1]

def file_contents_at_commit(filename, commit):
    git_object = git_object_name(filename, commit)
    # if commit.startswith('f'):
    #     return 'print %s\nprint 1\n' % commit
    # if commit.startswith('3'):
    #     return 'print %s\nprint 1\nprint 2\n' % commit
    output = subprocess.check_output(['git', 'show', git_object])

def git_object_name(filename, commit):
    return '%(commit)s:%(filename)s' % {
        'commit': commit, 'filename': filename}

def grab_filename(diff):
    """
    >>> diff = ["diff --git a/.vimrc b/.vimrc", "index fa90906..313a9b4 100644"]
    >>> grab_filename(diff)
    ('.vimrc', '.vimrc')
    """
    filenames = diff[0]
    _, _, file1, file2 = filenames.split(' ')
    return file1[2:], file2[2:]

def grab_commits(diff):
    """
    >>> diff = ["diff --git a/.vimrc b/.vimrc", "index fa90906..313a9b4 100644"]
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
    dcs = []
    for chunk in read_chunks(diff):
        dcs.append(DiffChunk(chunk, a, b))

    for dc in dcs:
        for o in dc.output():
            print o

if __name__ == '__main__':
    f = open('test.diff')
    diff = f.readlines()
    main(diff)
    import doctest
    doctest.testmod()
