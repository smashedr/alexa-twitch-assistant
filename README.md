# Alexa Twitch

[![build status](https://git.cssnr.com/shane/alexa-twitch-assistant/badges/master/build.svg)](https://git.cssnr.com/shane/alexa-twitch-assistant/commits/master) [![coverage report](https://git.cssnr.com/shane/alexa-twitch-assistant/badges/master/coverage.svg)](https://git.cssnr.com/shane/alexa-twitch-assistant/commits/master)

Oauth endpoint for alexa-twitch-assistant.

## Overview

Amazon Alexa built-in account linking does not work with all oauth endpoints.

This endpoint negotiates the oauth with Twitch, then returns the `access_token` 
to Amazon to store with the account for use with the Skill.

### Documentation

- Alexa: https://developer.amazon.com/docs/custom-skills/link-an-alexa-user-with-a-user-in-your-system.html
- Twitch:  https://dev.twitch.tv/docs/authentication
