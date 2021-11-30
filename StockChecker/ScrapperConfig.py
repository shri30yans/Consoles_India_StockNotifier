import config
PS5_wishlist = "https://www.amazon.in/hz/wishlist/ls/K5HVAMY70DJ5/?viewType=list"
XBOX_wishlist= "https://www.amazon.in/hz/wishlist/ls/18WU5P3MXFWL0/?viewType=list"

class Product:
    def __init__(
        self,
        name,
        display_name,
        links,
        notification_roles=None,
        notification_channels=None,
        affiliate_links=None,
        add_to_cart_links=None,
        wishlist=None,
        twitter_hashtags="",
        thumbnail_link=None,
        colour=0x000000,
        emoji="",
    ):
        self.name = name
        self.display_name = display_name
        self.links = links
        
        self.notification_roles = notification_roles
        self.notification_channels = notification_channels

        self.affiliate_links = affiliate_links
        self.add_to_cart_links = add_to_cart_links
        self.wishlist = wishlist

        self.twitter_hashtags = twitter_hashtags
        self.thumbnail_link = thumbnail_link
        self.emoji = emoji
        self.colour = colour


All_Products = {
    "PS5": Product(
        name="PS5",
        display_name="PS5",
        links={
            "amazon": "https://www.amazon.in/dp/B08FV5GC28?smid=AT95IG9ONZD7S",
            "flipkart": "https://www.flipkart.com/sony-playstation-5-cfi-1008a01r-825-gb-astro-s-playroom/p/itma0201bdea62fa",
            "shopatsc": "https://shopatsc.com/products/playstation-5-console",
            "games_the_shop": "https://www.gamestheshop.com/PlayStation-5-Console/5111",
            "ppgc": "https://prepaidgamercard.com/product/playstation-5-console-ps5/",
            "reliance":"https://www.reliancedigital.in/sony-playstation-5-console/p/491936180"

        },
        add_to_cart_links={
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag=?tag={config.amazon_affiliate_tag}&ASIN.1=B08FV5GC28&Quantity.1=1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/dp/B08FV5GC28/?tag={config.amazon_affiliate_tag}",
        },
        wishlist = PS5_wishlist,
        notification_roles = {
            config.playstation_server_id: 849606173522788352,
            config.my_server_id: 893734056720740352,
        },
        notification_channels=config.both_playstation_channels,
        twitter_hashtags="#RestockPS5India #PS5",
        thumbnail_link="https://i.imgur.com/pmgar66.jpg?1",
        colour=0x2100FF,
        emoji=config.PS5_emoji,
    ),
    "PS5_DE": Product(
        name="PS5 DE",
        display_name="PS5 DE",
        links={
            "amazon": "https://www.amazon.in/Sony-CFI-1008B01R-PlayStation-Digital-Edition/dp/B08FVRQ7BZ?smid=AT95IG9ONZD7S",
            "flipkart": "https://www.flipkart.com/sony-playstation-5-cfi-1008b01r-825-gb-astro-s-playroom/p/itm8bf74f8d0b890?",
            "shopatsc": "https://shopatsc.com/products/playstation5-digital-edition",
            "games_the_shop": "https://www.gamestheshop.com/PlayStation-5-Digital-Edition/5112",
            "ppgc": "https://prepaidgamercard.com/product/playstation-5-digital-edition-ps5/",
            "reliance":"https://www.reliancedigital.in/sony-playstation-5-console/p/491936181"
        },
        add_to_cart_links={
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag=?tag={config.amazon_affiliate_tag}&ASIN.1=B08FVRQ7BZ&Quantity.1=1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/Sony-CFI-1008B01R-PlayStation-Digital-Edition/dp/B08FVRQ7BZ/?tag={config.amazon_affiliate_tag}"
        },
        wishlist = PS5_wishlist,
        notification_roles = {
            config.playstation_server_id: 857134006243688458,
            config.my_server_id: 893734151428132894,
        },
        notification_channels=config.both_playstation_channels,
        twitter_hashtags="#RestockPS5India #PS5Digital",
        thumbnail_link="https://i.imgur.com/pmgar66.jpg?1",
        colour=0x008EFF,
        emoji=config.PS5_DE_emoji,
    ),
    "PS5_Camera_Bundle": Product(
        name="PS5_Camera_bundle",
        display_name="PS5 & HD camera bundle",
        links={
            "amazon": "https://www.amazon.in/dp/B08NTT4RTQ/?smid=AT95IG9ONZD7S",
        },
        add_to_cart_links={
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag=?tag={config.amazon_affiliate_tag}&ASIN.1=B08NTT4RTQ&Quantity.1=1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/dp/B08NTT4RTQ/?tag={config.amazon_affiliate_tag}",
        },
        wishlist = PS5_wishlist,
        notification_roles = {
            config.playstation_server_id: 849606173522788352,
            config.my_server_id: 893734056720740352,
        },
        notification_channels=config.both_playstation_channels,
        twitter_hashtags="#RestockPS5India #PS5",
        thumbnail_link="https://i.imgur.com/pmgar66.jpg?1",
        colour=0x2100FF,
        emoji=config.PS5_emoji,
    ),
    "PS5_DE_Camera_Bundle": Product(
        name="PS5_DE_Camera_bundle",
        display_name="PS5 DE & HD camera bundle",
        links={
            "amazon": "https://www.amazon.in/gp/product/B08NTV53TC/?smid=AT95IG9ONZD7S",
        },
        add_to_cart_links={
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag=?tag={config.amazon_affiliate_tag}&ASIN.1=B08NTV53TC&Quantity.1=1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/gp/product/B08NTV53TC/?tag={config.amazon_affiliate_tag}",
        },
        wishlist = PS5_wishlist,
        notification_roles = {
            config.playstation_server_id: 857134006243688458,
            config.my_server_id: 893734151428132894,
        },
        notification_channels=config.both_playstation_channels,
        twitter_hashtags="#RestockPS5India #PS5",
        thumbnail_link="https://i.imgur.com/pmgar66.jpg?1",
        colour=0x2100FF,
        emoji=config.PS5_emoji,
    ),
    "PS5_DE_Remote_Bundle": Product(
        name="PS5_DE_Remote_bundle",
        display_name="PS5 DE & Media Remote bundle",
        links={
            "amazon": "https://www.amazon.in/dp/B08NTVH9VG/?smid=AT95IG9ONZD7S",
        },
        add_to_cart_links={
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag=?tag={config.amazon_affiliate_tag}&ASIN.1=B08NTVH9VG&Quantity.1=1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/gp/product/B08NTVH9VG/?tag={config.amazon_affiliate_tag}",
        },
        wishlist = PS5_wishlist, 
        notification_roles = {
            config.playstation_server_id: 857134006243688458,
            config.my_server_id: 893734151428132894,
        },
        notification_channels=config.both_playstation_channels,
        twitter_hashtags="#RestockPS5India #PS5",
        thumbnail_link="https://i.imgur.com/pmgar66.jpg?1",
        colour=0x2100FF,
        emoji=config.PS5_emoji
    ),
    "PS5_DE_Pulse_Bundle": Product(
        name="PS5_DE_Pulse_bundle",
        display_name="PS5 DE & Pulse 3D bundle",
        links={
            "amazon": "https://www.amazon.in/dp/B08NTV1QDX/?smid=AT95IG9ONZD7S",
        },
        add_to_cart_links={
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag=?tag={config.amazon_affiliate_tag}&ASIN.1=B08NTV1QDX&Quantity.1=1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/gp/product/B08NTV1QDX/?tag={config.amazon_affiliate_tag}",
        },
        wishlist = PS5_wishlist,
        notification_roles = {
            config.playstation_server_id: 857134006243688458,
            config.my_server_id: 893734151428132894,
        },
        notification_channels=config.both_playstation_channels,
        twitter_hashtags="#RestockPS5India #PS5",
        thumbnail_link="https://i.imgur.com/pmgar66.jpg?1",
        colour=0x2100FF,
        emoji=config.PS5_emoji
    ),
    "PS5_DE_Charging_Station_Bundle": Product(
        name="PS5_DE_Charging_Station_Bundle",
        display_name="PS5 DE & Dualsense Charging station bundle",
        links={
            "amazon": "https://www.amazon.in/dp/B08NTVHTPT/?smid=AT95IG9ONZD7S",
        },
        add_to_cart_links={
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag=?tag={config.amazon_affiliate_tag}&ASIN.1=B08NTVHTPT&Quantity.1=1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/gp/product/B08NTVHTPT/?tag={config.amazon_affiliate_tag}",
        },
        wishlist = PS5_wishlist,
        notification_roles = {
            config.playstation_server_id: 857134006243688458,
            config.my_server_id: 893734151428132894,
        },
        notification_channels=config.both_playstation_channels,
        twitter_hashtags="#RestockPS5India #PS5",
        thumbnail_link="https://i.imgur.com/pmgar66.jpg?1",
        colour=0x2100FF,
        emoji=config.PS5_emoji
    ),
    "WHITE_PULSE_3D": Product(
        name="WHITE_PULSE_3D",
        display_name="White PULSE 3D",
        links={
            "amazon": "https://www.amazon.in/dp/B08FVNCYWZ/?smid=AT95IG9ONZD7S",
            "flipkart": "https://www.flipkart.com/sony-ps5-pulse-3d-wireless-headset/p/itm668d882c6bb65",
        },
        add_to_cart_links={
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag=?tag={config.amazon_affiliate_tag}&ASIN.1=B08FVNCYWZ&Quantity.1=1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/gp/product/B08FVNCYWZ/?tag={config.amazon_affiliate_tag}",
        },
        wishlist = PS5_wishlist,
        notification_roles = {
            config.my_server_id: 914105121959460874,
        },
        notification_channels=config.playstation_channel,
        twitter_hashtags="#RestockPS5India #Pulse3D #PS5",
        thumbnail_link="https://i.imgur.com/pmgar66.jpg?1",
        colour=0x2100FF,
        emoji=config.PS5_emoji
    ),
    "BLACK_PULSE_3D": Product(
        name="BLACK_PULSE_3D",
        display_name="Black PULSE 3D",
        links={
            "shopatsc": "https://shopatsc.com/collections/playstation-5-accessories/products/ps5-headset-black",
        },
        add_to_cart_links={
        },
        affiliate_links={
        },
        wishlist = PS5_wishlist,
        notification_roles = {
            config.my_server_id: 914105313030991902,
        },
        notification_channels=config.playstation_channel,
        twitter_hashtags="#RestockPS5India #Pulse3D #PS5",
        thumbnail_link="https://i.imgur.com/pmgar66.jpg?1",
        colour=0x2100FF,
        emoji=config.PS5_emoji
    ),
    "XSX": Product(
        name="XSX",
        display_name="XSX",
        links={
            "amazon": "https://www.amazon.in/Xbox-Series-X/dp/B08J7QX1N1/?smid=AT95IG9ONZD7S",
            "flipkart": "https://www.flipkart.com/microsoft-xbox-series-x-1024-gb/p/itm63ff9bd504f27",
            "ppgc": "https://prepaidgamercard.com/product/xbox-series-x/",
            "reliance":"https://www.reliancedigital.in/xbox-series-x-console-with-wireless-controller-1-tb/p/491934660"
        },
        add_to_cart_links={
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag=?tag={config.amazon_affiliate_tag}&ASIN.1=B08J7QX1N1&Quantity.1=1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/Xbox-Series-X/dp/B08J7QX1N1/{config.amazon_affiliate_tag}",
        },
        wishlist = XBOX_wishlist,
        notification_roles = {
            config.my_server_id: 893734236392144926,
        },
        notification_channels=config.xbox_channel,
        twitter_hashtags="#RestockXSXIndia #XSX",
        thumbnail_link="https://i.imgur.com/WpKbZXR.jpg",
        colour=0x3E8806,
        emoji=config.XSX_emoji,
    ),
    "XSX_Gears_Tactics_Bundle": Product(
        name="XSX_Gear_Bundle",
        display_name="Xbox Series X & Gears Tactics bundle",
        links={
            "amazon": "https://www.amazon.in/dp/B08NRLQ294/?smid=AT95IG9ONZD7S",
        },
        add_to_cart_links={
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag=?tag={config.amazon_affiliate_tag}&ASIN.1=B08NRLQ294&Quantity.1=1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/Xbox-Series-X/dp/B08NRLQ294/{config.amazon_affiliate_tag}",
        },
        wishlist = XBOX_wishlist,
        notification_roles = {
            config.my_server_id: 893734236392144926,
        },
        notification_channels=config.xbox_channel,
        twitter_hashtags="#RestockXSXIndia #XSX",
        thumbnail_link="https://i.imgur.com/WpKbZXR.jpg",
        colour=0x3E8806,
        emoji=config.XSX_emoji,
    ),
    "XSX_White_Controller_Bundle": Product(
        name="XSX_White_Controller_Bundle",
        display_name="Xbox Series X & Robot White Controller bundle",
        links={
            "amazon": "https://www.amazon.in/dp/B08NRLS39X/?smid=AT95IG9ONZD7S",
        },
        add_to_cart_links={
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag=?tag={config.amazon_affiliate_tag}&ASIN.1=B08NRLS39X&Quantity.1=1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/Xbox-Series-X/dp/B08NRLS39X/{config.amazon_affiliate_tag}",
        },
        wishlist = XBOX_wishlist,
        notification_roles = {
            config.my_server_id: 893734236392144926,
        },
        notification_channels=config.xbox_channel,
        twitter_hashtags="#RestockXSXIndia #XSX",
        thumbnail_link="https://i.imgur.com/WpKbZXR.jpg",
        colour=0x3E8806,
        emoji=config.XSX_emoji,
    ),
    "XSX_Black_Controller_Bundle": Product(
        name="XSX_Black_Controller_Bundle",
        display_name="Xbox Series X & Carbon Black Controller bundle",
        links={
            "amazon": "https://www.amazon.in/dp/B08NQZGSJ2/?smid=AT95IG9ONZD7S",
        },
        add_to_cart_links={
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag=?tag={config.amazon_affiliate_tag}&ASIN.1=B08NQZGSJ2&Quantity.1=1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/Xbox-Series-X/dp/B08NQZGSJ2/{config.amazon_affiliate_tag}",
        },
        wishlist = XBOX_wishlist,
        notification_roles = {
            config.my_server_id: 893734236392144926,
        },
        notification_channels=config.xbox_channel,
        twitter_hashtags="#RestockXSXIndia #XSX",
        thumbnail_link="https://i.imgur.com/WpKbZXR.jpg",
        colour=0x3E8806,
        emoji=config.XSX_emoji,
    ),
    "XSX_Blue_Controller_Bundle": Product(
        name="XSX_Blue_Controller_Bundle",
        display_name="Xbox Series X & Shock Blue Controller bundle",
        links={
            "amazon": "https://www.amazon.in/dp/B08NRBNSPW/?smid=AT95IG9ONZD7S",
        },
        add_to_cart_links={
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag=?tag={config.amazon_affiliate_tag}&ASIN.1=B08NRBNSPW&Quantity.1=1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/Xbox-Series-X/dp/B08NRBNSPW/{config.amazon_affiliate_tag}",
        },
        wishlist = XBOX_wishlist,
        notification_roles = {
            config.my_server_id: 893734236392144926,
        },
        notification_channels=config.xbox_channel,
        twitter_hashtags="#RestockXSXIndia #XSX",
        thumbnail_link="https://i.imgur.com/WpKbZXR.jpg",
        colour=0x3E8806,
        emoji=config.XSX_emoji,
    ),
    "XSS": Product(
        name="XSS",
        display_name="XSS",
        links={
            "amazon": "https://www.amazon.in/Xbox-Series-S/dp/B08J89D6BW/?smid=AT95IG9ONZD7S",
            "flipkart": "https://www.flipkart.com/microsoft-xbox-series-s-512-gb/p/itm13c51f9047da8",
            "ppgc": "https://prepaidgamercard.com/product/xbox-series-s/",
            "reliance": "https://www.reliancedigital.in/xbox-series-s-console-with-wireless-controller-512-gb/p/491934659",

        },
        add_to_cart_links={
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag=?tag={config.amazon_affiliate_tag}&ASIN.1=B08J89D6BW&Quantity.1=1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/Xbox-Series-S/dp/B08J89D6BW/?tag={config.amazon_affiliate_tag}"
        },
        wishlist = XBOX_wishlist,
        notification_roles = {
            config.my_server_id: 893734365476057119,
        },
        notification_channels=config.xbox_channel,
        twitter_hashtags="#XSS",
        thumbnail_link="https://i.imgur.com/OpInEum.jpg",
        colour=0x5DD35D,
        emoji=config.XSS_emoji,
    ),
    "RED_DS": Product(
        name="RED_DS",
        display_name="Red Dualsense",
        links={
            "amazon": "https://www.amazon.in/DualSense-Wireless-Controller-Red-PlayStation/dp/B098439Y2G?smid=AT95IG9ONZD7S",
            "shopatsc": "https://shopatsc.com/products/dualsense-wireless-controller-red",
        },
        add_to_cart_links={
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag=?tag={config.amazon_affiliate_tag}&ASIN.1=B098439Y2G&Quantity.1=1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/DualSense-Wireless-Controller-Red-PlayStation/dp/B098439Y2G?tag={config.amazon_affiliate_tag}"
        },
        wishlist = PS5_wishlist,
        notification_roles = {
            config.my_server_id: 893734512255701035,
        },
        notification_channels=config.playstation_channel,
        colour=0xFF0000,
        emoji=config.RED_DS_emoji,
    ),
    "BLACK_DS": Product(
        name="BLACK_DS",
        display_name="Black Dualsense",
        links={
            "amazon": "https://www.amazon.in/DualSense-Wireless-Controller-Black-PlayStation/dp/B09842ZHNM?smid=AT95IG9ONZD7S",
            "shopatsc": "https://shopatsc.com/products/dualsense-wireless-controller-black",
        },
        add_to_cart_links={
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag=?tag={config.amazon_affiliate_tag}&ASIN.1=B09842ZHNM&Quantity.1=1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/DualSense-Wireless-Controller-Black-PlayStation/dp/B09842ZHNM?smid=AT95IG9ONZD7S?tag={config.amazon_affiliate_tag}"
        },
        wishlist = PS5_wishlist,
        notification_roles = {
            config.my_server_id: 893734593621000232,
        },
        notification_channels=config.playstation_channel,
        colour=0x030000,
        emoji=config.BLACK_DS_emoji,
    ),
    "PS5_WISHLIST": Product(
        name="PS5_WISHLIST",
        display_name="Playstation Wishlist",
        links={
            "amazon": PS5_wishlist,
        },
        emoji=f"{config.PS5_emoji}📜",
    ),
    "XBOX_WISHLIST": Product(
        name="XBOX_WISHLIST",
        display_name="Xbox Wishlist",
        links={
            "amazon": XBOX_wishlist,
        },
        emoji=f"{config.XSX_emoji}📜",
    ),
}


