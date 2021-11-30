import discord
from discord.ext import commands
import config
import datetime

colourlist = config.embed_colours


class Tags(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.launch_time = datetime.datetime.utcnow()

    @commands.command(name="Playstation", aliases=["ps5 links","PS5","PS5 DE"], help="Shows all PS5 links")
    async def ps5links(self, ctx):
        embed = discord.Embed(title="PS5 Links")
        embed.add_field(
            name="ShopatSC",
            value='[Physical](https://shopatsc.com/products/playstation-5-console/ "Physical edition")\n[Digital](https://shopatsc.com/collections/playstation-5/products/playstation5-digital-edition/ "Digital edition")',
        )
        embed.add_field(
            name="Amazon",
            value='[Physical]( https://www.amazon.in/dp/B08FV5GC28/ "Physical edition")\n[Digital](https://www.amazon.in/Sony-CFI-1008B01R-PlayStation-Digital-Edition/dp/B08FVRQ7BZ/ "Digital edition")',
        )
        embed.add_field(
            name="Flipkart",
            value='[Physical](https://www.flipkart.com/sony-playstation-5-cfi-1008a01r-825-gb-astro-s-playroom/p/itma0201bdea62fa/ "Physical edition")\n[Digital](https://www.flipkart.com/sony-playstation-5-cfi-1008b01r-825-gb-astro-s-playroom/p/itm8bf74f8d0b890?/ "Digital edition")',
        )
        embed.add_field(
            name="Croma",
            value='[Physical](https://www.croma.com/sony-playstation-5-825gb-ssd-cfi-1008a01r-white-/p/231643/ "Physical edition")\n[Digital](https://www.croma.com/sony-playstation-5-digital-edition-825gb-ssd-cfi-1008b01r-white-/p/231644/ "Digital edition")',
        )
        embed.add_field(
            name="Vijay Sales",
            value='[Physical](https://ps5.vijaysales.com/Sony-PS5-Console.html "Physical edition")\n[Digital](https://ps5.vijaysales.com/Sony-PS5-Console-Digital.html "Digital edition")',
        )
        embed.add_field(
            name="Reliance Digital",
            value='[Physical](https://www.reliancedigital.in/sony-playstation-5-console/p/491936180 "Physical edition")\n[Digital](https://www.reliancedigital.in/sony-playstation-5-console/p/491936181 "Digital edition")',
        )
        embed.add_field(
            name="PPGC",
            value='[Physical](https://prepaidgamercard.com/product/playstation-5-console-ps5/ "Physical edition")\n[Digital](https://prepaidgamercard.com/product/playstation-5-digital-edition-ps5/ "Digital edition")',
        )
        embed.add_field(
            name="Games the Shop",
            value='[Physical](https://www.gamestheshop.com/PlayStation-5-Console/5111/ "Physical edition")\n[Digital]( https://www.gamestheshop.com/PlayStation-5-Digital-Edition/5112/ "Digital edition")',
        )
        embed.add_field(
            name="Gameloot",
            value='[Physical](https://gameloot.in/shop/sony-playstation-5/ "Physical edition")\n[Digital]( https://gameloot.in/shop/sony-playstation-5-digital-edition// "Digital edition")',
        )
        embed.set_footer(
            icon_url=ctx.author.avatar_url,
            text=f"Requested by {ctx.message.author} • {self.bot.user.name}",
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="Xbox", aliases=["ps5 links"], help="Shows all PS5 links")
    async def ps5links(self, ctx):
        embed = discord.Embed(title="PS5 Links")
        embed.add_field(
            name="Amazon",
            value='[Xbox Series X](https://www.amazon.in/Xbox-Series-X/dp/B08J7QX1N1 "Xbox Series X")\n[Xbox Series S](https://www.amazon.in/Xbox-Series-S/dp/B08J89D6BW/ "Xbox Series S")',
        )
        embed.add_field(
            name="Flipkart",
            value='[Xbox Series X](https://www.flipkart.com/microsoft-xbox-series-x-1024-gb/p/itm63ff9bd504f27 "Xbox Series X")\n[Xbox Series S](https://www.flipkart.com/microsoft-xbox-series-s-512-gb/p/itm13c51f9047da8 "Xbox Series S")',
        )
        embed.add_field(
            name="Croma",
            value='[Physical](https://www.croma.com/sony-playstation-5-825gb-ssd-cfi-1008a01r-white-/p/231643/ "Physical edition")\n[Digital](https://www.croma.com/sony-playstation-5-digital-edition-825gb-ssd-cfi-1008b01r-white-/p/231644/ "Digital edition")',
        )
        embed.add_field(
            name="Vijay Sales",
            value='[Physical](https://ps5.vijaysales.com/Sony-PS5-Console.html "Physical edition")\n[Digital](https://ps5.vijaysales.com/Sony-PS5-Console-Digital.html "Digital edition")',
        )
        embed.add_field(
            name="Reliance Digital",
            value='[Physical](https://www.reliancedigital.in/sony-playstation-5-console/p/491936180 "Physical edition")\n[Digital](https://www.reliancedigital.in/sony-playstation-5-console/p/491936181 "Digital edition")',
        )
        embed.add_field(
            name="PPGC",
            value='[Physical](https://prepaidgamercard.com/product/playstation-5-console-ps5/ "Physical edition")\n[Digital](https://prepaidgamercard.com/product/playstation-5-digital-edition-ps5/ "Digital edition")',
        )
        embed.add_field(
            name="Games the Shop",
            value='[Physical](https://www.gamestheshop.com/PlayStation-5-Console/5111/ "Physical edition")\n[Digital]( https://www.gamestheshop.com/PlayStation-5-Digital-Edition/5112/ "Digital edition")',
        )
        embed.add_field(
            name="Gameloot",
            value='[Physical](https://gameloot.in/shop/sony-playstation-5/ "Physical edition")\n[Digital]( https://gameloot.in/shop/sony-playstation-5-digital-edition// "Digital edition")',
        )
        embed.set_footer(
            icon_url=ctx.author.avatar_url,
            text=f"Requested by {ctx.message.author} • {self.bot.user.name}",
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Tags(bot))
