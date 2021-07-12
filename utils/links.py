class Website:
    def __init__(self,display_name:str,common_name:str,PS5_link:str,PS5_DE_link:str=None,XSX_link:str=None,XSS_link:str=None):
        self.display_name=display_name
        self.common_name=common_name
        self.PS5_link=PS5_link
        self.XSX_link=XSX_link
        self.XSS_link=XSS_link
        self.PS5_DE_link=PS5_DE_link
        
All_Websites={

    "amazon":Website(display_name="Amazon",common_name="amazon",
        PS5_link="https://www.amazon.in/dp/B08FV5GC28",
        PS5_DE_link="https://www.amazon.in/Sony-CFI-1008B01R-PlayStation-Digital-Edition/dp/B08FVRQ7BZ",
        XSX_link="https://www.amazon.in/Xbox-Series-X/dp/B08J7QX1N1/",
        XSS_link="https://www.amazon.in/Xbox-Series-S/dp/B08J89D6BW/"),
        
    "flipkart":Website(display_name="Flipkart",common_name="flipkart",
        PS5_link="https://www.flipkart.com/sony-playstation-5-cfi-1008a01r-825-gb-astro-s-playroom/p/itma0201bdea62fa",
        PS5_DE_link="https://www.flipkart.com/sony-playstation-5-cfi-1008b01r-825-gb-astro-s-playroom/p/itm8bf74f8d0b890?",
        XSX_link="https://www.flipkart.com/microsoft-xbox-series-x-1024-gb/p/itm63ff9bd504f27",
        XSS_link="https://www.flipkart.com/microsoft-xbox-series-s-512-gb/p/itm13c51f9047da8"),
    
    "shopatsc":Website(display_name="ShopAtSC",common_name="shopatsc",
        PS5_link="https://shopatsc.com/products/playstation-5-console",
        PS5_DE_link="https://shopatsc.com/collections/playstation-5/products/playstation5-digital-edition",),
    
    "games_the_shop":Website(display_name="Games the Shop",common_name="games_the_shop",
        PS5_link="https://www.gamestheshop.com/PlayStation-5-Console/5111"),
    
    "ppgc":Website(display_name="Prepaid Gamer Card",common_name="ppgc",
        PS5_link="https://prepaidgamercard.com/product/playstation-5-console-ps5/"),
        }




