## ***PlayStation Discord Bot***
### Functions:

* Track stock notifications (India Only)
* Create Trade Channels


### Basic Setup:
1. Obtain a Discord bot token from the [Discord developer portal](https://ptb.discord.com/developers/applications/)
2. Install all the required modules with:
```
pip install -r requirements.txt
```
3. Create a .env similiar to the .env sample.
4. Setup config.py.
5. Chrome Web Drivers for selenium will also need to be installed from [here](https://ptb.discord.com/developers/applications/) to take the screenshot of webpages.(Beta phase)

### Setup for Heroku:
1. Obtain a Discord bot token from the [Discord developer portal](https://ptb.discord.com/developers/applications/)
2. On Heroku, open your App. Click on the Settings tab and scroll down to Buildpacks.
3. If you would like to get screenshot's as well add the following buildpacks that allow us to install Chrome drivers for selenium on Heroku:(Beta phase)

```
Python (Select it from the officially supported buildpacks)
Headless Google Chrome: https://github.com/heroku/heroku-buildpack-google-chrome
Chromedriver: https://github.com/heroku/heroku-buildpack-chromedriver
```
4. Within the settings for project in Heroku, create the following `Config Vars` to configure the following: 
Note: CHROMEDRIVER_PATH and GOOGLE_CHROME_BIN are only if you are enabling selenium for web screenshots. (Beta phase)

```
DISCORD_BOT_TOKEN
CHROMEDRIVER_PATH = /app/.chromedriver/bin/chromedriver
GOOGLE_CHROME_BIN = /app/.apt/usr/bin/google-chrome
```

### Run script:

    python bot.py