# Slowed and Reverbed
This is a Telegram bot which transforms your `.mp3`-files in mysteriously-sounding tracks.

Users can select how much slower the resulting track will be.

The audio processing is based on [Pedalboard](https://github.com/spotify/pedalboard), and the Telegram Bots API is convenient and pythonic thanks to [pyTelegramBotAPI](https://pypi.org/project/pyTelegramBotAPI/).

# Docker
This repo is sufficient to build a Docker image of the bot. You can do this by running:

`docker build --tag <image_name> .`

And to run the image:

`docker run --mount type=volume,source=<volume_name>,destination=<mount_point> -it <image_name> <bot_token>`
