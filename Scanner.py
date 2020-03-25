#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Standard Import Libraries
import re
import os
import sys
import time
import datetime
import requests
import json
import threading
import traceback
import queue
# import uuid # To be used eventually

# Slack and Flask Import Libraries
from slackclient import SlackClient
from flask import Flask, request, jsonify, make_response, Response
# from flask import Flask, request, make_response, redirect, url_for

# Start Flask app
app = Flask(__name__)

class DbManage(threading.Thread):
    """
    """
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        pass

class Message:
    """docstring for Message."""
    def __init__(self, msg, message_type='raid', box=None):
        idk_url = "https://s3-us-west-2.amazonaws.com/slack-files2/bot_icons/2019-04-07/602962075476_48.png"
        self.emoji_list      = [':crescent_moon:',':question:',":heavy_check_mark:",":sunny:",":cloud:",":rain_cloud:",":snow_cloud:"]
        # self.id              = str(uuid.uuid4()) # To be used eventually
        self.ts              = msg['ts']
        self.username        = msg['username']
        self.icon_url        = msg['icons']['image_48']
        self.title_link      = msg['attachments'][0]['title_link']
        self.color           = msg['attachments'][0]['color']

        # self.callback_id     = msg['attachments'][0]['callback_id']
        # self.text            = msg['attachments'][0]['text']
        # self.title           = msg['attachments'][0]['title']
        
        self.lat, self.lon   = self.getLatLon(self.title_link)
        self.box = box 

        self.maps_zoom = 14
        self.maps_size = 200

        if message_type == 'mon':
            self.attachment = self.setup_wild_mon(msg)
        else:
            self.attachment = self.setup_raid_boss(msg)


    def setup_wild_mon(self, msg):
        self.callback_id = 'pokemon_sighting'
        self.username, trash = self.username.split(" - ")
        text = msg['attachments'][0]['text']
        text = text.replace("DSP", "Despawn")
        text = self.delete_emoji_mons(text)
        title = self.remove_parentheses(msg['attachments'][0]['title'])
        attachment = [
                {
                    "title": title,
                    "title_link": self.title_link,
                    "text": text,
                    "fallback": title,
                    "callback_id": "mon_post",
                    "color": self.color,
                    "image_url": self.get_maps_image(),
                    "attachment_type": "default"

                }
            ]
        return attachment

    def setup_raid_boss(self, msg):
        self.callback_id = 'raid_sighting'
        text = self.remove_parentheses(msg['attachments'][0]['text'])
        split_text = text.split('\n')
        if 'hatches' not in text.lower():
            del split_text[0]
        title = self.remove_parentheses(msg['attachments'][0]['title'])
        title, EX = self.handle_ex_raids(title)
        title = '*Location: *<{}|{}>'.format(self.title_link, title)
        text = title + EX +'\n' + '\n'.join(split_text)
        attachment = [
                {
                    "text": text,
                    "fallback": self.username,
                    "callback_id": "raid_post",
                    "color": self.color,
                    "image_url": self.get_maps_image(),
                    "attachment_type": "default"

                }
            ]
        return attachment

    def delete_emoji_mons(self, my_string):
        for emoji in self.emoji_list:
            my_string = my_string.replace(emoji, "")
        return my_string

    def get_info_str(self):
        return f"{self.username} {self.title_link} {self.icon_url} {self.color} {self.lat} {self.lon}\n"
    
    def is_in_box(self, boxes):
        for box in boxes:
            if box['min_lat'] <= self.lat <= box['max_lat'] and box['min_lon'] <= self.lon <= box['max_lon']:
                return True # Indicates that lat/lon is inside of one of the boxes
        return False # Not in any of the boxes

    def is_valid(self):
        """
        If message details are NOT in SQL server, uploads, otherwise returns False.
        Also checks if the scanned object is within the set criteria (lat/lon etc.)
        """
        
        # Do something here with max/min lat/lon
        if self.box is None or not self.is_in_box(self.box):
            return False

        if logger_type == 'sql':
            # Do Some sort of sql thingy
            pass
        else:
            info_str = self.get_info_str()
            with open("logfile.txt", 'r') as f:
                f = f.readlines()
            if info_str in f:
                # print("File is present. Skipping.")
                return False
            else:
                with open("logfile.txt", 'a+') as f:
                    f.write(info_str)
                return True

    def print_to_console(self, channel=""): #insert channel
        print(f"""
as_user = False
username = {self.username}
icon_url = {self.icon_url}
attachments =  {self.attachment}

""")

    def remove_parentheses(self, my_string):
        return re.sub(r'\([^)]*\)', '', my_string)

    def delete_emoji_raids(self, my_string):
        return re.sub(r'\:[^)]*\:', '', my_string)

    def handle_ex_raids(self, my_string): 
        out = re.sub(r'\:[^)]*\:', '', my_string)
        if len(out) != len(my_string):
            return out, '\n`EX RAID LOCATION`'
        else:
            return my_string, ""

    def getLatLon(self, link):
        link = link.replace('http://maps.google.com/maps?q=','')
        link,trash = link.split('&')
        lat,lon = link.split(',')
        lat = float(lat)
        lon = float(lon)
        return lat, lon

    def get_maps_image(self):
        maps_url =   'https://maps.googleapis.com/maps/api/staticmap?zoom='
        maps_url += f'{self.maps_zoom}&size={self.maps_size}x{self.maps_size}'
        maps_url += f'&maptype=roadmap&markers=color:red%7C{self.lat}+{self.lon}&key={maps_api_key}'
        return maps_url

    # def send_message(message, print_msg=False):
    #     if print_msg:
    #         print(message)
    # 	slack_client.api_call(
    #         "chat.postMessage",
    # 		channel="U4JUUTUBT",#CHANNEL_NAME,
    #                 text=message)

