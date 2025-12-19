from server.app.crawler.fotmob import FotMobCrawler
from server.app.models import Team, Manager
from server.utils.logger import get_logger
from server.app.store.db_store import save_team_overview
logger = get_logger(__name__)


async def fetch_team_overview_task(team_id: int) -> dict:
    """
    팀 ID를 받아서 팀 정보와 감독 정보를 가져오는 task
    
    Args:
        team_id: FotMob 팀 ID
        
    Returns:
        dict: 팀 정보와 감독 정보
    """

    crawler = FotMobCrawler()

    response = await crawler.fetch_team_overview(team_id)
    
    team = await crawler.get_team_info_by_team_id(team_id, response)

    players = await crawler.get_players_info_by_team_id(team, response)

    manager = await crawler.get_manager_info_by_team_id(team, response)
    
    logger.info(f"Successfully fetched team and manager info for team_id: {team_id}")
    
    result = await save_team_overview(team, players, manager)

    logger.info(f"Successfully saved team overview for team_id: {team_id}")

    return result


async def fetch_matches_by_team_id_task(team_id: int) -> dict:
    # TODO: 매치 크롤링 시 중복 제거 반드시 필요
    pass

tasks = [
    {
        "fetch_team_overview": fetch_team_overview_task,
    },
]