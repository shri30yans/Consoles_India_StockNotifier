import requests,time,random
import lxml.html

# How the bot checks for Stock availability?
# Instead of using selenium to replicate a browser experience it uses the requests library to fetch the HTML code of a URL. The Bot then searches the HTML code and looks for certain keywords in a specified location.

# Keyword Logic:
# Amazon: Amazon has a seperate divison in it's HTML page called Availabilty which allows me to check if a product is "Currently unavailable." or "In Stock"
# Flipkart: Flipkart has a seperate element to display Out of Stock. In case the product is available that element gives no value. The bot checks if that element is not displayed and double checks if the Add to Cart Button Exists.
# Games the Shop: Games the Shop shows the Add to Cart Button when the product is available.
# Prepaid Gamer Card: Prepaid Gamer Card shows the Add to Cart Button when the product is available.
# Note: Direct links to Sony Center, Reliance Digital and Vijay Sales are down. Croma requires Pin Code which is currently not possible to implement with Requests library.

# Issues:
# 1) I wrote the Scraping code in one day and as a result it isn't very efficient or trustworthy since it hasn't been tested extensively.
# 2) Amazon errors out or gives false information by blocking requests due to which the HTML page cannot be loaded.
# 3) Flipkart often redirects requests to random pages resulting in errors.

#Change the links to other products to test it out here        
# All_Websites={
#     "flipkart":"https://www.flipkart.com/sony-playstation-5-cfi-1008a01r-825-gb-astro-s-playroom/p/itma0201bdea62fa",
#     "amazon":"https://www.amazon.in/dp/B08FV5GC28",
#     "games_the_shop":"https://www.gamestheshop.com/PlayStation-5-Console/5111",
#     "ppgc":"https://prepaidgamercard.com/product/playstation-5-console-ps5/",}
All_Websites={
    "flipkart":"https://www.flipkart.com/demon-s-souls/p/itmdnayzmhdehghu?pid=GAMFYTWBYAQJSKYB&lid=LSTGAMFYTWBYAQJSKYBHKUMXO&marketplace=FLIPKART&store=4rr&srno=b_1_2&otracker=clp_banner_1_2.banner.BANNER_gaming-store_2GSQZNPR3D52&fm=neo%2Fmerchandising&iid=a1fc4bdc-c7bf-41aa-bd6a-fd4ea242ba2c.GAMFYTWBYAQJSKYB.SEARCH&ppt=clp&ppn=gaming-store&ssid=546zyh1ua80000001622964859694",
    "amazon":"https://www.amazon.in/PS5-RATCHET-CLANK-RIFT-APART/dp/B08WK5T3HY/ref=sr_1_1?crid=3ATMVHS5NX4PJ&dchild=1&keywords=rachet+and+clank&qid=1622949015&sprefix=rachet+and%2Caps%2C293&sr=8-1",
    "games_the_shop":"https://www.gamestheshop.com/PlayStation-5-Console/5111",
    "ppgc":"https://prepaidgamercard.com/product/playstation-5-console-ps5/",
    "shopatsc":"https://prepaidgamercard.com/product/playstation-5-console-ps5/",}

def run_notifications(website_name):
    print(f"Notification Alert! This product is in stock at {website_name}")

def startup(site):  
    if site == "flipkart" :
        scrape_flipkart(flipkart_link=All_Websites["flipkart"])
    elif site == "amazon" :
        scrape_amazon(amazon_link=All_Websites["amazon"])   
    elif site == "gts" :
        scrape_games_the_shop(games_the_shop_link=All_Websites["games_the_shop"])
    elif site == "ppgc" :
        scrape_ppgc(ppgc_link=All_Websites["ppgc"])
    elif site == "shopatsc" :
        scrape_shopatsc(shopatsc_link=All_Websites["shopatsc"])
    else:
        print("Unknown site")
        

