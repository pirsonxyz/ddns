from time import sleep
from discord import SyncWebhook
from dotenv.parser import Error
import requests
from loguru import logger
import os
from dotenv import load_dotenv

def main():
    logger.info("Starting service...")
    try:
        load_dotenv()
    except Error:
        logger.error("Could not get .env variables")

    # Getting env variables defaulting to empty string when they don't exist
    IP_SERVICE_URL = os.getenv("IP_SERVICE_URL") or "" 
    DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL") or ""
    USER_ID = os.getenv("USER_ID") or ""
    SLEEP_TIME = os.getenv("SLEEP_TIME") or ""

    session = requests.Session()

    r = session.get(IP_SERVICE_URL)
    if (r.status_code != 200):
        logger.error("Request failed! status_code is ", r.status_code)
    ip = r.text

    logger.info("Creating webhook...")
    webhook = SyncWebhook.from_url(DISCORD_WEBHOOK_URL, session=session)
    webhook.send(f'<@{USER_ID}> mi ip es {ip}!')
    time_to_sleep = int(SLEEP_TIME) or 45 # default to 45 mins

    # Main loop
    try:
       while True:
            sleep(time_to_sleep) #45 minutes
            logger.info("Trying to get an IP")
            new_r = session.get(IP_SERVICE_URL)

            if (new_r.status_code != 200):
                logger.error("Request failed! status_code is ", r.status_code)
                break;
        
            if (ip == new_r.text):
                logger.info("IPv4 has not changed since last time,skipping...")
                continue
            
            ip = new_r.text

            logger.info("IPv4 changed! Sending info...")
            webhook.send(f'<@661316187845558313> mi ip es {ip}!')
            
    except KeyboardInterrupt:
        print("CTRL + C pressed. bye 👋!")
    

if __name__ == "__main__":
    main()
