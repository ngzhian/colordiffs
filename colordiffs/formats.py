from pygments.console import ansiformat


def green_bg(text):
    return ansiformat('green', text)


def red_bg(text):
    return ansiformat('red', text)


def discreet(text):
    return ansiformat('faint', ansiformat('lightgray', text))
