from typing import Optional, List, Any
import asyncpg as acpg
import datetime
import math


class DatabaseHandler:
    def __init__(self, pool: acpg.Pool):
        self.pool = pool

    async def execute(self, query: str, *args):
        return await self.pool.execute(query, *args)

    async def fetchval(self, query: str, *args) -> Any:
        return await self.pool.fetchval(query, *args)

    async def fetchrow(self, query: str, *args) -> Optional[acpg.Record]:
        return await self.pool.fetchrow(query, *args)

    # Add user if not exist
    async def create_user_if_not_exist(self, user_id: int) -> None:
        await self.pool.execute(
            "INSERT INTO users (user_id) VALUES ($1) ON CONFLICT (user_id) DO NOTHING",
            user_id,
        )

    # Get user balance
    async def get_user_balance(self, user_id) -> List[acpg.Record]:
        await self.create_user_if_not_exist(user_id)
        async with self.pool.acquire() as conn:
            conn: acpg.Connection
            record = await conn.fetchrow(
                "SELECT points, daily_count FROM users WHERE user_id = $1", user_id
            )
            return record

    async def get_user_streak_count(self, user_id) -> int:
        await self.create_user_if_not_exist(user_id)

        query = "SELECT daily_count FROM users WHERE user_id = $1"
        return await self.pool.fetchval(query, user_id)

    # Add Points
    async def add_points(self, user_id: int, amount: int) -> int:
        await self.create_user_if_not_exist(user_id)

        new_balance = await self.pool.fetchval(
            "UPDATE users SET points = points + $2 WHERE user_id = $1 RETURNING points",
            user_id,
            amount,
        )
        return new_balance

    # Reduce Points
    async def reduce_points(self, user_id: int, amount: int) -> int:
        await self.create_user_if_not_exist(user_id)
        # check for avaiable points
        new_balance = await self.pool.fetchval(
            "UPDATE users SET points = points - $2 WHERE user_id = $1 RETURNING points",
            user_id,
            amount,
        )
        return new_balance

    # Process Claim
    async def process_daily_claim(
        self, user_id, daily_amount: int, interest_rate: float, cooldown: int
    ) -> tuple[bool, int, int, int, int]:
        """
        Returns
        -------
        tuple[bool, int, int, int, int]
            A 5-element tuple containing:
            1. bool: True if the bonus was successfully claimed, False otherwise.
            2. int: Today claim points.
            3. int: The user's new (or current) total points.
            4. int: The user's claim streak
            5. Optional[timedelta]: If the claim was unsuccessful (False), this is the
               time remaining until the user can claim again. If successful (True), this is None.
        """
        current_time = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        try:
            async with self.pool.acquire() as conn:
                conn: acpg.Connection
                await self.create_user_if_not_exist(user_id)

                claim_record = await conn.fetchrow(
                    "SELECT daily_count, last_daily FROM users WHERE user_id = $1",
                    user_id,
                )
                time_since_last_claim = current_time - claim_record["last_daily"]
                seconds_remaining = cooldown - time_since_last_claim.total_seconds()
                if seconds_remaining > 0:
                    return False, 0, 0, 0, seconds_remaining

                daily_bonus = round(
                    daily_amount
                    * math.pow((1 + interest_rate), claim_record["daily_count"])
                )

                new_balance = await conn.fetchval(
                    "UPDATE users SET points = points + $2, last_daily = $3, daily_count = daily_count + 1 WHERE user_id = $1 RETURNING points",
                    user_id,
                    daily_bonus,
                    current_time,
                )

                return True, daily_bonus, new_balance, claim_record["daily_count"], None
        except Exception as e:
            return False, 0, 0, 0, None

    # Transer Points From User To User
    async def transfer_point(
        self, src_user_id: int, end_user_id: int, amount: int
    ) -> tuple[bool, int]:
        try:
            async with self.pool.acquire() as conn:
                conn: acpg.Connection

                current_src_user_points = await conn.fetchval(
                    "SELECT points FROM users WHERE user_id = $1", src_user_id
                )
                if current_src_user_points < amount:
                    return True, 0
                async with conn.transaction():
                    await self.create_user_if_not_exist(end_user_id)
                    await self.pool.execute(
                        "UPDATE users SET points = points - $2 WHERE user_id = $1",
                        src_user_id,
                        amount,
                    )
                    new_balance = await self.pool.execute(
                        "UPDATE users SET points = points + $2 WHERE user_id = $1 RETURNING points",
                        end_user_id,
                        amount,
                    )
                return True, new_balance
        except Exception as e:
            print(f"transfer points error for {src_user_id}: {e}")
            return False, 0

    # Get All Memetics
    async def get_memetics(self) -> List[acpg.Record]:
        records = await self.pool.fetch("SELECT name, icon, description FROM memetics")
        return records

    async def reconnect(self) -> bool:
        pass
