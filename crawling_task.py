import asyncio

from server.app.tasks.task import (
    fetch_team_overview_task,
    fetch_matches_by_team_id_task,
    compute_all_player_ratings_task,
)


TEAM_ID = 9825


async def main() -> None:
    await fetch_team_overview_task(TEAM_ID)

    await fetch_matches_by_team_id_task(TEAM_ID)

    # await compute_all_player_ratings_task()

if __name__ == "__main__":
    asyncio.run(main())