def get_page_html(url,headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"}):
    page = requests.get(url, headers=headers)
    return page.content,page.status_code
    
def scrape_amazon(amazon_link):
    while True:
        page_html = str(get_page_html(amazon_link))
        doc = lxml.html.fromstring(page_html)
        try:
            stock=doc.xpath('//*[@id="availability"]/span')[0].text
            add_to_cart_button=doc.xpath('//*[@id="add-to-cart-button"]')
            all_buying_options=doc.xpath('//*[@id="buybox-see-all-buying-choices"]/span/a')
            pre_order_button=doc.xpath('//*[@id="buy-now-button"]')
        except:
            stock="Amazon Error"
        #print(stock)
        print(add_to_cart_button)
        print(all_buying_options)
        print(pre_order_button)
        
        if "Currently unavailable." in stock or "We don't know when or if this item will be back in stock." in stock :
            status="Out of Stock"
        
        elif "In stock" in stock:
            status="In Stock"
            run_notifications(website_name="amazon")
       
        elif "This item will be released on" in stock:
            status="In Stock"
            run_notifications(website_name="amazon")
        
        elif (len(add_to_cart_button) != 0) or (len(all_buying_options) != 0) or (len(pre_order_button) != 0):
            status="In Stock"
            run_notifications(website_name="amazon")

        else:
            status=f"A different response has been generated: {stock}"
        time.sleep(2)
        #print(status)
        
def scrape_shopatsc(shopatsc_link):
    while True:
        page_html = str(get_page_html(shopatsc_link))
        doc = lxml.html.fromstring(page_html)
        try:
            stock=doc.xpath('//*[@id="availability"]/span')[0].text
            add_to_cart_button=doc.xpath('//*[@id="add-to-cart-button"]')
            all_buying_options=doc.xpath('//*[@id="buybox-see-all-buying-choices"]/span/a')
            pre_order_button=doc.xpath('//*[@id="buy-now-button"]')
        except:
            stock="Amazon Error"
        #print(stock)
        print(add_to_cart_button)
        print(all_buying_options)
        print(pre_order_button)
        if "Currently unavailable." in stock or "We don't know when or if this item will be back in stock." in stock :
            status="Out of Stock"
        
        elif "In stock" in stock:
            status="In Stock"
            run_notifications(website_name="amazon")
       
        elif "This item will be released on" in stock:
            status="In Stock"
            run_notifications(website_name="amazon")
        
        elif (len(add_to_cart_button) != 0) or (len(all_buying_options) != 0) or (len(pre_order_button) != 0):
            status="In Stock"
            run_notifications(website_name="amazon")

        else:
            status=f"A different response has been generated: {stock}"
        time.sleep(2)
        #print(status)

def scrape_flipkart(flipkart_link):
    while True:
        page_html = str(get_page_html(flipkart_link))
        doc = lxml.html.fromstring(page_html)
        try:
            stock=doc.xpath('//*[@id="container"]/div/div[3]/div[1]/div[2]/div[3]/div')[0].text
            add_to_cart_button=doc.xpath('//*[@id="container"]/div/div[3]/div[1]/div[1]/div[2]/div/ul/li[1]/button')
        except:
            print("Flipkart Error")
            continue
        print(stock)
        print(add_to_cart_button)
        if stock is None and len(add_to_cart_button) !=0 :
            status="In Stock"
            run_notifications(website_name="flipkart")

        if stock is None:
            #No value was retrived, but Add to Cart button doesn't exist
            pass

        elif "Sold Out" in stock or "Coming Soon" in stock :
            status="Out of Stock"

        else:
            status=f"A different response has been generated: {stock}"
        time.sleep(2)
        print(status)

async def scrape_games_the_shop(games_the_shop_link):
    while True:
        page_html = get_page_html(games_the_shop_link)
        doc = lxml.html.fromstring(page_html)
        try:
            stock=doc.xpath('//*[@id="ctl00_ContentPlaceHolder1_divOfferDetails"]/div/div[2]/div/div[2]/div[1]/text()')
            #print(stock)
        except:
            print("Games the Shop Error")
    
        if " ADD TO CART" in stock:
            status="In Stock"
            run_notifications(website_name="games_the_shop")

        elif len(stock) == 0:
            status="Out of Stock"

        else:
            status=f"A different response has been generated: {stock}"               
        time.sleep(2)
        print(status)
    

async def scrape_ppgc(ppgc_link):
    while True:
        page_html = get_page_html(ppgc_link)
        doc = lxml.html.fromstring(page_html)
        try:
            stock=doc.xpath('//*[@id="product-7990"]/div/div[1]/div/div[2]/form/button/text()')#[0].strip()
            #print(stock)
        except:
            print("Prepaid Gamer Card Error")
    
        if "Add to cart" in stock:
            status="In Stock"
            run_notifications(website_name="ppgc")

        elif len(stock) == 0:
            status="Out of Stock"

        else:
            status=f"A different response has been generated: {stock}"
            
        time.sleep(2)
        print(status)


#Comment out the websites you are not using
#To comment a site add "#" in front of it.
#startup(site="flipkart")
#startup(site="amazon")
# startup(site="gts")
# startup(site="ppgc")
startup(site="shopatsc")