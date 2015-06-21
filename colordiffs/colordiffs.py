from itertools import takewhile
import os
import re
import subprocess

from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexer import Lexer
from pygments.lexers import guess_lexer, guess_lexer_for_filename
from pygments.token import Text
from pygments.util import ClassNotFound

from .output import output
from .diff import parse_diff_output
from .utils import NoneLexer


def colordiffs(diff):
    """Diff is a list of lines from a diff output"""
    old_commit, new_commit = diff.commits[0], diff.commits[1]
    file1, file2 = diff.file_a, diff.file_b

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

    # some fix for empty lines initially
    num_nl = len(list(takewhile(lambda c: c == '\n', iter(code))))
    result = num_nl * '\n' + highlight(code, lexer, formatter)
    result = result.split('\n')

    if result[-1] == '':
        return result[:-1]

    return result


def file_contents_at_commit(git_obj, filename):
    f = open(os.devnull, 'w')
    try:
        # this is probably HEAD, just use cat to get file contents
        output = subprocess.check_output(
            ['git', 'show', git_obj], stderr=f, universal_newlines=True)
    except subprocess.CalledProcessError:
        output = subprocess.check_output(
            ['cat', filename], universal_newlines=True)
    f.close()
    return output


def run(diff):
    for a_diff in parse_diff_output(diff):
        a, b = colordiffs(a_diff)
        output(a_diff, a, b)
