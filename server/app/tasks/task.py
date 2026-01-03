from server.app.crawler.fotmob import FotMobCrawler
from server.app.store.db_query import get_already_fetched_team_ids
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
    
    for element in [team, players, manager]:
        await save(element)

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

    # TODO: 여기서 현재 있는 match 제거하고 남아있는 팀들을 자동으로 crawling할 수 있게 세팅을 하는게 좋지 않을까?

    match_team_ids = []
    for x in match_logs:
        match_team_ids.extend([x.home_team_id, x.away_team_id])

    already_fetched_team_ids = await get_already_fetched_team_ids()

    new_team_ids = set(match_team_ids) - set(already_fetched_team_ids)

    for team_id in new_team_ids:
        not_fetched_team_response = await crawler.fetch_team_overview(team_id)
        team = await crawler.get_team_info_by_team_id(team_id, not_fetched_team_response)
        await save(team)

    await save(match_logs)

    logger.info(f"Successfully fetched matches for team_id: {team_id}")


tasks = [
    {
        "fetch_team_overview": fetch_team_overview_task,
        "fetch_matches_by_team_id": fetch_matches_by_team_id_task,
    },
]