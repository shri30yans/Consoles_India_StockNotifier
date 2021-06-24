############################################################################
#This is test code and will most likely not work
#For the scrapping code refer to cogs/stockchecker.py
############################################################################

import requests,time,random
import lxml.html
from collections import OrderedDict

All_Websites={
    "flipkart":"https://www.flipkart.com/sony-playstation-5-cfi-1008a01r-825-gb-astro-s-playroom/p/itma0201bdea62fa",
    "amazon":"https://www.amazon.in/Xbox-Series-S/dp/B08J89D6BW/",
    "games_the_shop":"https://www.gamestheshop.com/PlayStation-5-Console/5111",
    "ppgc":"https://prepaidgamercard.com/product/playstation-5-console-ps5/",
    "shopatsc":"https://shopatsc.com/collections/personal-audio/products/sony-wh-1000xm4-industry-leading-wireless-noise-cancelling-headphones-bluetooth-headset-with-mic-for-phone-calls-30-hours-battery-life-quick-charge-touch-control-alexa-voice-control-black?variant=34225365942411",}

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
        

def get_page_html(url,headers_list=[{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"}]):
    ordered_headers_list = []
    for headers in headers_list:
        h = OrderedDict()
        for header,value in headers.items():
            h[header]=value
            ordered_headers_list.append(h)
    headers = random.choice(headers_list)

    page = requests.get(url, headers=headers)
    return page.content,page.status_code

def scrape_amazon(amazon_link):
    headers_list = [{
            'Connection': 'keep-alive',
            'sec-ch-ua': '^\\^',
            'Accept': 'application/json',
            'DNT': '1',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36',
            'Content-Type': 'application/json',
            'Origin': 'https://www.amazon.in',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': 'https://www.amazon.in/',
            'Accept-Language': 'en-IN,en;q=0.9',
            },      
            {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.5',
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
            'Origin': 'https://www.amazon.in/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Referer': 'https://www.amazon.in/',
            },
            {
            'authority': 'www.amazon.in',
            'x-kl-ajax-request': 'Ajax_Request',
            'dnt': '1',
            'rtt': '200',
            'sec-ch-ua-mobile': '?0',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36',
            'accept': 'text/html,/',
            'ect': '4g',
            'sec-ch-ua': '^^',
            'origin': 'https://www.amazon.in/',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://www.amazon.in/',
            'accept-language': 'en-US,en;q=0.9',
           
            },
            {
            'Connection': 'keep-alive',
            'sec-ch-ua': '^^',
            'Accept': 'application/json, text/javascript, /; q=0.01',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36',
            'Origin': 'https://www.amazon.in/',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': 'https://www.amazon.in/',
            'Accept-Language': 'en-GB,en;q=0.9',
            },
            {
            'authority': 'www.amazon.in',
            'sec-ch-ua': '^\\^',
            'rtt': '50',
            'sec-ch-ua-mobile': '?0',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36',
            'content-type': 'application/x-www-form-urlencoded',
            'accept': 'text/html,*/*',
            'x-requested-with': 'XMLHttpRequest',
            'downlink': '10',
            'ect': '4g',
            'origin': 'https://www.amazon.in',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://www.amazon.in/dp/B08FV5GC28',
            'accept-language': 'en-US,en;q=0.9',         
            },
            {
            'sec-ch-ua': '^^',
            'Referer': 'https://www.amazon.in/',
            'sec-ch-ua-mobile': '?1',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Mobile Safari/537.36',
            }       
            ]

    while True:
        page_html = str(get_page_html(amazon_link,headers_list))
        doc = lxml.html.fromstring(page_html)
        try:
            stock=doc.xpath('//*[@id="availability"]/span')[0].text
            add_to_cart_button=doc.xpath('//*[@id="add-to-cart-button"]')
            all_buying_options=doc.xpath('//*[@id="buybox-see-all-buying-choices"]/span/a')
            pre_order_button=doc.xpath('//*[@id="buy-now-button"]')
        except:
            stock="Amazon Error"
            print("Error")
            continue
        #print(stock)
        print(add_to_cart_button)
        print(all_buying_options)
        print(pre_order_button)
        
        if "Currently unavailable." in stock or "We don't know when or if this item will be back in stock." in stock :
            status="Out of Stock"
        
        elif "In stock".lower() in stock.lower():
            status="In Stock"
            run_notifications(website_name="amazon")
       
        # elif "This item will be released on" in stock:
        #     status="In Stock"
        #     run_notifications(website_name="amazon")
        
        elif (len(add_to_cart_button) != 0) or (len(all_buying_options) != 0) or (len(pre_order_button) != 0):
            status="In Stock"
            run_notifications(website_name="amazon")

        else:
            status=f"A different response has been generated: {stock}"
        time.sleep(3)
        #print(status)
        
def scrape_shopatsc(shopatsc_link):
    while True:
        page_html = str(get_page_html(shopatsc_link))
        doc = lxml.html.fromstring(page_html)
        try:
            stock = doc.xpath('//*[@id="notify_btn_div"]')                                  
            add_to_cart_button = doc.xpath('//*[@id="product-add-to-cart"]')
        except:
            print("shopatscdigital Error")
            continue
        
        print("Stock",stock)
        print("Add_to_cart",add_to_cart_button)
        time.sleep(2)

        #print(status)

def scrape_flipkart(flipkart_link):
    headers_list = [{
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
        'Accept': '*/*',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
        'origin': 'https://www.flipkart.com',
        'referer': 'https://www.flipkart.com/',
        'accept-language': 'en-IN,en;q=0.9',
        'Referer': 'https://www.flipkart.com/',
        }, 
        {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36 Edg/91.0.864.54',
        'Accept-Language': 'en-US,en;q=0.9',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36 Edg/91.0.864.54',
        'accept': '*/*',
        'referer': 'https://www.flipkart.com/',
        'accept-language': 'en-US,en;q=0.9',
        'origin': 'https://www.flipkart.com',
        'Cache-Control': 'max-age=0',
        'Service-Worker': 'script',
        'Origin': 'https://www.flipkart.com',
        },
        {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,/;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9,ta;q=0.8",
        "Upgrade-Insecure-Requests": "1",
        'referer': 'https://www.flipkart.com/',
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36 Edg/91.0.864.54",
        'origin': 'https://www.flipkart.com',
        } ,
        {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,/;q=0.8,application/signed-exchange;v=b3;q=0.9", 
        "Accept-Encoding": "gzip, deflate, br", 
        "Accept-Language": "en-US,en;q=0.9",  
        'origin': 'https://www.flipkart.com',
        'referer': 'https://www.flipkart.com/',
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36", 
        }
        ]
    while True:
        page_html = str(get_page_html(flipkart_link,headers_list=headers_list))
        doc = lxml.html.fromstring(page_html)
        try:
            sold_out_element=doc.xpath('//*[@id="container"]/div/div[3]/div[1]/div[2]/div[3]/div')[0].text
            sold_out_sentence=doc.xpath('//*[@id="container"]/div/div[3]/div[1]/div[2]/div[3]/div[2]')[0].text
            add_to_cart_button=doc.xpath('//*[@id="container"]/div/div[3]/div[1]/div[1]/div[2]/div/ul/li[1]/button')
            buy_now_button=doc.xpath('//*[@id="container"]/div/div[3]/div[1]/div[1]/div[2]/div/ul/li[2]/form/button')
        except:
            print("Flipkart Error")
            continue
        print(sold_out_element)
        print(sold_out_sentence)
        print(add_to_cart_button)
        print(buy_now_button)

        print("------------")

        if "Sold Out" in sold_out_element or "This item is currently out of stock" in sold_out_sentence:
            pass #checks for false negatives/makes sure it doesn't show Item is in stock when this is shown
              
        elif len(add_to_cart_button) !=0 :
            status="In Stock"
            run_notifications(website_name="flipkart")
        
        elif len(buy_now_button ) !=0:
            status="In Stock"
            run_notifications(website_name="flipkart")
        
        elif sold_out_element is None and sold_out_sentence is None:
            status="In Stock"
            run_notifications(website_name="flipkart")

        else:
            pass
            #print("Not in stock")


            #stock=doc.xpath('//*[@id="container"]/div/div[3]/div[1]/div[2]/div[3]/div')[0].text
            #buy_now_button=doc.xpath('//*[@id="container"]/div/div[3]/div[1]/div[1]/div[2]/div/ul/li[2]/form/button')
        # except:
        #     print("Flipkart Error")
        #     continue
        
        #print(add_to_cart_button)
        #print(buy_now_button)


        # elif stock is None:
        #     #No value was retrived, but Add to Cart button doesn't exist
        #     pass

        # elif "Sold Out" in stock or "Coming Soon" in stock :
        #     status="Out of Stock"

        # else:
        #     status=f"A different response has been generated: {stock}"
        time.sleep(2)
        #print(status)

def scrape_games_the_shop(games_the_shop_link):
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
    

def scrape_ppgc(ppgc_link):
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
startup(site="flipkart")
#startup(site="amazon")
# startup(site="gts")
# startup(site="ppgc")
#startup(site="shopatsc")