class Scanner(object):
    """
    A class built to scan one Slack team and forward specific messages to another.
    
    This was designed specifically for a Pokemon Go Slack team who is wanting publicly
    accesible data forwarded from another team to their channels.
    
    API tokens are required to interact with the python SlackClient framework and this 
    requires a Slack App. the rtm_connect() method allows for the constant scanning of
    channels in real time, but we cannot use this because we are not able to generate
    the appropriate API tokens to utilize this method.

    Since we are not granted API tokens for the other team, I am using the web browser's
    token and cookies from the team to be scanned and am spamming the "conversations.history" 
    API method (and get a success response) without generating a valid token. This is 
    not nearly as effective as the rtm_connect() method, but it has shown less errors
    and issues with the socket connection failing. Furthermore, due to the Tier 4 rate
    limiting of the "conversations.history" method, we can run multiple channels using
    multithreading to scan any channel we desire to. The `Message' class is required
    for this to work; however, the one presented in this program has been specified
    to work exactly with the team we are scanning as we are making some serious changes
    to the messages before posting them to our channel. Modification should be made as
    needed to accomodate for other messages that are being scanned and reposted.

    According to Slack customer support, this should not be possible ;)
    """
    def __init__(self, queue=None, maps_api_key=None, cookies=None, scanner=None, sc=None, post_token=None, DEBUG=False):
        """
        ESSENTIAL SETUP -- If parameters are not provided, the program will exit
        """
        if queue is not None:
            self.queue = queue
        else:
            self.KILL("FATAL: No queue provided. Threading is impossible without this!!!")

        if maps_api_key is not None:
            self.maps_api_key = maps_api_key
        else:
            self.KILL("FATAL: No Google Maps API Key provided. Maps are impossible without this!!!")

        if cookies is not None:
            self.cookies = cookies
        else:
            self.KILL("FATAL: No cookies provided. Scanning is impossible without this!!!")

        if scanner is not None:
            self.scanner = scanner
        else:
            self.KILL("FATAL: No Scanner Token  provided. Scanning is impossible without this!!!")

        if post_token is not None:
            self.post_token = post_token
        else:
            self.KILL("FATAL: No Post Token provided. Posting messages is impossible without this!!!")

        if sc is not None:
            self.sc = sc
        else:
            self.KILL("No SlackClient posting object provided. Impossible to send messages without this !!!")

        self.DEBUG = DEBUG
        self.buffer = 1 # Buffer for scanning when initializing (in seconds)
        self.delay = .1 # Sleep Timer
        self.scanner_threads = 0
        self.ignore_batch = True # Sets to throw away the first batch from the scanner
        self.scanner_start = time.ctime()
        self.status = f"Status: `Setting Up`\nStarted: `{self.scanner_start}`\nLast Scan: `None`"
        self.channel_id_list = []
        self.post_channel_id_list = []
        self.channel_name_list = []
        self.post_channel_name_list = []
        self.scan_type_dict = {}
        self.scan_box_dict = {}
        self.data = {}
        self.update_queue()

    def mk(self, msg, markup_type):
        """
        Handles Slack markups for some pretty text formatting
        """
        markup_type = markup_type.lower()
        if markup_type in ['bold', 'b']:
            return f"*{msg}*"
        elif markup_type in ['code', 'c']:
            return f"`{msg}`"
        elif markup_type in ['underline', 'u']:
            return f"_{msg}_"
        elif markup_type in ['strikethrough', 's']:
            return f"~{msg}~"
        else:
            return msg

    def update_queue(self):
        while self.get_queue() != []:
            self.queue.get()
        self.queue.put(self.status)

    def get_queue(self):
        return list(self.queue.queue)

    def add_scan_channel(self, channel, post_channel, scan_type, scan_box):
        """
        Requires the channel being scanned and the channel you are posting to
        along with scan_type to identify which api token to use.
        """
        # if self.data == {}:
        #     idx = 1
        # else:
        #     idx = int(max(self.data)) + 1
        
        channel_name = self.get_channel_name(channel, token_type='scan')
        post_channel_name = self.get_channel_name(post_channel, token_type='post')

        # if channel in self.data:
        #     self.data[channel]["post_to_id"].append(post_channel)
        #     self.data[channel]["post_to_name"].append(post_channel_name)
        #     self.data[channel]["box"].append(scan_box)

        # else:
        #     self.data[channel] = {
        #         "channel_name": channel_name,
        #         "post_to_id": [post_channel],
        #         "post_to_name": [post_channel_name],
        #         "box": [scan_box]
        #     }

        self.channel_id_list.append(channel)
        self.post_channel_id_list.append(post_channel)

        self.channel_name_list.append(channel_name)
        self.post_channel_name_list.append(post_channel_name)

        self.scan_type_dict[channel] = scan_type
        self.scan_box_dict[channel] = scan_box

    def update_status(self, last_scan, status="Running"):
        # Not using `mk' as it would make this look pretty nasty
        channel_map = self.get_channel_map_str(join_type="\n")
        self.status = f"""
*Status:* `{status}`
*Started:* `{self.scanner_start}`
*Last Scan:* `{last_scan}`
*Scanning Instances*: `{self.scanner_threads}`
*Channels Scanned*
{channel_map}
        """

    def get_channel_name(self, channel, token_type='scan'):
        url = self.build_url(method="conversations.info", channel=channel, token_type=token_type)
        r = self.make_request(url)
        name = r['channel']['name']
        return name

    def get_channel_map_str(self, join_type=" "):
        channel_map = self.get_channel_map()
        out = []
        for key, value in channel_map.items():
            out.append(f"{self.mk(key, 'c')}->{self.mk(value, 'c')}")
        return join_type.join(out)

    def get_channel_map(self, names=True):
        """
        Returns Dict of {"scan_channel": "post_channel"}
        """
        # for channel, data in self.data.items():
        #     channel_name  = data["channel_name"]
        #     post_to_ids   = " ".join(data["post_to_id"])
        #     post_to_names = " ".join(data["post_to_name"])

        if names:
            return dict(zip(self.channel_name_list, self.post_channel_name_list))
        else:
            return dict(zip(self.channel_id_list, self.post_channel_id_list))

    def start(self):
        counter = 0 
        channel_dict = self.get_channel_map(names=False)
        for scan_channel, post_channel in channel_dict.items():
            counter += 1
            scan_type = self.scan_type_dict[scan_channel]
            scan_box = self.scan_box_dict[scan_channel]
            print(f"Thread {counter}: Starting Scanning {scan_channel}->{post_channel} for `{scan_type}' ...", end=" ")
            thread = threading.Thread(target=self.main, args=(scan_channel, post_channel, scan_type, scan_box))
            thread.start()
            print(f"Thread {counter} Started!")

        self.scanner_threads = counter

    def main(self, scan_channel, post_channel, scan_type, scan_box):
        ts = time.time()
        ts_old = ts - self.buffer # Sets buffer when initializing

        while True:
            request_url = self.build_url(ts=ts, ts_old=ts_old, channel=scan_channel)
            response = self.make_request(request_url)
            
            for message in response['messages']:
                if 'bot_id' and 'subtype' and 'attachments' not in message:
                    continue
                else:
                    message = Message(message, message_type=scan_type, box=scan_box)
                    if message.is_valid():
                        if self.DEBUG:
                            message.print_to_console()
                        elif self.ignore_batch:
                            # print('Ignoring Batch')
                            pass
                        else:
                            self.postToSlack(message, channel=post_channel)
            time.sleep(self.delay)
            self.ignore_batch = False 

    def postToSlack(self, message, channel='G6DLY0GDA'):
        r = self.sc.api_call(
            "chat.postMessage",
            channel     = channel,
            attachments = message.attachment,
            as_user     = False,
            username    = message.username,
            icon_url    = message.icon_url)

    def build_url(self, method="conversations.history", ts=None, ts_old=None, channel=None, token_type='scan'):
        """
        It's important to set the latest and oldest timestamp as we will extract them both later
        """
        if token_type == 'post':
            token = self.post_token
        else:
            token = self.scanner

        if method == "conversations.history":
            ts = time.time() if ts is  None else ts
            ts_old = ts_old if ts_old is not None else ts - 1 # or self.delay
            self.update_status(time.ctime())
            self.update_queue()
            return f"https://slack.com/api/{method}?token={token}&channel={channel}&latest={ts}$oldest={ts_old}"
        
        elif method == "conversations.info":
            return f"https://slack.com/api/{method}?token={token}&channel={channel}"

    def make_request(self, request_url, request_type='GET'):
        """
        Setup to be able to be used by multiple threads while still containing
        important information to all 
        """
        if request_type == "GET":
            r = requests.get(request_url, cookies={"cookies": self.cookies})
        elif request_type == "POST":
            r = requests.post(request_url, cookies={"cookies": self.cookies})

        r = r.json()

        if r['ok']: 
            return r
        else:
            error = r['error']
            error_msg = f"Request was denied with error message {error}.\nRequest URL: {request_url}\nFull Error Message:\n{r}"
            self.KILL(error_msg)

    def KILL(self, error): # DONE
        # Send Message alerting of failure to Slack
        # SLACK NOT SET UP YET
        print(error)
        os._exit(1) # Kill all threads, print failure to terminal output
            
