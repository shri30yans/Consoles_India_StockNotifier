import config


#Minimum time for the bot to notify about the same product from the same website again.
#Default is 30 seconds
notifications_delay={   
            "XSS":60*60*2,
            "XSX":60*1,
            "PS5":60*1,
            "PS5_DE":60*1,
            "RED_DS":60*60*3,
            "BLACK_DS":60*60*3}

class Product:
            def __init__(self,name,notification_channels,twitter_hashtags="",thumbnail_link=None,colour =0x000000,emoji = ""):
                self.name = name
                self.twitter_hashtags = twitter_hashtags
                self.notification_channels = notification_channels
                self.thumbnail_link = thumbnail_link
                self.emoji = emoji
                self.colour = colour

All_Products = {
            "PS5":Product(name="PS5",notification_channels = config.both_playstation_channels,twitter_hashtags="#RestockPS5India #PS5",thumbnail_link="https://i.imgur.com/pmgar66.jpg?1",colour =0x2100ff,emoji = config.PS5_emoji),
            "PS5_DE":Product(name="PS5 DE",notification_channels = config.both_playstation_channels,twitter_hashtags="#RestockPS5India #PS5Digital",thumbnail_link="https://i.imgur.com/pmgar66.jpg?1",colour =0x008eff,emoji = config.PS5_DE_emoji),
            "XSX":Product(name="XSX",notification_channels = config.xbox_channel,twitter_hashtags="#RestockXSXIndia #XSX",thumbnail_link="https://i.imgur.com/WpKbZXR.jpg",colour =0x3e8806,emoji = config.XSX_emoji),
            "XSS":Product(name="XSS",notification_channels = config.xbox_channel,twitter_hashtags="#XSS",thumbnail_link="https://i.imgur.com/OpInEum.jpg",colour =0x5dd35d,emoji = config.XSS_emoji),
            
            "RED_DS":Product(name="RED_DS",notification_channels = config.playstation_channel,colour =0xff0000,emoji = config.RED_DS_emoji),
            "BLACK_DS":Product(name="BLACK_DS",notification_channels = config.playstation_channel,colour =0x030000,emoji = config.BLACK_DS_emoji),
            }



class Website:
    def __init__(self,display_name:str,common_name:str,links:dict,wishlist_link:str=None,wishlist_products=None,affiliate_links:list=None,add_to_cart_links:list=None,headers:list=None):
        self.common_name = common_name
        self.display_name=display_name
        self.links = links
        self.wishlist_link=wishlist_link
        self.wishlist_products=wishlist_products
        self.headers = headers
        self.affiliate_links=affiliate_links
        self.add_to_cart_links = add_to_cart_links

class  Amazon_Wishlist_Item:
    def __init__(self,item_id,max_cost):
        self.item_id = item_id
        self.max_cost = max_cost

        
