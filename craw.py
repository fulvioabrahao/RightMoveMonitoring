import requests
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import InputMediaPhoto
# Get the bot token from an environment variable

populate_db = False

if populate_db:
    sleep_multiplier = 0.001
else:
    sleep_multiplier = 1


class CrawProperty:
    def __init__(self, db, bot):
        self.db = db
        self.scheduler = BackgroundScheduler()
        self.bot = bot

    async def start(self):
        while True:
            try:
                await self.run()
                await asyncio.sleep(60 * 30)
            except Exception as e:
                print(e)
                await asyncio.sleep(60 * 30)

    async def run(self):
        print("run CrawProperty")

        # get all monitoring from db
        monitors = self.db.monitors.find()

        for monitor in monitors:
            print(f"monitoring {monitor['location']}")

            # get properties from rightmove
            properties = self.get_properties(monitor)

            # filter properties
            properties = self.filter_properties(properties, monitor)

            # send properties to telegram
            if len(properties) > 0:
                await self.send_properties(properties, monitor)
                await asyncio.sleep(sleep_multiplier * 60)
            else:
                await asyncio.sleep(2)

    def get_properties(self, monitor):
        # get properties from rightmove
        # This is the get request we send to right move: https://www.rightmove.co.uk/api/_search?locationIdentifier=STATION%5E2252&maxBedrooms=2&minBedrooms=2&maxPrice=2500&minPrice=1750&numberOfPropertiesPerPage=24&radius=0.0&sortType=6&index=0&maxDaysSinceAdded=14&viewType=LIST&channel=RENT&areaSizeUnit=sqft&currencyCode=GBP&isFetching=false&viewport=

        # get location identifier
        location_identifier = self.get_location_identifier(monitor["location"])
        min_bedrooms = monitor["min_beds"]
        max_bedrooms = monitor["max_beds"]
        min_price = monitor["min_price"]
        max_price = monitor["max_price"]

        url = f"https://www.rightmove.co.uk/api/_search?locationIdentifier={location_identifier}&maxBedrooms={max_bedrooms}&minBedrooms={min_bedrooms}&maxPrice={max_price}&minPrice={min_price}&numberOfPropertiesPerPage=24&radius=0.0&sortType=6&index=0&maxDaysSinceAdded=14&viewType=LIST&channel=RENT&areaSizeUnit=sqft&currencyCode=GBP&isFetching=false&viewport="
        print(f"get properties from {url}")

        # get properties from rightmove
        # send a get request to rightmove using requests library
        response = requests.get(url)

        # get json from response
        json = response.json()

        # get properties from json
        properties = json["properties"]

        return properties

    def get_location_identifier(self, location):
        # hardcode location identifier for now
        ids = {
            "Colindale": "STATION%5E2252",
            "WhiteCity": "REGION%5E85399",
            "Islington": "REGION%5E93965",
            "NorthActon": "STATION%5E6704",
            "ActonMainLine": "STATION%5E74",
        }
        if location not in ids:
            raise Exception(f"location not found {location}")
        return ids[location]

    def filter_properties(self, properties, monitor):
        # find all properties from monitor with the same chat_id
        properties_from_chat = self.db.monitor_properties.find(
            {"chat_id": monitor["chat_id"]})

        properties_from_chat_prices = {}

        for property in properties_from_chat:
            properties_from_chat_prices[
                property["id"]
            ] = property["price"]["amount"]

        # filtered_properties = []
        # for property in properties:
        #     if property["id"] not in  properties_from_chat_ids:
        #         property["chat_id"] = monitor["chat_id"]
        #         filtered_properties.append(property)

        # changing a bit the logic, it should add to filtered_properties only if the property is not in the db OR if the property is in the db but the PRICE is different
        filtered_properties = []
        used_ids = set()
        for property in properties:
            if property["id"] in used_ids:
                continue

            if property["id"] not in properties_from_chat_prices:
                property["chat_id"] = monitor["chat_id"]
                property["status"] = "new_property"
                used_ids.add(property["id"])
                filtered_properties.append(property)
            elif property["id"] in properties_from_chat_prices and property["price"]["amount"] != properties_from_chat_prices[property["id"]]:
                property["chat_id"] = monitor["chat_id"]
                property["status"] = "price_changed"
                property["old_price"] = properties_from_chat_prices[property["id"]]
                used_ids.add(property["id"])
                filtered_properties.append(property)

        # return only two properties
        if populate_db:
            return filtered_properties
        return filtered_properties[:2]

    async def send_properties(self, properties, monitor):
        for property in properties:

            status = property["status"]
            if status == "new_property":
                message = f"New property found in {monitor['location']}\n"
                message += f"Price: £{property['price']['amount']}\n"
            elif status == "price_changed":
                message = f"Price changed in {monitor['location']}\n"
                message += f"Price: £{property['price']['amount']}, Old Price: £{property['old_price']}\n"

            message += f"Bedrooms: {property['bedrooms']}\n"
            message += f"Bathrooms: {property['bathrooms']}\n"
            message += f"Address: {property['displayAddress']}\n"

            message += f"Url: https://www.rightmove.co.uk/properties/{property['id']}\n"

            # send property to telegram
            if populate_db == False:
                await self.bot.send_message(
                    monitor["chat_id"], message)
            await asyncio.sleep(sleep_multiplier * 1)
            if "propertyImages" in property and "images" in property["propertyImages"] and len(property["propertyImages"]["images"]) > 0:
                urls = [image["srcUrl"]
                        for image in property["propertyImages"]["images"]]
                # limit 10 images only
                if len(urls) > 6:
                    urls = urls[:6]
                media_group = [InputMediaPhoto(media=url) for url in urls]
                if populate_db == False:
                    await self.bot.send_media_group(monitor["chat_id"], media=media_group)

            await asyncio.sleep(sleep_multiplier * 10)

            if status == "new_property":
                # save property to db
                self.db.monitor_properties.insert_one(property)
            elif status == "price_changed":
                # update property in db
                self.db.monitor_properties.update_one(
                    {"id": property["id"]}, {"$set": property})
