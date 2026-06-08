"""Entry point for the communication worker process.

Usage:
    python run_worker.py [--interval N]

Runs the async communication worker that polls the database for pending
communication batches and sends emails via SMTP.
"""

import argparse
import asyncio
import logging

from app.workers.communication_worker import run_worker

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="activia-trace communication worker"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=None,
        help="Poll interval in seconds (default: WORKER_POLL_INTERVAL from env)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    try:
        asyncio.run(run_worker(interval=args.interval))
    except KeyboardInterrupt:
        logging.getLogger("communication_worker").info("Worker terminated by user")