class WebServer(threading.Thread): # THIS CLASS HAS NOT BEEN STARTED
    """
    WebServer is the flask app for managing slack buttons and other
    interactive components.
    """
    def __init__(self, queue=None, verify_token=None):
        WebServer.queue = queue
        WebServer.verify_token = verify_token

        if WebServer.queue is None:
            WebServer.KILL("No queue provided. Interactivity is impossible without this queue!!!")

        threading.Thread.__init__(self)
    @app.route('/') # Done
    def index():
        return ""

    @app.route('/status', methods=['POST', 'GET']) # Done
    def status():
        status = WebServer.queue.get()
        # status = list(scanner_queue.queue)
        print(status)

        form = request.form.to_dict()
        token, team_id, channel_id, user_id, text, response_url, trigger_id = process_request(form)
        # print(token, team_id, channel_id, user_id, text, response_url, trigger_id, sep="\n")
        if 'public' == text.lower():
            status = f"<@{user_id}> Shared the Scanner Status using `/scanner_status {text}`\n{status}"
            sc_posting.api_call(
            "chat.postMessage",
            text=status,
            channel=channel_id)
        else:
            sc_posting.api_call(
                "chat.postEphemeral",
                text=status,
                channel=channel_id,
                user=user_id)
        return make_response("", 200)

    @app.route('/button') # Not Started
    def button():
        """
        Module for handling interactive requests
        Not started yet
        """
        form = request.form.to_dict()
        token, team_id, channel_id, user_id, text, response_url, trigger_id = process_request(form)
        return ""

    @app.route('/nuke') # Not Started
    def nuke():
        """
        Module for handling file deleting files.
        Not started yet
        """
        form = request.form.to_dict()
        token, team_id, channel_id, user_id, text, response_url, trigger_id = process_request(form)
        if verify(user_id):
            pass
        return ""

    @app.route('/slash_1') # Not Started
    def slash_1():
        """
        Module for handling an undefined slash command
        Not started yet
        """
        form = request.form.to_dict()
        token, team_id, channel_id, user_id, text, response_url, trigger_id = process_request(form)
        return ""

    @app.route('/slash_2') # Not Started
    def slash_2():
        """
        Module for handling an undefined slash command
        Not started yet
        """
        form = request.form.to_dict()
        token, team_id, channel_id, user_id, text, response_url, trigger_id = process_request(form)
        return ""

    @app.route('/slash_3') # Not Started
    def slash_3():
        """
        Module for handling an undefined slash command
        Not started yet
        """
        form = request.form.to_dict()
        token, team_id, channel_id, user_id, text, response_url, trigger_id = process_request(form)
        return ""

    @app.route('/slash_4') # Not Started
    def slash_4():
        """
        Module for handling an undefined slash command
        Not started yet
        """
        form = request.form.to_dict()
        token, team_id, channel_id, user_id, text, response_url, trigger_id = process_request(form)
        return ""

    @app.route('/slash_5') # Not Started
    def slash_5():
        """
        Module for handling an undefined slash command
        Not started yet
        """
        form = request.form.to_dict()
        token, team_id, channel_id, user_id, text, response_url, trigger_id = process_request(form)
        return ""

    @app.route('/slash_6') # Not Started
    def slash_6():
        """
        Module for handling an undefined slash command
        Not started yet
        """
        form = request.form.to_dict()
        token, team_id, channel_id, user_id, text, response_url, trigger_id = process_request(form)
        return ""

    def run(self):
        app.run(host='0.0.0.0', port=server_port)

    def KILL(self, error):
        # Send Message alerting of failure to Slack
        print(error)
        os._exit(1) # Kill all threads, print failure to terminal output


