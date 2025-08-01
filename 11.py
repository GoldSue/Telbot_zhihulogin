from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from aiohttp_socks import ProxyConnector

proxy_url = "socks5://127.0.0.1:1080"  # 修改为你的 SOCKS5 代理地址和端口
connector = ProxyConnector.from_url(proxy_url)
session = AiohttpSession(connector=connector)

bot = Bot(token="8036873972:AAGOU80L1ut1GTsHFdBwxveOD6vIF-C5UQM", session=session)
