from aiogram import Router, types, F
from db import get_latest_news, get_latest_movies, search_content

router = Router()

@router.message(F.text == "/start")
async def cmd_start(message: types.Message):
    await message.answer("👋 欢迎使用资讯机器人！\n\n你可以使用以下命令：\n/news 获取新闻\n/movie 获取电影\n/search 关键词")

@router.message(F.text == "/news")
async def cmd_news(message: types.Message):
    news = get_latest_news()
    text = "\n\n".join([f"📰 {n['title']}\n🔗 {n['url']}" for n in news]) or "暂无新闻数据"
    await message.answer(text)

@router.message(F.text == "/movie")
async def cmd_movie(message: types.Message):
    movie = get_latest_movies()  # 单条字典
    text = (
        f'🎬 <b>{movie["title"]}</b> ({movie["year"]})\n'
        f'豆瓣评分: {movie.get("douban_score", "暂无")}, IMDb评分: {movie.get("imdb_score", "暂无")}\n'
        f'<i>{movie.get("intro", "暂无简介")}</i>'
    )
    await message.answer(text, parse_mode="HTML")

@router.message(F.text.startswith("/search"))
async def cmd_search(message: types.Message):
    keyword = message.text.replace("/search", "").strip()
    if not keyword:
        await message.answer("请输入关键词，例如：/search 星际穿越")
        return
    results = search_content(keyword)
    text = "\n\n".join([f"{r['type']} - {r['title']}\n🔗 {r['url']}" if r['url'] else f"{r['type']} - {r['title']}" for r in results]) or "未找到相关内容"
    await message.answer(text)

def register_handlers():
    return router
