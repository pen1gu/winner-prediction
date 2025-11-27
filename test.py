from server.app.crawler.fotmob import FotMobCrawler
from server.app.models.player import Player
import asyncio

from server.utils.logger import get_logger

logger = get_logger(__name__)

async def main():
    crawler = FotMobCrawler()
    players_info = await crawler.get_players_info_by_team_id(9825)

    print(players_info)

if __name__ == "__main__":
    asyncio.run(main())