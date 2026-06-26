"""Entry point untuk Pawnia Telegram Bot."""
import asyncio
import logging
import os
import sys

# Pastikan path src ada
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ekosistem_satwa.telegram import main

if __name__ == "__main__":
    asyncio.run(main())
