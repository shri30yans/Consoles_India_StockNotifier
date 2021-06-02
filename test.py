from cogs.Notifications import Notifications
import discord,random,asyncio,requests,time
from discord.ext import commands,tasks
from bs4 import BeautifulSoup
import lxml.html
import config
import links 
link="https://prepaidgamercard.com/product/sony-playstation-plus-12-month-membership-indian-psn-account/"


def get_page_html(url):
        headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"}
        page = requests.get(url, headers=headers)
        #print(page.status_code)
        return page.content

def scrape(link):
        while True:
            page_html = get_page_html(link)
            doc = lxml.html.fromstring(page_html)
            try:
                stock=doc.xpath('//*[@id="product-7990"]/div/div[1]/div/div[2]/form/button/text()')#[0].strip()
                print(stock)
            except:
                print("Error")
        
            if "Add to cart" in stock[0]:
                status="In Stock"

            elif len(stock) == 0:
                status="Out of Stock"

            else:
                status=f"A different response has been generated: {stock}"
                
            time.sleep(2)

scrape(link)