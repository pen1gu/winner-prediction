from server.app.crawler.fotmob import FotMobCrawler
from server.app.models import Player
import asyncio

from server.app.tasks.task import fetch_matches_by_team_id_task, fetch_team_overview_task

from server.utils.logger import get_logger

logger = get_logger(__name__)

async def main():

    team_id = 9825

    crawler = FotMobCrawler()

    await fetch_team_overview_task(team_id)

    await fetch_matches_by_team_id_task(team_id)
        
    

if __name__ == "__main__":
    asyncio.run(main())