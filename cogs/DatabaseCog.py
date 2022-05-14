import discord, json
from discord.ext import commands


class DatabaseFunctions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_user_info(self, user):
        async with self.bot.pool.acquire() as connection:
            async with connection.transaction():
                await self.has_account(user)
                user_account = await connection.fetchrow(
                    "SELECT * FROM info WHERE user_id=$1", user.id
                )
                user_account = dict(user_account)
                return user_account

    async def get_user_rep(self, user):
        async with self.bot.pool.acquire() as connection:
            async with connection.transaction():
                await self.has_account(user)
                user_account = await connection.fetchrow(
                    "SELECT rep FROM info WHERE user_id=$1", user.id
                )
                user_account = dict(user_account)
                rep = user_account.get("rep")
                return rep

    async def has_account(self, user):
        async def create_account(user):
            await connection.execute(
                "INSERT INTO info (user_id,rep) VALUES ($1,$2)", user.id, 0
            )

        if user.bot:
            return
        else:
            async with self.bot.pool.acquire() as connection:
                async with connection.transaction():
                    user_account = dict(
                        await connection.fetchrow(
                            "SELECT EXISTS(SELECT 1 FROM info WHERE user_id=$1)",
                            user.id,
                        )
                    )

                    if user_account["exists"] == False:
                        await create_account(user)
                    else:
                        return

    async def add_user_rep(self, user, amt):
        if amt == 0:
            return
        elif user.bot:
            return
        else:
            await self.has_account(user)
            async with self.bot.pool.acquire() as connection:
                async with connection.transaction():
                    await connection.execute(
                        "UPDATE info SET rep = rep + $1 WHERE user_id=$2", amt, user.id
                    )

    async def set_user_rep(self, user, amt):
        if user.bot:
            return
        else:
            await self.has_account(user)
            async with self.bot.pool.acquire() as connection:
                async with connection.transaction():
                    await connection.execute(
                        "UPDATE info SET rep = $1 WHERE user_id=$2", amt, user.id
                    )

def setup(bot):
    bot.add_cog(DatabaseFunctions(bot))
