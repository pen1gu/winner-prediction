from server.app.crawler.fotmob import FotMobCrawler
from server.app.store.db_query import get_already_fetched_player_ids, get_already_fetched_team_ids
from server.utils.logger import get_logger
from server.app.store.db_store import save
from server.app.store.db_query import get_player_by_id
from server.app.compute.player_rating import compute_player_rating
from server.app.models.players.player_rating import PlayerRating
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

    match_team_ids = []
    match_logs_ids = []
    for x in match_logs:
        if hasattr(x, "home_team_id") and hasattr(x, "away_team_id"):
            match_team_ids.extend([x.home_team_id, x.away_team_id])
        if hasattr(x, "id") and not hasattr(x, "match_id"): # MatchLogs
            match_logs_ids.append(x.id)
        elif hasattr(x, "match_id") and not hasattr(x, "id"): # MatchInfos/MatchDetails
            match_logs_ids.append(x.match_id)
    
    # 중복 제거
    match_logs_ids = list(set(match_logs_ids))

    already_fetched_team_ids = await get_already_fetched_team_ids()

    new_team_ids = set(match_team_ids) - set(already_fetched_team_ids)

    for team_id in new_team_ids:
        not_fetched_team_response = await crawler.fetch_team_overview(team_id)
        team = await crawler.get_team_info_by_team_id(team_id, not_fetched_team_response)
        await save(team)

        new_player_infos = await crawler.get_players_info_by_team_id(team, not_fetched_team_response)
        await save(new_player_infos)

    await save(match_logs)

    for match_log_id in match_logs_ids:
        match_details = await crawler.get_match_details_info_by_match_id(match_log_id)
        for detail in match_details:
            await save(detail)
    

    logger.info(f"Successfully fetched matches for team_id: {team_id}")


async def compute_player_rating_task(player_id: int) -> None:
    """
    description: 선수 ID를 받아서 선수의 rating을 계산하는 task
    
    Args:
        player_id: 선수 ID
    Returns:
        None
    """
    player = await get_player_by_id(player_id)
    if player is None:
        logger.warning(f"Player not found: {player_id}")
        return

    rating = await compute_player_rating(player)

    # rating은 별도 테이블(player_ratings)에 히스토리로 누적 저장한다.
    pr = PlayerRating(
        player_id=player_id,
        rating=rating,
        algorithm_version="v1",
    )
    await save(pr)
    logger.info(f"Saved player rating history. player_id={player_id} rating={rating}")


async def compute_all_player_ratings_task() -> None:
    """
    description: DB에 존재하는 모든 선수의 rating을 계산해서 저장하는 task
    """
    player_ids = await get_already_fetched_player_ids()
    if not player_ids:
        logger.warning("No players found in DB; skip computing ratings.")
        return

    saved = 0
    skipped = 0
    for pid in player_ids:
        try:
            await compute_player_rating_task(pid)
            saved += 1
        except Exception as e:
            skipped += 1
            logger.exception(f"Failed computing/saving rating. player_id={pid} err={e!r}")

    logger.info(f"Finished computing all player ratings. total={len(player_ids)} ok={saved} failed={skipped}")


tasks = [
    {
        "fetch_team_overview": fetch_team_overview_task,
        "fetch_matches_by_team_id": fetch_matches_by_team_id_task,
        "compute_all_player_ratings": compute_all_player_ratings_task,
    },
]