######################
# Valid Modules Only #
######################

def get_token(token_file): # DONE
    token_file = os.path.join(os.path.expanduser("~"), ".scanner", token_file)
    with open(token_file , 'r') as f:
        return(f.readline().replace("\n","").strip())

def verify(user): # functional method
    if user in AUTHED_USER_LIST:
        return True
    else:
        return False

def process_request(info):
    # user_name    = info['user_name']
    token        = info['token']
    team_id      = info['team_id']
    channel_id   = info['channel_id']
    user_id      = info['user_id']
    text         = info['text'].strip()
    response_url = info['response_url']
    trigger_id   = info['trigger_id']
    return token, team_id, channel_id, user_id, text, response_url, trigger_id

######################

global server_port, AUTHED_USER_LIST, maps_api_key, DEBUG, logger_type
db               = "pogo"
db_table         = ""
db_user          = ""
db_pass          = ""
scanner_queue    = queue.Queue()
server_port      = 8080
AUTHED_USER_LIST = [] # INSERT USERS HERE 
maps_api_key     = get_token(".MAPS_API")
cookies          = get_token(".COOKIES")
scanner_token    = get_token(".SCAN_TOKEN")
post_token       = get_token(".POST_TOKEN")
verify_token     = get_token(".VERIFICATION_TOKEN")
sc_posting       = SlackClient(post_token)
# scanner_map      = {
#     "C95PNBBQA" : {
#         "post_to": "C949PBR46",
#         "type": "raid"
#     },
#     "CBJRLE45U" : {
#         "post_to": "G6DLY0GDA",
#         "type": "mon"
#     }
# }
scanner_map      = {
    # 1 : { #NORTH-RAIDS
    #     "scan_channel": "C95PNBBQA",
    #     "post_to": "CUSDADQCD",
    #     "type": "raid",
    #     "box": [{
    #             "max_lat":  40.4318390,
    #             "min_lat":  40.3118490,
    #             "max_lon": -111.643005,
    #             "min_lon": -111.865929 
    #             }]
    # },
    2 : { #SOUTH-RAIDS
        "scan_channel": "C95PNBBQA",
        "post_to": "CUSDBCG1K",
        "type": "raid",
        "box": [{
                "max_lat":  40.3118490,
                "min_lat":  40.1600000,
                "max_lon": -111.587037,
                "min_lon": -111.754051 
                }]
    },
    # 3 : { #NORTH-MONS
    #     "scan_channel": "CBJRLE45U",
    #     "post_to": "CUSDADQCD",
    #     "type": "mon",
    #     "box": [{
    #             "max_lat":  40.4318390,
    #             "min_lat":  40.3118490,
    #             "max_lon": -111.643005,
    #             "min_lon": -111.865929 
    #             }]
    # },
    # 4 : { #SOUTH-MONS
    #     "scan_channel": "CBJRLE45U",
    #     "post_to": "CUSDBCG1K",
    #     "type": "mon",
    #     "box": [{
    #             "max_lat":  40.3118490,
    #             "min_lat":  40.1600000,
    #             "max_lon": -111.587037,
    #             "min_lon": -111.754051 
    #             }]
    # }
    4 : { #SOUTH-MONS-INTO-PG
        "scan_channel": "CBJRLE45U",
        "post_to": "CUSDBCG1K",
        "type": "mon",
        "box": [{
                "max_lat":  40.3912200,
                "min_lat":  40.1600000,
                "max_lon": -111.587037,
                "min_lon": -111.807367
                }]
    }
}
# TODO! 