All_Websites={

    "amazon":Website(display_name="Amazon",common_name="amazon",
        links = {
                "PS5": "https://www.amazon.in/dp/B08FV5GC28?smid=AT95IG9ONZD7S",
                "PS5_DE": "https://www.amazon.in/Sony-CFI-1008B01R-PlayStation-Digital-Edition/dp/B08FVRQ7BZ?smid=AT95IG9ONZD7S",
                "XSX": "https://www.amazon.in/Xbox-Series-X/dp/B08J7QX1N1/?smid=AT95IG9ONZD7S",
                "XSS": "https://www.amazon.in/Xbox-Series-S/dp/B08J89D6BW/?smid=AT95IG9ONZD7S",
                "RED_DS": "https://www.amazon.in/DualSense-Wireless-Controller-Red-PlayStation/dp/B098439Y2G?smid=AT95IG9ONZD7S",
                "BLACK_DS" :"https://www.amazon.in/DualSense-Wireless-Controller-Black-PlayStation/dp/B09842ZHNM?smid=AT95IG9ONZD7S" },

        affiliate_links = {
            "RED_DS":"https://amzn.to/39na5kH",
            "BLACK_DS": "https://amzn.to/3iriuZl",
            "PS5" : "https://www.amazon.in/dp/B08FV5GC28/?tag=shri30yans-21",
            "PS5_DE" :"https://www.amazon.in/Sony-CFI-1008B01R-PlayStation-Digital-Edition/dp/B08FVRQ7BZ/?tag=shri30yans-21",
            "XSS" : "https://amzn.to/3a13tIZ",
            "XSX" :"https://www.amazon.in/Xbox-Series-X/dp/B08J7QX1N1/?tag=shri30yans-21",
            "WISHLIST": "https://www.amazon.in/hz/wishlist/ls/1TAF69OJPC2BQ/?viewType=list&tag=shri30yans-21"},
        
        add_to_cart_links ={
            "PS5": "https://www.amazon.in/gp/aws/cart/add.html?AssociateTag=?tag=shri30yans-21&ASIN.1=B08FV5GC28&Quantity.1=1",
            "PS5_DE": "https://www.amazon.in/gp/aws/cart/add.html?AssociateTag=?tag=shri30yans-21&ASIN.1=B08FVRQ7BZ&Quantity.1=1",
            "XSX": "https://www.amazon.in/gp/aws/cart/add.html?AssociateTag=?tag=shri30yans-21&ASIN.1=B08J7QX1N1&Quantity.1=1",
            "XSS": "https://www.amazon.in/gp/aws/cart/add.html?AssociateTag=?tag=shri30yans-21&ASIN.1=B08J89D6BW&Quantity.1=1",
            "RED_DS": "https://www.amazon.in/gp/aws/cart/add.html?AssociateTag=?tag=shri30yans-21&ASIN.1=B098439Y2G&Quantity.1=1",
            "BLACK_DS" :"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag=?tag=shri30yans-21&ASIN.1=B09842ZHNM&Quantity.1=1" },
        


        wishlist_link = "https://www.amazon.in/hz/wishlist/ls/1TAF69OJPC2BQ/?viewType=list",

        wishlist_products = {
            "RED_DS":Amazon_Wishlist_Item(item_id = "I3237V48OIEN94", max_cost = 6500 ),
            "BLACK_DS": Amazon_Wishlist_Item(item_id = "IJQJKY5K0113B", max_cost = 6000 ),
            "PS5" : Amazon_Wishlist_Item(item_id = "IB3PLDK83YLBG",max_cost = 50000),
            "PS5_DE" : Amazon_Wishlist_Item(item_id = "I1G75WOQCJ6GYE",max_cost = 40000),
            "XSS" : Amazon_Wishlist_Item(item_id = "I2D2PR67EB4NAH",max_cost = 35000 ),
            "XSX" : Amazon_Wishlist_Item(item_id = "I3M997QVSEVYFH",max_cost = 50000 )},
       
        headers = [{       
            'sec-ch-ua': '^\\^',
            'Accept': 'application/json',
            'DNT': '1',
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
            'Content-Type': 'application/json',
            'Origin': 'https://www.amazon.in/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Referer': 'https://www.amazon.in/',
            },
            {
            'authority': 'www.amazon.in',
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
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36',
            'content-type': 'application/x-www-form-urlencoded',
            'accept': 'text/html,*/*',
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
        ),
        
    "flipkart":Website(display_name="Flipkart",common_name="flipkart",
        links = {
                "PS5": "https://www.flipkart.com/sony-playstation-5-cfi-1008a01r-825-gb-astro-s-playroom/p/itma0201bdea62fa",
                "PS5_DE": "https://www.flipkart.com/sony-playstation-5-cfi-1008b01r-825-gb-astro-s-playroom/p/itm8bf74f8d0b890?",
                "XSX": "https://www.flipkart.com/microsoft-xbox-series-x-1024-gb/p/itm63ff9bd504f27",
                "XSS": "https://www.flipkart.com/microsoft-xbox-series-s-512-gb/p/itm13c51f9047da8", },

        headers = [{
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
        ),
    
    "shopatsc":Website(display_name="ShopAtSC",common_name="shopatsc",
        links  = {
                "PS5": "https://shopatsc.com/products/playstation-5-console",
                "PS5_DE": "https://shopatsc.com/products/playstation5-digital-edition",
                "RED_DS": "https://shopatsc.com/products/dualsense-wireless-controller-red",
                "BLACK_DS" :"https://shopatsc.com/products/dualsense-wireless-controller-black" }),
    
    "games_the_shop":Website(display_name="Games the Shop",common_name="games_the_shop",
        links = {
                "PS5": "https://www.gamestheshop.com/PlayStation-5-Console/5111",
                "PS5_DE": "https://www.gamestheshop.com/PlayStation-5-Digital-Edition/5112",
                "XSX": "https://www.flipkart.com/microsoft-xbox-series-x-1024-gb/p/itm63ff9bd504f27",
                "XSS": "https://www.flipkart.com/microsoft-xbox-series-s-512-gb/p/itm13c51f9047da8"}),

    "ppgc":Website(display_name="Prepaid Gamer Card",common_name="ppgc",
        links = {
                "PS5": "https://prepaidgamercard.com/product/playstation-5-console-ps5/",
                "PS5_DE": "https://prepaidgamercard.com/product/playstation-5-digital-edition-ps5/"})   
        }
