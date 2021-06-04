## ***PlayStation Discord Bot***
### Functions:

* Track stock notifications (India Only)
* Create Trade Channels

### Modules Installation

	pip install -r requirements.txt

### Setup:
1. Obtain a Discord bot token from the [Discord developer portal](https://ptb.discord.com/developers/applications/)
2. Within the Repository settings for your fork or repo, create the following `Secrets` to configure the permissions to be used by the GitHub Actions pipeline:

```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_REGION
DISCORD_BOT_TOKEN
```

### Run script:

    python bot.py