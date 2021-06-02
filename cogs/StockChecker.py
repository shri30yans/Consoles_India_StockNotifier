from cogs.Notifications import Notifications
import discord,random,asyncio,requests,time
from discord.ext import commands,tasks
from bs4 import BeautifulSoup
from lxml import etree
import config

class StockChecker(commands.Cog): 
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.startup())
        #self.amazon_link="https://www.amazon.in/dp/B08FV5GC28"
        self.amazon_link="https://www.amazon.in/PS4-Marvels-Spider-Man-Miles-Morales/dp/B08LFBM5JV/?_encoding=UTF8&pd_rd_w=IFOWl&pf_rd_p=ab4aa62e-ee61-4bc4-928a-fc54f74f1993&pf_rd_r=610RK1K5XJWWTGGNXM2F&pd_rd_r=fd7cd9e2-e3f0-4540-ab06-b2f375b0068e&pd_rd_wg=hU5Oz&ref_=pd_gw_ci_mcx_mr_hp_d"
        #self.flipkart_link="https://www.flipkart.com/sony-playstation-5-cfi-1008a01r-825-gb-astro-s-playroom/p/itma0201bdea62fa"
        self.flipkart_link="https://www.flipkart.com/infinity-harman-hardrock-410-200-w-bluetooth-home-theatre/p/itm972d6bc2f0744?pid=ACCGYNE5XYQNNNGB&lid=LSTACCGYNE5XYQNNNGBSYSDVX&marketplace=FLIPKART&store=0pm%2F0o7&srno=b_1_1&otracker=hp_omu_Super%2BSaver%2BDeals%2BOf%2BThe%2BDay_1_3.dealCard.OMU_2KGPXO96IJD9_3&otracker1=hp_omu_PINNED_neo%2Fmerchandising_Super%2BSaver%2BDeals%2BOf%2BThe%2BDay_NA_dealCard_cc_1_NA_view-all_3&fm=neo%2Fmerchandising&iid=en_MLmLzAPyh%2BcXYMbV028VkbcnlTiHriKSYFzSUxSzkzQU%2FJNZ6HdP7fm%2BWTiVHoGlswI8mD%2BYfsYhiPG2c6hdvA%3D%3D&ppt=browse&ppn=browse&ssid=q6luzltimo0000001622607770040"
    
    async def run_notifications(self,website_name):
        Notifications = self.bot.get_cog('Notifications')
        await Notifications.notify(website_name)

    
    
    async def startup(self): 
        await self.bot.wait_until_ready()        
        self.bot.loop.create_task(self.run_scrape_flipkart())
        self.bot.loop.create_task(self.run_scrape_amazon())

    async def run_scrape_flipkart(self):       
        while True:
            flipkart_status = await self.scrape_flipkart(self.flipkart_link)
            if flipkart_status == "In Stock":
                print("Flipkart",flipkart_status)
                await self.run_notifications(website_name="flipkart")
                await asyncio.sleep(2)
    
    async def run_scrape_amazon(self):       
        while True:
            amazon_status = await self.scrape_flipkart(self.flipkart_link)
            if amazon_status == "In Stock":
                print("Amazon",amazon_status)
                await self.run_notifications(website_name="amazon")
                await asyncio.sleep(5)


 

    amazon_link="https://www.amazon.in/dp/B08FV5GC28"
    flipkart_link="https://www.flipkart.com/sony-playstation-5-cfi-1008a01r-825-gb-astro-s-playroom/p/itma0201bdea62fa"
    #flipkart_link="https://www.flipkart.com/microsoft-xbox-series-x-1024-gb/p/itm63ff9bd504f27?pid=GMCFVPFCFDFGJHGG&lid=LSTGMCFVPFCFDFGJHGGLGCF4A&marketplace=FLIPKART&q=xbox+series+x&store=4rr%2Fx1m&srno=s_1_2&otracker=search&fm=SEARCH&iid=5ff68b60-da5b-42ef-88ac-78427c9cc7cc.GMCFVPFCFDFGJHGG.SEARCH&ppt=sp&ppn=sp&ssid=uko3bh0yqo0000001622607922665&qH=4bdad5bdc8d5c743"


    async def get_page_html(self,url):
        headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"}
        page = requests.get(url, headers=headers)
        #print(page.status_code)
        return page.content
    
    async def scrape_amazon(self,amazon_link):
        page_html = await self.get_page_html(amazon_link)
        soup = BeautifulSoup(page_html, 'html.parser')
        try:
            dom = etree.HTML(str(soup))
            stock=dom.xpath('//*[@id="availability"]/span')[0].text
        except:
            stock="Error"
        #print(stock)
        if "Currently unavailable." in stock or "We don't know when or if this item will be back in stock." in stock :
            status="Out of Stock"
        elif "In stock" in stock:
            status="In Stock"
        else:
            status=f"A different response has been generated: {stock}"
        return status

    async def scrape_flipkart(self,flipkart_link):
        page_html = await self.get_page_html(flipkart_link)
        soup = BeautifulSoup(page_html, 'html.parser')
        try:
            dom = etree.HTML(str(soup))
            stock=dom.xpath('//*[@id="container"]/div/div[3]/div[1]/div[2]/div[3]/div')[0].text
            add_to_cart_button=dom.xpath('//*[@id="container"]/div/div[3]/div[1]/div[1]/div[2]/div/ul/li[1]/button')
        except:
            print("Error")
    
        if stock is None and len(add_to_cart_button) !=0 :
            status="In Stock"

        elif "Sold Out" in stock or "Coming Soon" in stock :
            status="Out of Stock"

        else:
            status=f"A different response has been generated: {stock}"
        return status




def setup(bot):
    bot.add_cog(StockChecker(bot))