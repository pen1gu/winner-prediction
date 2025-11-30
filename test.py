from server.app.crawler.fotmob import FotMobCrawler
from server.app.models.player import Player
import asyncio

from server.utils.logger import get_logger

logger = get_logger(__name__)

async def main():

    team_id = 9825

    crawler = FotMobCrawler()
    response = await crawler.get_team(team_id)
    
    team = await crawler.get_team_info_by_team_id(team_id, response)
    players_info = await crawler.get_manager_info_by_team_id(team, response)
    print(players_info)

if __name__ == "__main__":
    asyncio.run(main())