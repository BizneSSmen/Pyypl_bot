import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiomysql import Pool

from DataBase import createPool
from config import loadConfig, Config
from Routers import routers

from Middlewares import DataBaseMiddleWare


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    config: Config = loadConfig("config.env")
    dbConfig = config.dataBase

    loop = asyncio.get_event_loop()

    pool: Pool = await createPool(user=dbConfig.login,
                                  password=dbConfig.password,
                                  address=dbConfig.address,
                                  port=dbConfig.port,
                                  db=dbConfig.dbName,
                                  loop=loop)

    userBot: Bot = Bot(config.tgBot.userToken, parse_mode="HTML")

    userDp: Dispatcher = Dispatcher(storage=MemoryStorage(), loop=loop)
    userDp.message.outer_middleware(DataBaseMiddleWare(pool=pool))
    userDp.callback_query.outer_middleware(DataBaseMiddleWare(pool=pool))

    userDp.include_routers(*routers)

    await userDp.start_polling(userBot)


if __name__ == "__main__":
    asyncio.run(main())
