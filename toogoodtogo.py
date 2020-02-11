import os
import json
import requests
import smtplib
import random
import time
import datetime
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

        self.destination = config['destination']
        self.smtp = config['smtp']

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

        r = self.post("/api/item/v3/", data)
        return r.json()

    def available(self, items):
        for item in items['items']:
            name = item['display_name']
            price = item['item']['price']['minor_units'] / 100
            value = item['item']['value']['minor_units'] / 100
            color = "green" if item['items_available'] > 0 else "red"

            print("[+] merchant: %s%s%s" % (self.colors[color], name, self.colors['nc']))

            print("[+]   distance: %.2f km" % item['distance'])
            print("[+]   available: %d" % item['items_available'])
            print("[+]   price: %.2f € [%.2f €]" % (price, value))

            if item['items_available'] > 0:
                if not self.availables.get(name):
                    print("[+]")
                    print("[+]   == NEW ITEMS AVAILABLE ==")
                    self.notifier(item)
                    self.availables[name] = True

            else:
                if self.availables.get(name):
                    del self.availables[name]

            print("[+]")

    def notifier(self, item):
        sender = config['sender']
        name = item['display_name']
        items = item['items_available']

        message = """From: %s <%s>
        To: <%s>
        Subject: Merchant available

        Items: %d
        """ % (name, sender, self.destination, items)

        sm = smtplib.SMTP(self.smtp, 25)
        sm.sendmail(sender, [self.destination], message.encode('utf-8'))

    def watch(self):
        if self.config['accesstoken'] is None:
            self.login()
            self.save()

        while True:
            fav = self.favorite()
            self.available(fav)

            # let's pause after 21h00
            # this pause the script between 21h00 and 6h00
            now = datetime.datetime.now()
            if now.hour >= config['pause-from']:
                print("[+] waiting tomorrow (pause for %dh)" % config['pause-for'])
                time.sleep(config['pause-for'] * 60 * 60)
                print("[+] starting new day")

            # waiting next iteration
            wait = random.randrange(20, 55)
            print("[+] waiting %d seconds" % wait)
            time.sleep(wait)

        self.save()



if __name__ == '__main__':
    tgtg = TooGoodToGo()
    tgtg.watch()
