from time import sleep
from discord import SyncWebhook
from dotenv.parser import Error
import requests
from loguru import logger
import os
from dotenv import load_dotenv
import json

API_BASE_URL = "https://api.cloudflare.com/client/v4"


def get_zone_id(domain_name: str, session: requests.Session) -> str:
    params = {"name": domain_name, "status": "active"}
    url = f"{API_BASE_URL}/zones"

    r = session.get(url, params=params)
    return r.json()["result"][0]["id"]


def get_record_id(record_name: str, type: str, session: requests.Session, zone_id: str):
    url = f"{API_BASE_URL}/zones/{zone_id}/dns_records"
    params = {"type": type, "name": record_name}
    r = session.get(url, params=params)
    return r.json()["result"][0]["id"]


def patch_ip_content(
    new_ip: str,
    domain_name: str,
    record_name: str,
    record_type: str,
    session: requests.Session,
):
    zone_id = get_zone_id(domain_name, session)
    record_id = get_record_id(record_name, record_type, session, zone_id)
    url = f"{API_BASE_URL}/zones/{zone_id}/dns_records/{record_id}"
    payload = {"content": new_ip}

    res = session.patch(url, data=json.dumps(payload))
    res.raise_for_status()


def main():
    logger.info("Starting service...")
    try:
        load_dotenv()
    except Error:
        logger.error("Could not get .env variables")

    # Getting env variables defaulting to empty string when they don't exist
    logger.info("Trying to get .env keys...")
    IP_SERVICE_URL = os.getenv("IP_SERVICE_URL") or ""
    DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL") or ""
    USER_ID = os.getenv("USER_ID") or ""
    SLEEP_TIME = os.getenv("SLEEP_TIME") or ""
    CF_API_TOKEN = os.getenv("CF_API_TOKEN") or ""
    DOMAIN_NAME = os.getenv("DOMAIN_NAME") or ""
    RECORD_NAME = os.getenv("RECORD_NAME") or ""
    RECORD_TYPE = os.getenv("RECORD_TYPE") or ""

    logger.info("Creating http session...")
    session = requests.Session()
    session.headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "application/json",
    }

    r = session.get(IP_SERVICE_URL)
    if r.status_code != 200:
        logger.error("Request failed! status_code is ", r.status_code)
    ip = r.text
    try:
        logger.info("Patching cloudflare ip...")
        patch_ip_content(ip, DOMAIN_NAME, RECORD_NAME, RECORD_TYPE, session)
    except:
        logger.error("Could not patch ip")
    logger.info("Creating webhook...")
    webhook = SyncWebhook.from_url(DISCORD_WEBHOOK_URL, session=session)
    webhook.send(f"<@{USER_ID}> Servicio empezado, voy a notifcar todo lo que pase!")
    time_to_sleep = int(SLEEP_TIME) or 45  # default to 45 mins

    # Main loop
    try:
        while True:
            sleep(time_to_sleep * 60)  # 45 minutes
            logger.info("Trying to get an IP")
            new_r = session.get(IP_SERVICE_URL)

            if new_r.status_code != 200:
                logger.error("Request failed! status_code is ", r.status_code)
                break

            if ip == new_r.text:
                logger.info("IPv4 has not changed since last time,skipping...")
                continue

            ip = new_r.text

            logger.info("IPv4 changed! Sending info...")
            logger.info("Patching cloudflare ip with new ip...")
            webhook.send(
                f"<@{USER_ID}> mi ip ha cambiado! Mandando info a cloudflare..."
            )
            patch_ip_content(ip, DOMAIN_NAME, RECORD_TYPE, RECORD_TYPE, session)

    except KeyboardInterrupt:
        print("CTRL + C pressed. bye 👋!")


if __name__ == "__main__":
    main()
