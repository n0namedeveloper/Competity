import asyncio
import sys
import os

# Add the project root to sys.path so 'app' can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import AsyncSessionLocal
from app.services.collector_service import CollectorService

async def main():
    print("Starting manual data collection...")
    async with AsyncSessionLocal() as session:
        collector = CollectorService(session)
        result = await collector.collect_all()
        print("Collection finished:", result)

if __name__ == "__main__":
    asyncio.run(main())
