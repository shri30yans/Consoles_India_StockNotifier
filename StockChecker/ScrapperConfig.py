import config

# PS5_wishlist = "https://www.amazon.in/hz/wishlist/ls/K5HVAMY70DJ5/?viewType=list"
# XBOX_wishlist= "https://www.amazon.in/hz/wishlist/ls/18WU5P3MXFWL0/?viewType=list"
PS5_wishlist = "https://www.amazon.in/hz/wishlist/ls/K5HVAMY70DJ5/"
XBOX_wishlist = "https://www.amazon.in/hz/wishlist/ls/18WU5P3MXFWL0/"


class Product:
    def __init__(
        self,
        name,
        display_name,
        links,
        # To show in GUI
        hidden=False,
        # For wishlists
        subproducts=None,
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
        self.hidden = hidden
        self.subproducts = subproducts

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
    "TEST": Product(
        name="Test",
        display_name="PS5",
        hidden=True,
        links={
            "amazon": "https://www.amazon.in/dp/B08FV5GC28?smid=AT95IG9ONZD7S",
            "flipkart": "https://www.flipkart.com/stop-worrying-start-living/p/itmfez44fyrr8dud",
            "shopatsc": "https://shopatsc.com/products/playstation-5-console",
            "games_the_shop": "https://www.gamestheshop.com/PlayStation-5-Console/5111",
            "ppgc": "https://prepaidgamercard.com/product/playstation-5-console-ps5/",
            "reliance": "https://www.reliancedigital.in/bajaj-gx-1-mixer-grinder/p/490743989",
        },
    ),
    "PS5": Product(
        name="PS5",
        display_name="PS5",
        links={
            "amazon": "https://www.amazon.in/dp/B09V59MD1P?smid=AT95IG9ONZD7S",
            "flipkart": "https://www.flipkart.com/sony-playstation-5-cfi-1008a01r-825-gb-astro-s-playroom/p/itma0201bdea62fa",
            "shopatsc": "https://shopatsc.com/products/playstation-5-console",
            "games_the_shop": "https://www.gamestheshop.com/PlayStation-5-Console/5111",
            "ppgc": "https://prepaidgamercard.com/product/playstation-5-console-ps5/",
            "reliance":"https://www.reliancedigital.in/sony-playstation-5-console/p/491936180"
        },
        add_to_cart_links={
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag={config.amazon_affiliate_tag}&ASIN.1=B09V59MD1P&Quantity.1=1",
            "shopatsc": f"https://shopatsc.com/cart/34169891815563:1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/dp/B09V59MD1P/?tag={config.amazon_affiliate_tag}",
        },
        wishlist=PS5_wishlist,
        notification_roles={
            config.playstation_server_id: 849606173522788352,
            config.my_server_id: 893734056720740352,
        },
        notification_channels=config.both_playstation_channels,
        twitter_hashtags="#RestockPS5India #PS5 #PS5India",
        thumbnail_link="https://i.imgur.com/pmgar66.jpg?1",
        colour=0x2100FF,
        emoji=config.PS5_emoji,
    ),
    "PS5_DE": Product(
        name="PS5_DE",
        display_name="PS5 Digital",
        links={
            "amazon": "https://www.amazon.in/dp/B09V58Q6DY?smid=AT95IG9ONZD7S",
            "flipkart": "https://www.flipkart.com/sony-playstation-5-cfi-1008b01r-825-gb-astro-s-playroom/p/itm8bf74f8d0b890?",
            "shopatsc": "https://shopatsc.com/products/playstation5-digital-edition",
            "games_the_shop": "https://www.gamestheshop.com/PlayStation-5-Digital-Edition/5112",
            "ppgc": "https://prepaidgamercard.com/product/playstation-5-digital-edition-ps5/",
            "reliance": "https://www.reliancedigital.in/sony-playstation-5-console/p/491936181",
        },
        add_to_cart_links={
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag={config.amazon_affiliate_tag}&ASIN.1=B09V58Q6DY&Quantity.1=1",
            "shopatsc": f"https://shopatsc.com/cart/34426793427083:1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/Sony-CFI-1008B01R-PlayStation-Digital-Edition/dp/B09V58Q6DY/?tag={config.amazon_affiliate_tag}"
        },
        wishlist=PS5_wishlist,
        notification_roles={
            config.playstation_server_id: 857134006243688458,
            config.my_server_id: 893734151428132894,
        },
        notification_channels=config.both_playstation_channels,
        twitter_hashtags="#RestockPS5India #PS5Digital",
        thumbnail_link="https://i.imgur.com/pmgar66.jpg?1",
        colour=0x008EFF,
        emoji=config.PS5_DE_emoji,
    ),
    "PS5_GT7_BUNDLE": Product(
        name="PS5_GT7_BUNDLE",
        display_name="PS5 & GT7 bundle",
        links={
            "amazon": "https://www.amazon.in/dp/B09YD71MZT/?smid=AT95IG9ONZD7S",
            "shopatsc": "https://shopatsc.com/collections/playstation-5/products/playstation%C2%AE5-console-with-ps5-gran-turismo-7-standard-ed",
        },
        add_to_cart_links={
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag={config.amazon_affiliate_tag}&ASIN.1=B09YD71MZT&Quantity.1=1",
            "shopatsc": f"https://shopatsc.com/cart/40186379436171:1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/dp/B09YD71MZT/?tag={config.amazon_affiliate_tag}",
        },
        wishlist= PS5_wishlist,
        notification_roles={
            config.playstation_server_id: 849606173522788352,
            config.my_server_id: 893734056720740352,
        },
        notification_channels=config.both_playstation_channels,
        twitter_hashtags="#RestockPS5India #PS5",
        thumbnail_link="https://i.imgur.com/pmgar66.jpg?1",
        colour=0x2100FF,
        emoji=config.PS5_emoji,
    ),
    # "PS5_DE_REMOTE_BUNDLE": Product(
    #     name="PS5_DE_REMOTE_BUNDLE",
    #     display_name="PS5 Digital & Media Remote bundle",
    #     links={
    #         "amazon": "https://www.amazon.in/dp/B08NTVH9VG/?smid=AT95IG9ONZD7S",
    #     },
    #     add_to_cart_links={
    #         "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag={config.amazon_affiliate_tag}&ASIN.1=B08NTVH9VG&Quantity.1=1"
    #     },
    #     affiliate_links={
    #         "amazon": f"https://www.amazon.in/gp/product/B08NTVH9VG/?tag={config.amazon_affiliate_tag}",
    #     },
    #     wishlist=PS5_wishlist,
    #     notification_roles={
    #         config.playstation_server_id: 857134006243688458,
    #         config.my_server_id: 893734151428132894,
    #     },
    #     notification_channels=config.both_playstation_channels,
    #     twitter_hashtags="#RestockPS5India #PS5",
    #     thumbnail_link="https://i.imgur.com/pmgar66.jpg?1",
    #     colour=0x2100FF,
    #     emoji=config.PS5_emoji,
    # ),
    # "PS5_DE_PULSE_BUNDLE": Product(
    #     name="PS5_DE_PULSE_BUNDLE",
    #     display_name="PS5 Digital & Pulse 3D bundle",
    #     links={
    #         "amazon": "https://www.amazon.in/dp/B08NTV1QDX/?smid=AT95IG9ONZD7S",
    #     },
    #     add_to_cart_links={
    #         "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag={config.amazon_affiliate_tag}&ASIN.1=B08NTV1QDX&Quantity.1=1"
    #     },
    #     affiliate_links={
    #         "amazon": f"https://www.amazon.in/gp/product/B08NTV1QDX/?tag={config.amazon_affiliate_tag}",
    #     },
    #     wishlist=PS5_wishlist,
    #     notification_roles={
    #         config.playstation_server_id: 857134006243688458,
    #         config.my_server_id: 893734151428132894,
    #     },
    #     notification_channels=config.both_playstation_channels,
    #     twitter_hashtags="#RestockPS5India #PS5",
    #     thumbnail_link="https://i.imgur.com/pmgar66.jpg?1",
    #     colour=0x2100FF,
    #     emoji=config.PS5_emoji,
    # ),
    # "PS5_DE_CHARGING_STATION_BUNDLE": Product(
    #     name="PS5_DE_CHARGING_STATION_BUNDLE",
    #     display_name="PS5 Digital & Charging station bundle",
    #     links={
    #         "amazon": "https://www.amazon.in/dp/B08NTVHTPT/?smid=AT95IG9ONZD7S",
    #     },
    #     add_to_cart_links={
    #         "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag={config.amazon_affiliate_tag}&ASIN.1=B08NTVHTPT&Quantity.1=1"
    #     },
    #     affiliate_links={
    #         "amazon": f"https://www.amazon.in/gp/product/B08NTVHTPT/?tag={config.amazon_affiliate_tag}",
    #     },
    #     wishlist=PS5_wishlist,
    #     notification_roles={
    #         config.playstation_server_id: 857134006243688458,
    #         config.my_server_id: 893734151428132894,
    #     },
    #     notification_channels=config.both_playstation_channels,
    #     twitter_hashtags="#RestockPS5India #PS5",
    #     thumbnail_link="https://i.imgur.com/pmgar66.jpg?1",
    #     colour=0x2100FF,
    #     emoji=config.PS5_emoji,
    # ),
    "WHITE_PULSE_3D": Product(
        name="WHITE_PULSE_3D",
        display_name="White Pulse 3D",
        links={
            "amazon": "https://www.amazon.in/dp/B08FVNCYWZ/?smid=AT95IG9ONZD7S",
        },
        add_to_cart_links={
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag={config.amazon_affiliate_tag}&ASIN.1=B08FVNCYWZ&Quantity.1=1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/gp/product/B08FVNCYWZ/?tag={config.amazon_affiliate_tag}",
        },
        wishlist=PS5_wishlist,
        notification_channels=config.both_playstation_channels,
        twitter_hashtags="#RestockPS5India #PS5",
        thumbnail_link="https://i.imgur.com/pmgar66.jpg?1",
        colour=0x2100FF,
        emoji=config.PS5_emoji,
    ),
    # "BLACK_PULSE_3D": Product(
    #     name="BLACK_PULSE_3D",
    #     display_name="Black Pulse 3D",
    #     links={
    #         "amazon": "https://www.amazon.in/dp/B08FVNCYWZ/?smid=AT95IG9ONZD7S",
    #     },
    #     add_to_cart_links={
    #         "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag={config.amazon_affiliate_tag}&ASIN.1=B08FVNCYWZ&Quantity.1=1"
    #     },
    #     affiliate_links={
    #         "amazon": f"https://www.amazon.in/gp/product/B08FVNCYWZ/?tag={config.amazon_affiliate_tag}",
    #     },
    #     wishlist=PS5_wishlist,
    #     notification_channels=config.both_playstation_channels,
    #     twitter_hashtags="#RestockPS5India #PS5",
    #     thumbnail_link="https://i.imgur.com/pmgar66.jpg?1",
    #     colour=0x2100FF,
    #     emoji=config.PS5_emoji,
    # ),
    "DS_CHARGING_STATION": Product(
        name="DS_CHARGING_STATION",
        display_name="DualSense charging station",
        links={
            "amazon": "https://www.amazon.in/dp/B08FVMT8QN/?smid=AT95IG9ONZD7S",
        },
        add_to_cart_links={
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag={config.amazon_affiliate_tag}&ASIN.1=B08FVMT8QN&Quantity.1=1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/gp/product/B08FVMT8QN/?tag={config.amazon_affiliate_tag}",
        },
        wishlist=PS5_wishlist,
        notification_channels=config.both_playstation_channels,
        twitter_hashtags="#RestockPS5India #PS5",
        thumbnail_link="https://i.imgur.com/pmgar66.jpg?1",
        colour=0x2100FF,
        emoji=config.PS5_emoji,
    ),
    "XSX": Product(
        name="XSX",
        display_name="XSX",
        links={
            "amazon": "https://www.amazon.in/Xbox-Series-X/dp/B08J7QX1N1/?smid=AT95IG9ONZD7S",
            "flipkart": "https://www.flipkart.com/microsoft-xbox-series-x-1024-gb/p/itm63ff9bd504f27",
            "ppgc": "https://prepaidgamercard.com/product/xbox-series-x/",
            "reliance": "https://www.reliancedigital.in/xbox-series-x-console-with-wireless-controller-1-tb/p/491934660",
        },
        add_to_cart_links={
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag={config.amazon_affiliate_tag}&ASIN.1=B08J7QX1N1&Quantity.1=1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/Xbox-Series-X/dp/B08J7QX1N1/?tag={config.amazon_affiliate_tag}",
        },
        wishlist=XBOX_wishlist,
        notification_roles={
            config.my_server_id: 893734236392144926,
        },
        notification_channels=config.xbox_channel,
        twitter_hashtags="#RestockXSXIndia #XSX",
        thumbnail_link="https://i.imgur.com/WpKbZXR.jpg",
        colour=0x3E8806,
        emoji=config.XSX_emoji,
    ),
    "XSX_HALO_EDITION": Product(
        name="XSX_HALO_EDITION",
        display_name="XSX Halo Edition Bundle",
        links={
            "amazon": "https://www.amazon.in/dp/B09LMY7K1L/",
            "flipkart": "https://www.flipkart.com/microsoft-xbox-series-x-1000-gb-halo-infinite-game-digital-code/p/itmc66869fa47647",
            "ppgc": "https://prepaidgamercard.com/product/xbox-series-x-halo-infinite-limited-edition-bundle/",
        },
        add_to_cart_links={
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag={config.amazon_affiliate_tag}&ASIN.1=B09LMY7K1L&Quantity.1=1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/Xbox-Series-X/dp/B09LMY7K1L/?tag={config.amazon_affiliate_tag}",
        },
        wishlist=XBOX_wishlist,
        notification_roles={
            config.my_server_id: 893734236392144926,
        },
        notification_channels=config.xbox_channel,
        twitter_hashtags="#RestockXSXIndia #XSX",
        thumbnail_link="https://i.imgur.com/WpKbZXR.jpg",
        colour=0x3E8806,
        emoji=config.XSX_emoji,
    ),
    "XSX_HALO_EDITION_CONTROLLER": Product(
        name="XSX_HALO_EDITION_CONTROLLER",
        display_name="XSX Halo Edition Elite controller",
        links={
            "amazon": "https://www.amazon.in/dp/B09LMY7K1L/",
            "flipkart": "https://www.flipkart.com/microsoft-xbox-elite-wireless-controller-series-2-halo-infinite-limited-bluetooth-gamepad/p/itm28256af2eb91a",
            "ppgc": "https://prepaidgamercard.com/product/xbox-elite-wireless-controller-series-2-halo-infinite-limited-edition/",
        },
        add_to_cart_links={
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag={config.amazon_affiliate_tag}&ASIN.1=B09LMY7K1L&Quantity.1=1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/Xbox-Series-X/dp/B09LMY7K1L/?tag={config.amazon_affiliate_tag}",
        },
        wishlist=XBOX_wishlist,
        notification_channels=config.xbox_channel,
        twitter_hashtags="#RestockXSXIndia #XboxSeriesX #XSX #Halo #",
        thumbnail_link="https://i.imgur.com/WpKbZXR.jpg",
        colour=0x3E8806,
        emoji=config.XSX_emoji,
    ),
    "XBOX_WIRELESS_HEADSET": Product(
        name="XBOX_WIRELESS_HEADSET",
        display_name="Xbox Wireless Headset",
        links={
            "amazon": "https://www.amazon.in/dp/product/B09HSHXYCR/",
            "flipkart": "https://www.flipkart.com/microsoft-xbox-wireless-bluetooth-gaming-headset/p/itm7541ed4978931",
        },
        add_to_cart_links={
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag={config.amazon_affiliate_tag}&ASIN.1=B09HSHXYCR&Quantity.1=1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/Xbox-Series-X/dp/B09HSHXYCR/?tag={config.amazon_affiliate_tag}",
        },
        wishlist=XBOX_wishlist,
        notification_channels=config.xbox_channel,
        twitter_hashtags="#RestockXSXIndia #XboxSeriesX #XSX",
        thumbnail_link="https://i.imgur.com/C4yH5JO.jpg",
        colour=0x3E8806,
        emoji=config.XSX_emoji,
    ),
    "XSX_20TH_ANNIVERSARY_EDITION_CONTROLLER": Product(
        name="XSX_20TH_ANNIVERSARY_EDITION_CONTROLLER",
        display_name="Xbox 20th Anniversary Edition Controller",
        links={
            "amazon": "https://www.amazon.in/dp/B09HTV3Q3T/",
        },
        add_to_cart_links={
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag={config.amazon_affiliate_tag}&ASIN.1=B09HTV3Q3T&Quantity.1=1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/Xbox-Series-X/dp/B09HTV3Q3T/?tag={config.amazon_affiliate_tag}",
        },
        wishlist=XBOX_wishlist,
        notification_channels=config.xbox_channel,
        twitter_hashtags="#RestockXSXIndia #XboxSeriesX #XSX",
        thumbnail_link="https://i.imgur.com/ptzXioe.jpg",
        colour=0x3E8806,
        emoji=config.XSX_emoji,
    ),
    "XSX_GEARS_TACTIC_BUNDLE": Product(
        name="XSX_GEARS_TACTIC_BUNDLE",
        display_name="XSX & Gears Tactics bundle",
        links={
            "amazon": "https://www.amazon.in/dp/B08NRLQ294/?smid=AT95IG9ONZD7S",
        },
        add_to_cart_links={
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag={config.amazon_affiliate_tag}&ASIN.1=B08NRLQ294&Quantity.1=1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/Xbox-Series-X/dp/B08NRLQ294/?tag={config.amazon_affiliate_tag}",
        },
        wishlist=XBOX_wishlist,
        notification_roles={
            config.my_server_id: 893734236392144926,
        },
        notification_channels=config.xbox_channel,
        twitter_hashtags="#RestockXSXIndia #XboxSeriesX #XSX",
        thumbnail_link="https://i.imgur.com/WpKbZXR.jpg",
        colour=0x3E8806,
        emoji=config.XSX_emoji,
    ),
    "XSX_WHITE_CONTROLLER_BUNDLE": Product(
        name="XSX_WHITE_CONTROLLER_BUNDLE",
        display_name="XSX & Robot White Controller bundle",
        links={
            "amazon": "https://www.amazon.in/dp/B08NRLS39X/?smid=AT95IG9ONZD7S",
        },
        add_to_cart_links={
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag={config.amazon_affiliate_tag}&ASIN.1=B08NRLS39X&Quantity.1=1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/Xbox-Series-X/dp/B08NRLS39X/?tag={config.amazon_affiliate_tag}",
        },
        wishlist=XBOX_wishlist,
        notification_roles={
            config.my_server_id: 893734236392144926,
        },
        notification_channels=config.xbox_channel,
        twitter_hashtags="#RestockXSXIndia #XboxSeriesX #XSX",
        thumbnail_link="https://i.imgur.com/WpKbZXR.jpg",
        colour=0x3E8806,
        emoji=config.XSX_emoji,
    ),
    "XSX_BLACK_CONTROLLER_BUNDLE": Product(
        name="XSX_BLACK_CONTROLLER_BUNDLE",
        display_name="XSX & Carbon Black Controller bundle",
        links={
            "amazon": "https://www.amazon.in/dp/B08NQZGSJ2/?smid=AT95IG9ONZD7S",
        },
        add_to_cart_links={
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag={config.amazon_affiliate_tag}&ASIN.1=B08NQZGSJ2&Quantity.1=1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/Xbox-Series-X/dp/B08NQZGSJ2/?tag={config.amazon_affiliate_tag}",
        },
        wishlist=XBOX_wishlist,
        notification_roles={
            config.my_server_id: 893734236392144926,
        },
        notification_channels=config.xbox_channel,
        twitter_hashtags="#RestockXSXIndia #XboxSeriesX #XSX",
        thumbnail_link="https://i.imgur.com/WpKbZXR.jpg",
        colour=0x3E8806,
        emoji=config.XSX_emoji,
    ),
    "XSX_BLUE_CONTROLLER_BUNDLE": Product(
        name="XSX_BLUE_CONTROLLER_BUNDLE",
        display_name="XSX & Shock Blue Controller bundle",
        links={
            "amazon": "https://www.amazon.in/dp/B08NRBNSPW/?smid=AT95IG9ONZD7S",
        },
        add_to_cart_links={
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag={config.amazon_affiliate_tag}&ASIN.1=B08NRBNSPW&Quantity.1=1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/Xbox-Series-X/dp/B08NRBNSPW/?tag={config.amazon_affiliate_tag}",
        },
        wishlist=XBOX_wishlist,
        notification_roles={
            config.my_server_id: 893734236392144926,
        },
        notification_channels=config.xbox_channel,
        twitter_hashtags="#RestockXSXIndia #XboxSeriesX #XSX",
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
        wishlist=XBOX_wishlist,
        notification_roles={
            config.my_server_id: 893734365476057119,
        },
        notification_channels=config.xbox_channel,
        twitter_hashtags="#XboxSeriesS #XSS",
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
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag={config.amazon_affiliate_tag}&ASIN.1=B098439Y2G&Quantity.1=1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/DualSense-Wireless-Controller-Red-PlayStation/dp/B098439Y2G/?tag={config.amazon_affiliate_tag}"
        },
        wishlist=PS5_wishlist,
        notification_roles={
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
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag={config.amazon_affiliate_tag}&ASIN.1=B09842ZHNM&Quantity.1=1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/DualSense-Wireless-Controller-Black-PlayStation/dp/B09842ZHNM/?tag={config.amazon_affiliate_tag}"
        },
        wishlist=PS5_wishlist,
        notification_roles={
            config.my_server_id: 893734593621000232,
        },
        notification_channels=config.playstation_channel,
        colour=0x030000,
        emoji=config.BLACK_DS_emoji,
    ),
    "PINK_DS": Product(
        name="Pink_DS",
        display_name="Pink Dualsense",
        links={
            "amazon": "https://www.amazon.in/dp/B09SM63G1L?smid=AT95IG9ONZD7S",
            "shopatsc": "https://shopatsc.com/collections/all/products/dualsense-controller-pink-rus",
        },
        add_to_cart_links={
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag={config.amazon_affiliate_tag}&ASIN.1=B09SM63G1L&Quantity.1=1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/dp/B09SM63G1L/?tag={config.amazon_affiliate_tag}"
        },
        wishlist=PS5_wishlist,
        notification_roles={
            config.my_server_id: 893734593621000232,
        },
        notification_channels=config.playstation_channel,
        colour=0x030000,
        emoji=config.BLACK_DS_emoji,
    ),
    "BLUE_DS": Product(
        name="BLUE_DS",
        display_name="Blue Dualsense",
        links={
            "amazon": "https://www.amazon.in/dp/B09SM6ML4K?smid=AT95IG9ONZD7S",
            "shopatsc": "https://shopatsc.com/collections/all/products/dualsense-controller-ice-blue-rus",
        },
        add_to_cart_links={
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag={config.amazon_affiliate_tag}&ASIN.1=B09SM6ML4K&Quantity.1=1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/dp/B09SM6ML4K/?tag={config.amazon_affiliate_tag}"
        },
        wishlist=PS5_wishlist,
        notification_roles={
            config.my_server_id: 893734593621000232,
        },
        notification_channels=config.playstation_channel,
        colour=0x030000,
        emoji=config.BLACK_DS_emoji,
    ),
    "PURPLE_DS": Product(
        name="PURPLE_DS",
        display_name="Purple Dualsense",
        links={
            "amazon": "https://www.amazon.in/dp/B09SM5NFTH?smid=AT95IG9ONZD7S",
            "shopatsc": "https://shopatsc.com/collections/all/products/dualsense-controller-purple-rus",
        },
        add_to_cart_links={
            "amazon": f"https://www.amazon.in/gp/aws/cart/add.html?AssociateTag={config.amazon_affiliate_tag}&ASIN.1=B09SM5NFTH&Quantity.1=1"
        },
        affiliate_links={
            "amazon": f"https://www.amazon.in/dp/B09SM5NFTH/?tag={config.amazon_affiliate_tag}"
        },
        wishlist=PS5_wishlist,
        notification_roles={
            config.my_server_id: 893734593621000232,
        },
        notification_channels=config.playstation_channel,
        colour=0x030000,
        emoji=config.BLACK_DS_emoji,
    ),
    
    # For the GUI
    "PS_WISHLIST": Product(
        name="PS_WISHLIST",
        display_name="Playstation Wishlist",
        hidden=True,
        subproducts=[
            "PS5",
            "PS5_DE",
            "PS5_Camera_Bundle",
            "PS5_DE_Remote_Bundle",
            "PS5_DE_Pulse_Bundle",
            "PS5_DE_Charging_Station_Bundle",
        ],
        links={
            "amazon": PS5_wishlist,
        },
        emoji=f"{config.PS5_emoji}📜",
    ),
    "XBOX_WISHLIST": Product(
        name="XBOX_WISHLIST",
        display_name="Xbox Wishlist",
        hidden=True,
        subproducts=[
            "XSX",
            "XSX_HALO_EDITION",
            "XSX_Gears_Tactics_Bundle",
            "XSX_White_Controller_Bundle",
            "XSX_Black_Controller_Bundle",
            "XSX_Blue_Controller_Bundle",
        ],
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
        name: str,
        wishlist_link: str = None,
        wishlist_products=None,
        headers: list = None,
    ):
        self.name = name
        self.display_name = display_name
        self.wishlist_link = wishlist_link
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
        name="amazon",
        wishlist_products={
            # "RED_DS": Amazon_Wishlist_Item(
            #     name="RED_DS", ASIN="B098439Y2G", max_cost=6500
            # ),
            # "BLACK_DS": Amazon_Wishlist_Item(
            #     name="BLACK_DS", ASIN="B09842ZHNM", max_cost=6000
            # ),
            "PS5": Amazon_Wishlist_Item(
                name="PS5", ASIN="B09V59MD1P"),
            "PS5_DE": Amazon_Wishlist_Item(
                name="PS5_DE", ASIN="B09V58Q6DY"
            ),
            "PS5_GT7_BUNDLE": Amazon_Wishlist_Item(
                name="PS5_GT7_BUNDLE", ASIN="B09YD71MZT"
            ),
            # "PS5_DE_REMOTE_BUNDLE": Amazon_Wishlist_Item(
            #     name="PS5_DE_REMOTE_BUNDLE", ASIN="B08NTVH9VG"
            # ),
            # "PS5_DE_PULSE_BUNDLE": Amazon_Wishlist_Item(
            #     name="PS5_DE_PULSE_BUNDLE", ASIN="B08NTV1QDX"
            # ),
            # "PS5_DE_CHARGING_STATION_BUNDLE": Amazon_Wishlist_Item(
            #     name="PS5_DE_CHARGING_STATION_BUNDLE", ASIN="B08NTVHTPT"
            # ),
            # "DS_CHARGING_STATION": Amazon_Wishlist_Item(
            #     name="DS_CHARGING_STATION", ASIN="B08FVMT8QN"
            # ),
            # "WHITE_PULSE_3D": Amazon_Wishlist_Item(
            #     name="WHITE_PULSE_3D", ASIN="B08FVNCYWZ"
            # ),
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
            ),
            "XSX_HALO_EDITION": Amazon_Wishlist_Item(
                name="XSX_HALO_EDITION",
                ASIN="B09LMY7K1L",
            ),
            "XSX_20TH_ANNIVERSARY_EDITION_CONTROLLER": Amazon_Wishlist_Item(
                name="XSX_20TH_ANNIVERSARY_EDITION_CONTROLLER",
                ASIN="B09HTV3Q3T",
            ),
            # "XBOX_WIRELESS_HEADSET": Amazon_Wishlist_Item(
            #     name="XBOX_WIRELESS_HEADSET",
            #     ASIN="B09HSHXYCR",
            # ),
            "XSX_GEARS_TACTIC_BUNDLE": Amazon_Wishlist_Item(
                name="XSX_GEARS_TACTIC_BUNDLE", ASIN="B08NRLQ294"
            ),
            "XSX_BLUE_CONTROLLER_BUNDLE": Amazon_Wishlist_Item(
                name="XSX_BLUE_CONTROLLER_BUNDLE", ASIN="B08NRBNSPW"
            ),
            "XSX_WHITE_CONTROLLER_BUNDLE": Amazon_Wishlist_Item(
                name="XSX_WHITE_CONTROLLER_BUNDLE", ASIN="B08NRLS39X"
            ),
            "XSX_BLACK_CONTROLLER_BUNDLE": Amazon_Wishlist_Item(
                name="XSX_BLACK_CONTROLLER_BUNDLE", ASIN="B08NQZGSJ2"
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
                "Referer": "https://www.amazon.in/",
                "DNT": "1",
                "Accept-Language": "en-GB,en;q=0.9",
            },
            {
                "authority": "www.amazon.in",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
                "content-type": "application/x-www-form-urlencoded",
                "accept": "text/html,*/*",
                "ect": "4g",
                "origin": "https://www.amazon.in",
                "referer": "https://www.amazon.in/",
                "DNT": "1",
                "accept-language": "en-US,en;q=0.9",
            },
        ],
    ),
    "flipkart": Website(
        display_name="Flipkart",
        name="flipkart",
        headers=[
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
                "Accept": "*/*",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
                "origin": "https://www.flipkart.com",
                "referer": "https://www.flipkart.com/",
                "accept-language": "en-IN,en;q=0.9",
                "DNT": "1",
                "Referer": "https://www.flipkart.com/",
            },
            {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
                "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36",
                "accept": "*/*",
                "referer": "https://www.flipkart.com/",
                "accept-language": "en-US,en;q=0.9",
                "origin": "https://www.flipkart.com",
                "DNT": "1",
            },
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,/;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9,ta;q=0.8",
                "referer": "https://www.google.com/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36",
                "DNT": "1",
                "origin": "https://www.flipkart.com",
            },
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,/;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9",
                "origin": "https://www.google.com",
                "referer": "https://www.flipkart.com/",
                "DNT": "1",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            },

            # Below this all random Headers are used.
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,/;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9",
                "origin": "https://www.google.com",
                "referer": "https://www.flipkart.com/",
                "DNT": "1",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36",
            }, 
            {
                'authority': 'https://www.flipkart.com/',
                'dnt': '1',
                "accept-encoding": "gzip, deflate, br",
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                "referer": "https://www.flipkart.com/",
                'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            },
            {
                'authority': 'https://www.flipkart.com/',
                'dnt': '1',
                'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/97.0.4692.84 Mobile/15E148 Safari/604.1',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                "accept-encoding": "gzip, deflate, br",
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                "referer": "https://www.google.in/",
                'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            },
            
            {
                'authority': 'https://www.flipkart.com/',
                'dnt': '1',
                'user-agent': 'Mozilla/5.0 (iPad; CPU OS 15_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/97.0.4692.84 Mobile/15E148 Safari/604.1',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                "accept-encoding": "gzip, deflate, br",
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                "referer": "https://www.google.in/",
                'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            },
            {
                'authority': 'https://www.flipkart.com/',
                'dnt': '1',
                'user-agent': 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.98 Mobile Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                "accept-encoding": "gzip, deflate, br",
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                "referer": "https://www.google.com/",
                'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            },
            {
                'authority': 'https://www.flipkart.com/',
                'dnt': '1',
                'user-agent': 'Mozilla/5.0 (Linux; Android 10; SM-N960U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.98 Mobile Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                "accept-encoding": "gzip, deflate, br",
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                "referer": "https://www.flipkart.com/",
                'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            },
            {
                'authority': 'https://www.flipkart.com/',
                'dnt': '1',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                "accept-encoding": "gzip, deflate, br",
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                "referer": "https://www.google.com/",
            },
            {
                'authority': 'https://www.flipkart.com/',
                'dnt': '1',
                'user-agent': 'Mozilla/5.0 (Linux; Android 9; SM-N950F Build/PPR1.180610.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.157 Mobile Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                "accept-encoding": "gzip, deflate, br",
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                "referer": "https://www.google.com/",
            },
            {
                'authority': 'https://www.flipkart.com/',
                'dnt': '1',
                'user-agent': 'Mozilla/5.0 (Linux; Android 7.0; SM-G610M Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/69.0.3497.100 Mobile Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                "accept-encoding": "gzip, deflate, br",
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                "referer": "https://www.google.com/",
            },
             {
                'authority': 'https://www.flipkart.com/',
                'dnt': '1',
                'user-agent': 'Mozilla/5.0 (Linux; Android 7.1.2; AFTMM Build/NS6265; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/70.0.3538.110 Mobile Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                "accept-encoding": "gzip, deflate, br",
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                "referer": "https://www.google.com/",
            },
             {
                'authority': 'https://www.flipkart.com/',
                'dnt': '1',
                'user-agent': 'Mozilla/5.0 (Linux; Android 8.0.0; SM-G930F Build/R16NW; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.157 Mobile Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                "accept-encoding": "gzip, deflate, br",
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                "referer": "https://www.google.com/",
            },
             {
                'authority': 'https://www.flipkart.com/',
                'dnt': '1',
                'user-agent': 'Mozilla/5.0 (Linux; Android 7.1.1; SM-T567V Build/NMF26X; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/70.0.3538.80 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                "accept-encoding": "gzip, deflate, br",
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                "referer": "https://www.google.com/",
            },
             {
                'authority': 'https://www.flipkart.com/',
                'dnt': '1',
                'user-agent': 'Mozilla/5.0 (Linux; Android 9; SM-N950F Build/PPR1.180610.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.157 Mobile Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                "accept-encoding": "gzip, deflate, br",
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                "referer": "https://www.google.com/",
            },
            {
                'authority': 'https://www.flipkart.com/',
                'dnt': '1',
                'user-agent': 'Mozilla/5.0 (Linux; Android 8.0.0; SM-G935F Build/R16NW; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.157 Mobile Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                "accept-encoding": "gzip, deflate, br",
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                "referer": "https://www.flipkart.com/",
            },
            {
                'authority': 'https://www.flipkart.com/',
                'dnt': '1',
                'user-agent': 'Mozilla/5.0 (Linux; Android 7.1.2; AFTMM Build/NS6265; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/70.0.3538.110 Mobile Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                "accept-encoding": "gzip, deflate, br",
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'accept-language': 'en-GB',
                "referer": "https://www.google.com/",
            },
            {
                'authority': 'https://www.flipkart.com/',
                'dnt': '1',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                "accept-encoding": "gzip, deflate, br",
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                "referer": "https://www.google.com/",
            },
            {
                'authority': 'https://www.flipkart.com/',
                'dnt': '1',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                "accept-encoding": "gzip, deflate, br",
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                "referer": "https://www.flipkart.com/",
            },
            {
                'authority': 'https://www.flipkart.com/',
                'dnt': '1',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                "accept-encoding": "gzip, deflate, br",
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'accept-language': 'en-US',
                "referer": "https://www.google.com/",
            },
        ],
    ),
    "shopatsc": Website(
        display_name="ShopAtSC",
        name="shopatsc",
    ),
    "reliance": Website(
        display_name="Reliance Digital",
        name="reliance",
    ),
    "games_the_shop": Website(
        display_name="Games the Shop",
        name="games_the_shop",
    ),
    "ppgc": Website(
        display_name="Prepaid Gamer Card",
        name="ppgc",
    ),
}
