import requests,time
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
    "flipkart":"https://www.flipkart.com/sony-playstation-5-cfi-1008a01r-825-gb-astro-s-playroom/p/itma0201bdea62fa",
    "amazon":"https://www.amazon.in/Bundled-Spider-Man-GTaSport-Ratchet-3Month/dp/B08FNXXH5J/?_encoding=UTF8&pd_rd_w=RukHh&pf_rd_p=ab4aa62e-ee61-4bc4-928a-fc54f74f1993&pf_rd_r=BWEZTTGPG0X35GMQ0A75&pd_rd_r=eed58695-de47-41d2-bce5-c38b4f7a9b56&pd_rd_wg=Y6O6X&ref_=pd_gw_ci_mcx_mr_hp_d",
    "games_the_shop":"https://www.gamestheshop.com/PlayStation-5-Console/5111",
    "ppgc":"https://prepaidgamercard.com/product/playstation-5-console-ps5/",}

def run_notifications(website_name):
    pass
    #print(f"Notification Alert! This product is in stock at {website_name}")

def startup(site):  
    if site == "flipkart" :
        scrape_flipkart(flipkart_link=All_Websites["flipkart"])
    elif site == "amazon" :
        scrape_amazon(amazon_link=All_Websites["amazon"])   
    elif site == "gts" :
        scrape_games_the_shop(games_the_shop_link=All_Websites["games_the_shop"])
    elif site == "ppgc" :
        scrape_ppgc(ppgc_link=All_Websites["ppgc"])
    else:
        print("Unknown site")
        

def get_page_html(url):
    headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"}
    page = requests.get(url, headers=headers)
    #print(page.status_code)
    return page.content
    
def scrape_amazon(amazon_link):
    while True:
        page_html = get_page_html(amazon_link)
        doc = lxml.html.fromstring(page_html)
        try:
            stock=doc.xpath('//*[@id="availability"]/span')[0].text
            #add_to_cart_button=doc.xpath('//*[@id="a-autoid-2-announce"]')
            #all_buying_options=doc.xpath('//*[@id="buybox-see-all-buying-choices"]/span/a')
        except:
            stock="Amazon Error"
        print(stock)
        #print(add_to_cart_button)
        #print(all_buying_options)
        if "Currently unavailable." in stock or "We don't know when or if this item will be back in stock." in stock :
            status="Out of Stock"
        elif "In stock" in stock:
            status="In Stock"
            run_notifications(website_name="amazon")
        else:
            status=f"A different response has been generated: {stock}"
        time.sleep(2)
        #print(status)

def scrape_flipkart(flipkart_link):
    while True:
        page_html = get_page_html(flipkart_link)
        doc = lxml.html.fromstring(page_html)
        try:
            stock=doc.xpath('//*[@id="container"]/div/div[3]/div[1]/div[2]/div[3]/div')[0].text
            add_to_cart_button=doc.xpath('//*[@id="container"]/div/div[3]/div[1]/div[1]/div[2]/div/ul/li[1]/button')
        except:
            print("Flipkart Error")
        #print(stock)
        #print(add_to_cart_button)
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
startup(site="amazon")
# startup(site="gts")
# startup(site="ppgc")