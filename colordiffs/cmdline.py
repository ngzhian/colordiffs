import sys
from .colordiffs import run

def main():
    lines = [line for line in sys.stdin]
    if lines:
        run(lines)
