"""BabelDOC WebUI - A modern web UI for BabelDOC PDF translation tool."""

import logging
import sys
import multiprocessing as mp

from ui.app import run


def main():
    """Main entry point."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Suppress noisy loggers
    for logger_name in ["httpx", "httpcore", "openai", "pdfminer"]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    run()


if __name__ == "__main__":
    # Set multiprocessing start method
    if sys.platform == "darwin" or sys.platform == "win32":
        mp.set_start_method("spawn", force=True)
    else:
        mp.set_start_method("forkserver", force=True)

    main()
