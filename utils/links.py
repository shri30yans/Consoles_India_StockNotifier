class Website:
    def __init__(self,display_name:str,common_name:str,link:str):
        self.display_name=display_name
        self.common_name=common_name
        self.link=link
        
All_Websites={
    "flipkart":Website(display_name="Flipkart",common_name="flipkart",link="https://www.flipkart.com/sony-playstation-5-cfi-1008a01r-825-gb-astro-s-playroom/p/itma0201bdea62fa"),
    "amazon":Website(display_name="Amazon",common_name="amazon",link="https://www.amazon.in/dp/B08FV5GC28"),
    "games_the_shop":Website(display_name="Games the Shop",common_name="games_the_shop",link="https://www.gamestheshop.com/PlayStation-5-Console/5111"),
    "ppgc":Website(display_name="Prepaid Gamer Card",common_name="ppgc",link="https://prepaidgamercard.com/product/playstation-5-console-ps5/"),}



