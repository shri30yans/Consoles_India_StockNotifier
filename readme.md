## ***PlayStation Discord Bot***
### Functions:

* Stock notifications for PS5 (India Only) (Amazon, Flipkart, Prepaid Gamer Card,Games the Shop)
* Stock notifications for Xbox Series X and Series S (India Only) (Amazon, Flipkart)
* Create Trade Channels

### Pictures:
![PS5 Stock](https://github.com/shri30yans/PS5_DiscordBot/blob/main/Images/PS5.jpg)   
*PS5 Stock Alert* 

![XSS Stock](https://github.com/shri30yans/PS5_DiscordBot/blob/main/Images/XSS.jpg)   
*Xbox Series S Stock Alert*   
 
![Trade Channel](https://github.com/shri30yans/PS5_DiscordBot/blob/main/Images/Create_a_trade_channel.jpg)   
*Creating a Trade Channel*
     
![Instructions](https://github.com/shri30yans/PS5_DiscordBot/blob/main/Images/instructions.jpg)   
*Auto-message in Trade Channel*  



### Basic Setup:
1. Install all the required modules with:
```
pip3 install -r requirements.txt
```
2. Obtain a Discord bot token from the [Discord developer portal](https://ptb.discord.com/developers/applications/)
3. Create a .env similiar to the .env sample.
4. Setup config.py.
5. Chrome Web Drivers for selenium will also need to be installed from [here](https://www.selenium.dev/downloads/) to take the screenshot of webpages. (Beta phase)

### Setup for Heroku:
1. On Heroku, open your App. Click on the Settings tab and scroll down to Buildpacks.
2. If you would like to get screenshot's as well add the following buildpacks that allow us to install Chrome drivers for selenium on Heroku:  (Beta phase)

```
Python (Select it from the officially supported buildpacks)
Headless Google Chrome: https://github.com/heroku/heroku-buildpack-google-chrome
Chromedriver: https://github.com/heroku/heroku-buildpack-chromedriver
```
3. Obtain a Discord bot token from the [Discord developer portal](https://ptb.discord.com/developers/applications/)
4. Within the settings for project in Heroku, create the following `Config Vars` to configure the following: 
Note: CHROMEDRIVER_PATH and GOOGLE_CHROME_BIN are only if you are enabling selenium for web screenshots. (Beta phase)

```
DISCORD_BOT_TOKEN
CHROMEDRIVER_PATH = /app/.chromedriver/bin/chromedriver
GOOGLE_CHROME_BIN = /app/.apt/usr/bin/google-chrome
```

### Run script:

    python bot.py