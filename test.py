from server.app.crawler.fotmob import FotMobCrawler
from server.app.models import Player
import asyncio

from server.utils.logger import get_logger

logger = get_logger(__name__)

async def main():

    team_id = 4947174

    crawler = FotMobCrawler()
    response = await crawler.get_next_match_info_by_match_id(team_id)
    
    # team = await crawler.get_team_info_by_team_id(team_id, response)
    # players_info = await crawler.get_manager_info_by_team_id(team, response)
    # print(players_info)

    # result = await get_next_match_info_by_match_id(team_id)
    # print(result)

if __name__ == "__main__":
    asyncio.run(main())