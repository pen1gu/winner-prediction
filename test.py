from server.app.crawler.player_info import PlayerInfoCrawler
import asyncio

async def main():
    crawler = PlayerInfoCrawler()
    try:
        await crawler.test_httpx()
    finally:
        await crawler.close()

if __name__ == "__main__":
    asyncio.run(main())