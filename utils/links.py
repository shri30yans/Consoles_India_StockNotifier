class Website:
    def __init__(self,display_name:str,common_name:str,PS5_link:str,XSX_link:str=None,XSS_link:str=None):
        self.display_name=display_name
        self.common_name=common_name
        self.PS5_link=PS5_link
        self.XSX_link=XSX_link
        self.XSS_link=XSS_link
        
All_Websites={
    "flipkart":Website(display_name="Flipkart",common_name="flipkart",PS5_link="https://www.flipkart.com/sony-playstation-5-cfi-1008a01r-825-gb-astro-s-playroom/p/itma0201bdea62fa",XSX_link="https://www.flipkart.com/microsoft-xbox-series-x-1024-gb/p/itm63ff9bd504f27",XSS_link="https://www.flipkart.com/microsoft-xbox-series-s-512-gb/p/itm13c51f9047da8"),
    "amazon":Website(display_name="Amazon",common_name="amazon",PS5_link="https://www.amazon.in/dp/B08FV5GC28",XSX_link="https://www.amazon.in/Xbox-Series-X/dp/B08J7QX1N1/",XSS_link="https://www.amazon.in/Xbox-Series-S/dp/B08J89D6BW/ref=sr_1_1?dchild=1&keywords=xbox+series+s&qid=1624253613&sr=8-1"),
    "games_the_shop":Website(display_name="Games the Shop",common_name="games_the_shop",PS5_link="https://www.gamestheshop.com/PlayStation-5-Console/5111"),
    "ppgc":Website(display_name="Prepaid Gamer Card",common_name="ppgc",PS5_link="https://prepaidgamercard.com/product/playstation-5-console-ps5/"),}


# All_Websites={
#     "flipkart":Website(display_name="Flipkart",common_name="flipkart",PS5_link="https://www.flipkart.com/marvels-spider-man-miles-morales/p/itm27b29133a64d3?pid=GAMFYTW9ZRQAZFKG&lid=LSTGAMFYTW9ZRQAZFKGDDV1S3&marketplace=FLIPKART&store=4rr&srno=b_1_2&otracker=clp_banner_1_2.banner.BANNER_gaming-store_2GSQZNPR3D52&fm=organic&iid=0bdae676-02ad-47d1-bc33-73ff7ff3ee1d.GAMFYTW9ZRQAZFKG.SEARCH&ppt=None&ppn=None&ssid=0t3y9ge4a80000001622897908920"),
#     "amazon":Website(display_name="Amazon",common_name="amazon",PS5_link="https://www.amazon.in/dp/B08WK5T3HY?pf_rd_m=A1VBAL9TL5WCBF&pf_rd_t=30901&pf_rd_i=976460031&pf_rd_s=mobile-browse-hero-2&pf_rd_r=KBBDGVS15HD850GS8ZWY&pf_rd_p=526450a6-8633-4d0f-9869-41929acbc963&ref_=Oct_Arh_mobile-browse-hero-2_d33ddf81-38ab-43b5-8d6b-202869bb1e5e"),
#     "games_the_shop":Website(display_name="Games the Shop",common_name="games_the_shop",PS5_link="https://www.gamestheshop.com/PlayStation-5-Console/5111"),
#     "ppgc":Website(display_name="Prepaid Gamer Card",common_name="ppgc",PS5_link="https://prepaidgamercard.com/product/playstation-5-console-ps5/"),}


