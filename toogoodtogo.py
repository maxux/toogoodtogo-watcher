import os
import json
import requests
import smtplib
import random
import time
import datetime
import telegram
from config import config

class TooGoodToGo:
    def __init__(self):
        self.home = os.path.expanduser("~")
        self.cfgfile = "%s/.config/tgtgw/config.json" % self.home

        # default values
        self.email = config['email']
        self.password = config['password']
        self.config = {
            'accesstoken': None,
            'refreshtoken': None,
            'userid': "",
        }

        self.availables = {}
        self.baseurl = 'https://apptoogoodtogo.com'
        self.session = requests.session()

        self.colors = {
            'red': "\033[31;1m",
            'green': "\033[32;1m",
            'nc': "\033[0m",
        }

        self.bot = telegram.Bot(token=config['telegram-token'])

        # load configuration if exists
        self.load()

    # load configuration
    def load(self):
        if not os.path.exists(self.cfgfile):
            return False

        print("[+] loading configuration: %s" % self.cfgfile)
        with open(self.cfgfile, "r") as f:
            data = f.read()

        self.config = json.loads(data)

        print("[+] access token: %s" % self.config['accesstoken'])
        print("[+] refresh token: %s" % self.config['refreshtoken'])
        print("[+] user id: %s" % self.config['userid'])

    # save configuration
    def save(self):
        basepath = os.path.dirname(self.cfgfile)
        print("[+] configuration directory: %s" % basepath)

        if not os.path.exists(basepath):
            os.makedirs(basepath)

        with open(self.cfgfile, "w") as f:
            print("[+] writing configuration: %s" % self.cfgfile)
            f.write(json.dumps(self.config))

    def url(self, endpoint):
        return "%s%s" % (self.baseurl, endpoint)

    def post(self, endpoint, json):
        headers = {
            'User-Agent': 'TGTG/19.12.0 (724) (Android/Unknown; Scale/3.00)',
            'Accept': "application/json",
            'Accept-Language': "en-US"
        }

        if self.config['accesstoken']:
            headers['Authorization'] = "Bearer %s" % self.config['accesstoken']

        return self.session.post(self.url(endpoint), headers=headers, json=json)

    def login(self):
        login = {
            'device_type': "UNKNOWN",
            'email': self.email,
            'password': self.password
        }

        r = self.post("/api/auth/v1/loginByEmail", login)
        data = r.json()

        self.config['accesstoken'] = data['access_token']
        self.config['refreshtoken'] = data['refresh_token']
        self.config['userid'] = data['startup_data']['user']['user_id']

        return True

    def refresh(self):
        data = {'refresh_token': self.config['refreshtoken']}
        ref = self.post('/api/auth/v1/token/refresh', data)

        payload = ref.json()
        self.config['accesstoken'] = payload['access_token']

        print("[+] new token: %s" % self.config['accesstoken'])

        return True

    def favorite(self):
        data = {
            'favorites_only': True,
            'origin': {
                'latitude': config['latitude'],
                'longitude': config['longitude']
            },
            'radius': 200,
            'user_id': self.config['userid']
        }

        while True:
            r = self.post("/api/item/v3/", data)
            if r.status_code == 502:
                continue

            if r.status_code == 200:
                return r.json()

            try:
                r.json()

            except Exception as e:
                print(r.text)
                print(e)

            return r.json()

    def datetimeparse(self, datestr):
        fmt = "%Y-%m-%dT%H:%M:%SZ"
        value = datetime.datetime.strptime(datestr, fmt)
        return value.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)

    def issameday(self, d1, d2):
        return (d1.day == d2.day and d1.month == d2.month and d1.year == d2.year)

    def pickupdate(self, item):
        now = datetime.datetime.now()
        pfrom = self.datetimeparse(item['pickup_interval']['start'])
        pto = self.datetimeparse(item['pickup_interval']['end'])

        prange = "%02d:%02d - %02d:%02d" % (pfrom.hour, pfrom.minute, pto.hour, pto.minute)

        if self.issameday(pfrom, now):
            return "Today, %s" % prange

        return "%d/%d, %s" % (pfrom.day, pfrom.month, prange)


    def available(self, items):
        for item in items['items']:
            name = item['display_name']
            price = item['item']['price']['minor_units'] / 100
            value = item['item']['value']['minor_units'] / 100
            color = "green" if item['items_available'] > 0 else "red"
            kname = "%s-%.2d" % (name, price)

            print("[+] merchant: %s%s%s" % (self.colors[color], name, self.colors['nc']))

            if item['items_available'] == 0:
                if self.availables.get(kname):
                    del self.availables[kname]

                continue

            print("[+]   distance: %.2f km" % item['distance'])
            print("[+]   available: %d" % item['items_available'])
            print("[+]   price: %.2f € [%.2f €]" % (price, value))
            print("[+]   address: %s" % item['pickup_location']['address']['address_line'])
            print("[+]   pickup: %s" % self.pickupdate(item))

            if not self.availables.get(kname):
                print("[+]")
                print("[+]   == NEW ITEMS AVAILABLE ==")
                self.notifier(item)
                self.availables[kname] = True


            print("[+]")

    def notifier(self, item):
        name = item['display_name']
        items = item['items_available']
        price = item['item']['price']['minor_units'] / 100
        pickup = self.pickupdate(item)

        fmt = telegram.ParseMode.MARKDOWN
        message = "*%s*\n*Available*: %d\n*Price*: %.2f €\n*Pickup*: %s" % (name, items, price, pickup)

        self.bot.send_message(chat_id=config['telegram-chat-id'], text=message, parse_mode=fmt)

    def daytime(self):
        now = datetime.datetime.now()
        nowint = (now.hour * 100) + now.minute
        return nowint

    def watch(self):
        if self.config['accesstoken'] is None:
            self.login()
            self.save()

        while True:
            fav = self.favorite()
            self.available(fav)

            #
            # night pause
            #
            now = self.daytime()

            if now >= config['night-pause-from'] or now <= config['night-pause-to']:
                print("[+] night mode enabled, fetching disabled")

                while now >= config['night-pause-from'] or now <= config['night-pause-to']:
                    now = self.daytime()
                    time.sleep(60)

                print("[+] starting new day")

            #
            # speedup or normal waiting time
            #
            waitfrom = config['normal-wait-from']
            waitto = config['normal-wait-to']

            if now >= config['speedup-time-from'] and now <= config['speedup-time-to']:
                print("[+] speedup time range enabled")
                waitfrom = config['speedup-wait-from']
                waitto = config['speedup-wait-to']

            #
            # next iteration
            #
            wait = random.randrange(waitfrom, waitto)
            print("[+] waiting %d seconds" % wait)
            time.sleep(wait)

        self.save()

if __name__ == '__main__':
    tgtg = TooGoodToGo()
    tgtg.watch()
