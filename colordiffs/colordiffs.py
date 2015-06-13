import os
import re
import subprocess

from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexer import Lexer
from pygments.lexers import guess_lexer, guess_lexer_for_filename
from pygments.token import Text
from pygments.util import ClassNotFound

from .diff import Diff


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
   :wa
    ... "diff --git a/.vimrc b/.vimrc",
    ... "index fa90906..313a9b4 100644"]
    >>> grab_commits(diff)
    ('fa90906', '313a9b4')
    """
    commits = diff[1]
    _, old, new, __ = re.split('\.\.| ', commits)
    return old, new


def run(diff):
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
