from server.app.crawler.fotmob import FotMobCrawler
from server.utils.logger import get_logger
from server.app.store.db_store import save
logger = get_logger(__name__)


async def fetch_team_overview_task(team_id: int) -> None:
    """
    description: 팀 ID를 받아서 팀 정보와 감독 정보를 가져오는 task
    
    Args:
        team_id: FotMob 팀 ID
    Returns:
        None
    """

    crawler = FotMobCrawler()

    response = await crawler.fetch_team_overview(team_id)
    
    team = await crawler.get_team_info_by_team_id(team_id, response)

    players = await crawler.get_players_info_by_team_id(team, response)

    manager = await crawler.get_manager_info_by_team_id(team, response)
    
    logger.info(f"Successfully fetched team and manager info for team_id: {team_id}")
    
    for store in [team, players, manager]:
        await save(store)

    logger.info(f"Successfully saved team overview for team_id: {team_id}")


async def fetch_matches_by_team_id_task(team_id: int) -> dict:
    """
    description: 팀 ID를 받아서 팀의 매치 정보를 가져오는 task
    
    Args:
        team_id: FotMob 팀 ID
    Returns:
        None
    """

    crawler = FotMobCrawler()

    response = await crawler.fetch_team_overview(team_id)

    match_logs = await crawler.get_match_logs_info_by_team_id(team_id, response)

    # TODO: 여기서 현재 있는 match 제거하고 남아있는 팀들을 자동으로 crawling할 수 있게 세팅을 하는게 좋지 않으띾?
    pass

tasks = [
    {
        "fetch_team_overview": fetch_team_overview_task,
        "fetch_matches_by_team_id": fetch_matches_by_team_id_task,
    },
]