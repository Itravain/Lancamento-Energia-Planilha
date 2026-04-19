import sys

from src.main import run, run_terminal


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_terminal(sys.argv[1:])
    else:
        run()