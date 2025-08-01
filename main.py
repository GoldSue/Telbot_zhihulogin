import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from handlers import register_handlers
from scheduler import setup_scheduler
from config import BOT_TOKEN

async def main():
    proxy_url = "http://127.0.0.1:7897"  # 你的代理地址和端口
    session = AiohttpSession(proxy=proxy_url)
    print("🕵️ 准备初始化 Bot")
    bot = Bot(token=BOT_TOKEN, session=session)

    print("🧱 初始化 Dispatcher")
    dp = Dispatcher()
    dp.include_router(register_handlers())

    print("📅 初始化调度器")
    setup_scheduler(bot)

    try:
        me = await bot.me()
        print(f"🤖 机器人用户名：{me.username}，ID：{me.id}")
    except Exception as e:
        print(f"❌ 获取机器人信息失败: {e}")

    try:
        print("✅ 启动轮询")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        print("✅ Bot 会话已关闭")

if __name__ == '__main__':
    asyncio.run(main())