DEBUG       = False
logger_type = 'txt'

if __name__ == "__main__":
    print("Starting Flask Webserver ...", end=" ")
    Webserver = WebServer(queue=scanner_queue, verify_token=verify_token)
    Webserver.setDaemon(True)
    Webserver.start()
    time.sleep(3) # Allows time for Webserver to start
    print("Webserver Started!\n")

    if logger_type.lower() == 'sql':
        print("Starting SQL DB Manager ...", end=" ")
        DB = DbManage() # Add Args
        DB.setDaemon(True)
        DB.start()
        print("SQL DB Manager Started!\n")

    print("Setting Up Scanner ...", end=" ")
    Scan = Scanner(
        queue=scanner_queue, 
        maps_api_key=maps_api_key,
        cookies=cookies,
        scanner=scanner_token,
        sc=sc_posting,
        post_token=post_token,
        DEBUG=DEBUG
    )
    print("Set Up Complete!\n")

    for key, info in scanner_map.items():
        scan_channel = info['scan_channel']
        post_channel = info['post_to']
        scan_type    = info['type']
        scan_box     = info['box']
        print(f"Adding Scan Channel {scan_channel}->{post_channel} with type {scan_type} ...", end=" ")
        Scan.add_scan_channel(scan_channel, post_channel, scan_type, scan_box)
        print("Added!")

    print("\nStarting Scanner ...")
    Scan.start()
    print("Scanner Started!")

