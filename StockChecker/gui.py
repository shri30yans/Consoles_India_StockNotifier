from tkinter import *
import tkinter as tk

# from StockChecker.Notifications import countinous_stock
from StockChecker.ScrapperConfig import All_Products, All_Websites
from discord.ext import commands
import asyncio


class GUI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.root = Tk()
        self.root.title("StockChecker")
        self.root.iconbitmap("images/Consoles_India.ico")
        self.f = Frame(self.root)
        self.bot.loop.create_task(self.intialize())
        self.bot.loop.create_task(self.update())

    async def intialize(self):
        # The topmost left entry needs to be blank.
        self.f.configure(bg="black")
        e = Entry(
            self.f,
            width=40,
            fg="white",
            bg="black",
            font=("Arial", 16, "bold"),
            borderwidth=0,
            highlightthickness=0,
            justify="center",
        )
        e.grid(row=0, column=0)
        e.insert(END, " ")
        WebsiteDisplayNames = [x.display_name for x in All_Websites.values()]
        for column_number in range(len(WebsiteDisplayNames)):
            e = Entry(
                self.f,
                width=20,
                fg="white",
                bg="black",
                font=("Arial", 16, "bold"),
                borderwidth=0,
                highlightthickness=0,
                justify="center",
            )
            e.grid(row=0, column=column_number + 1, padx=4, pady=15)
            e.insert(END, WebsiteDisplayNames[column_number])

        ProductsDisplayNames = [
            product.display_name
            for product in All_Products.values()
            if not (product.hidden)
        ]
        for row_number in range(len(ProductsDisplayNames)):
            e = Entry(
                self.f,
                width=40,
                fg="white",
                bg="black",
                font=("Arial", 16, "bold"),
                borderwidth=0,
                highlightthickness=0,
            )
            e.grid(row=row_number + 1, column=0, padx=4, pady=15)
            e.insert(END, ProductsDisplayNames[row_number])

        for row in range(len(ProductsDisplayNames)):
            for column in range(len(WebsiteDisplayNames)):
                # label = Label(f,text=f"{row}/{column}", borderwidth=0, width=10)
                label = Label(
                    self.f,
                    fg="#C0C0C0",
                    bg="black",
                    text=f"━━",
                    borderwidth=0,
                    width=10,
                    highlightthickness=0,
                )
                label.configure(anchor="center")
                label.grid(
                    row=row + 1, column=column + 1, sticky="nsew", padx=4, pady=15
                )

        self.f.grid()

    async def update_values(self, product, website_name, value):
        Website_Class = All_Websites.get(website_name)
        Product_Class = All_Products.get(product)

        for x in self.f.grid_slaves():
            if type(x) is Entry:
                # x.get() returns the text of the Entry object

                # Get row number
                if Product_Class.display_name == x.get():
                    row = (x.grid_info()).get("row")

                # Get column number
                if Website_Class.display_name == x.get():
                    column = (x.grid_info()).get("column")

        if value is True:
            label = Label(
                self.f,
                text="In Stock",
                fg="#00FF00",
                bg="black",
                borderwidth=0,
                width=10,
                font=("Arial", 15, "bold"),
            )
            label.grid(row=row, column=column, sticky="nsew", padx=4, pady=8)
        elif value is False:
            label = Label(
                self.f,
                text="Out of Stock",
                fg="#FF0000",
                bg="black",
                borderwidth=0,
                width=10,
                font=("Arial", 15, "bold"),
            )
            label.grid(row=row, column=column, sticky="nsew", padx=4, pady=8)

        else:
            label = Label(
                self.f,
                text="Loading...",
                fg="#C0C0C0",
                bg="black",
                borderwidth=0,
                width=10,
                font=("Arial", 15, "bold"),
            )
            label.grid(row=row, column=column, sticky="nsew", padx=4, pady=8)

    async def update(self):
        while True:
            self.root.update()
            await asyncio.sleep(0)


def setup(bot):
    bot.add_cog(GUI(bot))
