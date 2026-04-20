import sys

from src.main import run_hybrid_interface, run_terminal


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_terminal(sys.argv[1:])
    else:
        run_hybrid_interface()