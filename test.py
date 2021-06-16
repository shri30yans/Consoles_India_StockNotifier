import requests,lxml.html,random,time

def get_page_html(url,headers_list=[{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"}]):
        headers = random.choice(headers_list)
        page = requests.get(url, headers=headers)
        return page.content

def scrape_scdigital(scdigital_link):
    while True:
        page_html = str(get_page_html(scdigital_link))
        doc = lxml.html.fromstring(page_html)
        #print(doc)
        try:
            stock = doc.xpath('//*[@id="notify_btn_div"]')                                  
            add_to_cart_button = doc.xpath('//*[@id="product-add-to-cart"]')
        except:
            print("shopatscdigital Error")
            continue
        
        print("Stock",stock)
        print("Add_to_cart",add_to_cart_button)
        time.sleep(1)


scrape_scdigital("https://shopatsc.com/collections/playstation-5/products/playstation5-digital-edition")
#scrape_scdigital("https://shopatsc.com/collections/home-audio/products/sony-ht-rt3-sound-bar-type-home-theatre-system-black")


