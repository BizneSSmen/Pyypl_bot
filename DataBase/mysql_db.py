import aiomysql
from aiomysql import Pool


async def createPool(user: str, password: str, address: str, port: str, db: str, loop):
    return await aiomysql.create_pool(host=address,
                                      port=port,
                                      user=user,
                                      password=password,
                                      db=db,
                                      loop=loop,
                                      autocommit=True,
                                      cursorclass=aiomysql.DictCursor)


class Database:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def insertСlaim(self, claim: dict) -> int:
        sql = """
        INSERT INTO claims (
            operation_type, description, card_paid_from, card_awaiting_to,
            tel, status, sum_A, sum_B, exchange_applied_rate, fee, currency_A,
            currency_B
        )
        VALUES (
            %(_Claim__operationType)s, %(_Claim__description)s, %(_Claim__cardPaidFrom)s,
            %(_Claim__cardAwaitingTo)s, %(_Claim__phoneNumber)s, %(_Claim__status)s, %(_Claim__targetAmount)s,
            %(_Claim__finalAmount)s, %(_Claim__exchangeAppliedRate)s,
            %(_Claim__fee)s, %(_Claim__currencyB)s, %(_Claim__currencyA)s
        )
        """

        async with self.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                try:
                    await cursor.execute(sql, claim)
                    await connection.commit()
                    return cursor.lastrowid  # Возвращает ID новой записи
                except Exception as e:
                    print(f"Error executing SQL query: {e}")

    async def updateClaimById(self, claim_id: int, updates: dict):
        queries: list[str] = [f"UPDATE claims SET {field} WHERE id = %s" for field in [f'{key} = %s' for key in updates.keys()]]
        values = list(updates.values())
        resultQueries = list(zip(queries, list(zip(values, [claim_id]*len(values)))))

        async with self.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                for query in resultQueries:
                    try:
                        await cursor.execute(*query)
                        await connection.commit()
                    except Exception as e:
                        print(f"Error executing SQL query: {e}")