class Website:
    def __init__(
        self,
        display_name: str,
        common_name: str,
        wishlist_link: str = None,
        affiliate_wishlist_link=None,
        wishlist_products=None,
        headers: list = None,
    ):
        self.common_name = common_name
        self.display_name = display_name
        self.wishlist_link = wishlist_link
        self.affiliate_wishlist_link = affiliate_wishlist_link
        self.wishlist_products = wishlist_products
        self.headers = headers


class Amazon_Wishlist_Item:
    def __init__(self, name, ASIN, max_cost=None):
        self.name = name
        self.ASIN = ASIN
        self.max_cost = max_cost


All_Websites = {
    "amazon": Website(
        display_name="Amazon",
        common_name="amazon",
        affiliate_wishlist_link=f"https://www.amazon.in/hz/wishlist/ls/1TAF69OJPC2BQ/?viewType=list&tag={config.amazon_affiliate_tag}",
        wishlist_products={
            # "RED_DS": Amazon_Wishlist_Item(
            #     name="RED_DS", ASIN="B098439Y2G", max_cost=6500
            # ),
            # "BLACK_DS": Amazon_Wishlist_Item(
            #     name="BLACK_DS", ASIN="B09842ZHNM", max_cost=6000
            # ),
            "PS5": Amazon_Wishlist_Item(
                name="PS5", 
                ASIN="B08FV5GC28",
                max_cost=50000
            ),
            "PS5_DE": Amazon_Wishlist_Item(
                name="PS5_DE",
                ASIN="B08FVRQ7BZ",
                max_cost=40000
            ),
            "PS5_Camera_Bundle": Amazon_Wishlist_Item(
                name="PS5_Camera_Bundle",
                ASIN="B08NTT4RTQ"
            ),
            "PS5_DE_Camera_Bundle": Amazon_Wishlist_Item(
                name="PS5_DE_Camera_Bundle",
                ASIN="B08NTV53TC"
            ),
            "PS5_DE_Remote_Bundle": Amazon_Wishlist_Item(
                name="PS5_DE_Remote_Bundle",
                ASIN="B08NTVH9VG"
            ),
            "PS5_DE_Pulse_Bundle": Amazon_Wishlist_Item(
                name="PS5_DE_Pulse_Bundle",
                ASIN="B08NTV1QDX"
            ),
            "PS5_DE_Charging_Station_Bundle": Amazon_Wishlist_Item(
                name="PS5_DE_Charging_Station_Bundle",
                ASIN="B08NTVHTPT"
            ),
            "PS5_Camera_Bundle": Amazon_Wishlist_Item(
                name="PS5_Camera_Bundle",
                ASIN="B08NTT4RTQ"
            ),
            "WHITE_PULSE_3D": Amazon_Wishlist_Item(
                name="WHITE_PULSE_3D",
                ASIN="B08FVNCYWZ"
            ),
            # "BLACK_PULSE_3D": Amazon_Wishlist_Item(
            #     name="BLACK_PULSE_3D",
            #     ASIN=""
            # ),
            # "XSS": Amazon_Wishlist_Item(
            #     name="XSS",
            #     ASIN="B08J89D6BW",
            #     max_cost=35000
            # ),
            "XSX": Amazon_Wishlist_Item(
                name="XSX",
                ASIN="B08J7QX1N1",
                max_cost=50000
            ),
            "XSX_Gears_Tactics_Bundle": Amazon_Wishlist_Item(
                name="XSX_Gears_Tactics_Bundle",
                ASIN="B08NRLQ294"
            ),
            "XSX_Blue_Controller_Bundle": Amazon_Wishlist_Item(
                name="XSX_Blue_Controller_Bundle",
                ASIN="B08NRBNSPW"
            ),
            "XSX_White_Controller_Bundle": Amazon_Wishlist_Item(
                name="XSX_White_Controller_Bundle",
                ASIN="B08NRLS39X"
            ),
            "XSX_Black_Controller_Bundle": Amazon_Wishlist_Item(
                name="XSX_Black_Controller_Bundle",
                ASIN="B08NQZGSJ2"
            ),
        },

        headers=[
            {
                "sec-ch-ua": "^\\^",
                "Accept": "application/json",
                "DNT": "1",
                "sec-ch-ua-mobile": "?0",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
                "Content-Type": "application/json",
                "Origin": "https://www.amazon.in",
                "Sec-Fetch-Site": "cross-site",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Dest": "empty",
                "Referer": "https://www.amazon.in/",
                "Accept-Language": "en-IN,en;q=0.9",
            },
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.5",
                "Content-Type": "application/json",
                "Origin": "https://www.amazon.in/",
                "DNT": "1",
                "Connection": "keep-alive",
                "Referer": "https://www.amazon.in/",
            },
            {
                "authority": "www.amazon.in",
                "dnt": "1",
                "rtt": "200",
                "sec-ch-ua-mobile": "?0",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
                "accept": "text/html,/",
                "ect": "4g",
                "sec-ch-ua": "^^",
                "origin": "https://www.amazon.in/",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty",
                "referer": "https://www.amazon.in/",
                "accept-language": "en-US,en;q=0.9",
            },
            {
                "Connection": "keep-alive",
                "sec-ch-ua": "^^",
                "Accept": "application/json, text/javascript, /; q=0.01",
                "sec-ch-ua-mobile": "?0",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
                "Origin": "https://www.amazon.in/",
                "Sec-Fetch-Site": "cross-site",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Dest": "empty",
                "Referer": "https://www.amazon.in/",
                "Accept-Language": "en-GB,en;q=0.9",
            },
            {
                "authority": "www.amazon.in",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
                "content-type": "application/x-www-form-urlencoded",
                "accept": "text/html,*/*",
                "ect": "4g",
                "origin": "https://www.amazon.in",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty",
                "referer": "https://www.amazon.in/dp/B08FV5GC28",
                "accept-language": "en-US,en;q=0.9",
            },
            {
                "sec-ch-ua": "^^",
                "Referer": "https://www.amazon.in/",
                "sec-ch-ua-mobile": "?1",
                "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Mobile Safari/537.36",
            },
        ],
    ),
    "flipkart": Website(
        display_name="Flipkart",
        common_name="flipkart",
        headers=[
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
                "Accept": "*/*",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
                "origin": "https://www.flipkart.com",
                "referer": "https://www.flipkart.com/",
                "accept-language": "en-IN,en;q=0.9",
                "Referer": "https://www.flipkart.com/",
            },
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36 Edg/91.0.864.54",
                "Accept-Language": "en-US,en;q=0.9",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36 Edg/91.0.864.54",
                "accept": "*/*",
                "referer": "https://www.flipkart.com/",
                "accept-language": "en-US,en;q=0.9",
                "origin": "https://www.flipkart.com",
                "Cache-Control": "max-age=0",
                "Service-Worker": "script",
            },
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,/;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9,ta;q=0.8",
                "Upgrade-Insecure-Requests": "1",
                "referer": "https://www.flipkart.com/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36 Edg/91.0.864.54",
                "origin": "https://www.flipkart.com",
            },
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,/;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9",
                "origin": "https://www.flipkart.com",
                "referer": "https://www.flipkart.com/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            },
        ],
    ),
    "shopatsc": Website(
        display_name="ShopAtSC",
        common_name="shopatsc",
    ),
    "reliance": Website(
        display_name="Reliance Digital",
        common_name="reliance",
    ),
    "games_the_shop": Website(
        display_name="Games the Shop",
        common_name="games_the_shop",
    ),
    "ppgc": Website(
        display_name="Prepaid Gamer Card",
        common_name="ppgc",
    ),
}
