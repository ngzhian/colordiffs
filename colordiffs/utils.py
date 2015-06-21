from pygments.lexer import Lexer
from pygments.token import Text


class NoneLexer(Lexer):
    def analyse_text(text):
        return 2

    def get_tokens_unprocessed(sef, text):
        return [(0, Text, text)]
