import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from db import get_latest_news, get_latest_movies

SUBSCRIBED_USERS = [987654321]  # 实际使用时改成你的用户ID列表

scheduler = AsyncIOScheduler()

def setup_scheduler(bot):
    async def push_news():
        news = get_latest_news()
        if news:
            text = "\n\n".join([f"📰 {n['title']}\n🔗 {n['url']}" for n in news])
            for uid in SUBSCRIBED_USERS:
                try:
                    await bot.send_message(uid, f"📢 每日新闻推荐\n\n{text}")
                except Exception as e:
                    print(f"发送新闻给 {uid} 失败: {e}")

    async def push_movies():
        movie = get_latest_movies()  # 单条字典
        if movie:
            text = (
                f'🎬 <b>{movie["title"]}</b> ({movie["year"]})\n'
                f'豆瓣评分: {movie.get("douban_score", "暂无")}, IMDb评分: {movie.get("imdb_score", "暂无")}\n'
                f'<i>{movie.get("intro", "暂无简介")}</i>\n'
                f'<a href="{movie.get("url", "")}">查看详情</a>'
            )
            for uid in SUBSCRIBED_USERS:
                try:
                    await bot.send_message(uid, f"🎬 每日电影推荐\n\n{text}", parse_mode="HTML")
                except Exception as e:
                    print(f"发送电影给 {uid} 失败: {e}")

    # APScheduler 调用异步函数时，包装成任务
    scheduler.add_job(lambda: asyncio.create_task(push_news()), "cron", hour=9, minute=0)
    scheduler.add_job(lambda: asyncio.create_task(push_movies()), "cron", hour=18, minute=24)
    scheduler.start()
