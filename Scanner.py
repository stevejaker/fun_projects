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
import uuid
# import math

# Slack and Flask Import Libraries
from slackclient import SlackClient
from flask import Flask, request, jsonify, make_response, Response
# from flask import Flask, request, make_response, redirect, url_for

# Personal Import Libraries
# from mytime import mytime # Maybe not needed

# Start Flask app
app = Flask(__name__)

class Message:
    """docstring for Message."""
    def __init__(self, msg, message_type='raid'):
        self.emoji_list      = [':crescent_moon:',':question:',":heavy_check_mark:",":sunny:",":cloud:",":rain_cloud:",":snow_cloud:"]
        self.id              = str(uuid.uuid4())
        self.ts              = msg['ts']
        self.username        = msg['username']
        self.icon_url        = msg['icons']['image_48']
        self.title_link      = msg['attachments'][0]['title_link']
        self.color           = msg['attachments'][0]['color']

        # self.callback_id     = msg['attachments'][0]['callback_id']
        # self.text            = msg['attachments'][0]['text']
        # self.title           = msg['attachments'][0]['title']
        
        self.lat, self.lon   = self.getLatLon(self.title_link)

        # Control Info
        self.max_lat   = None # FIXME: ADD CORRECT LAT
        self.min_lat   = None # FIXME: ADD CORRECT LAT
        self.max_lon   = None # FIXME: ADD CORRECT LON
        self.min_lon   = None # FIXME: ADD CORRECT LON
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

    def is_valid(self):
        """
        If message details are NOT in SQL server, uploads, otherwise returns False.
        Also checks if the scanned object is within the set criteria (lat/lon etc.)
        """
        
        # Do something here with max/min lat/lon
        info_str = self.get_info_str()
        if logger_type == 'sql':
            # Do Some sort of sql thingy
            pass
        else:
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
    #     del slack_client

class Scanner(object):
    """docstring for Scanner."""
    def __init__(self, queue=None, maps_api_key=None, cookies=None, scanner=None, sc=None, post_token=None):
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
            self.KILL("No SlackClient posting object provided. Impossible to send messages withoutthis !!!")

        self.buffer = 1 # Buffer for scanning when initializing (in seconds)
        self.delay = .1 # Sleep Timer
        self.scanner_threads = 0
        self.scanner_start = time.ctime()
        self.status = f"Status: Setting Up\nStarted: {self.scanner_start}\nLast Scan: None"
        self.channel_id_list = []
        self.post_channel_id_list = []
        self.channel_name_list = []
        self.post_channel_name_list = []
        self.scan_type_dict = {}
        self.update_queue

    def mk(self, msg, markup_type):
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

    def add_scan_channel(self, channel, post_channel, scan_type):
        """
        Requires the channel being scanned and the channel being posted to
        """
        channel_name = self.get_channel_name(channel, token_type='scan')
        post_channel_name = self.get_channel_name(post_channel, token_type='post')

        self.channel_id_list.append(channel)
        self.post_channel_id_list.append(post_channel)

        self.channel_name_list.append(channel_name)
        self.post_channel_name_list.append(post_channel_name)

        self.scan_type_dict[channel] = scan_type

    def update_status(self, last_scan, status="Running"):
        # Not using `mk' as it would make this look pretty nasty
        self.status = f"""
*Status:* `{status}`
*Started:* `{self.scanner_start}`
*Last Scan:* `{last_scan}`
*Scanning Instances*: `{self.scanner_threads}`
*Channels Scanned:* {self.get_channel_map_str()}
        """

    def get_channel_name(self, channel, token_type='scan'):
        url = self.build_url(method="conversations.info", channel=channel, token_type=token_type)
        r = self.make_request(url)
        name = r['channel']['name']
        return name

    def get_channel_map_str(self):
        channel_map = self.get_channel_map()
        out = []
        for key, value in channel_map.items():
            out.append(f"{self.mk(key, 'c')}->{self.mk(value, 'c')}")
        return " ".join(out)

    def get_channel_map(self, names=True):
        """
        Returns Dict of {"scan_channel": "post_channel"}
        """
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
            print(f"Thread {counter}: Starting Scanning {scan_channel}->{post_channel} for `{scan_type}' ...", end=" ")
            thread = threading.Thread(target=self.main, args=(scan_channel, post_channel, scan_type))
            thread.start()
            print(f"Thread {counter} Started!")

        self.scanner_threads = counter

    def main(self, scan_channel, post_channel, scan_type):
        ts = time.time()
        ts_old = ts - self.buffer # Sets buffer when initializing

        while True:
            request_url = self.build_url(ts=ts, ts_old=ts_old, channel=scan_channel)
            response = self.make_request(request_url)
            
            for message in response['messages']:
                if 'bot_id' and 'subtype' and 'attachments' not in message:
                    continue
                else:
                    message = Message(message, message_type=scan_type)
                    if message.is_valid():
                        if DEBUG:
                            message.print_to_console()
                        else:
                            self.postToSlack(message)#, channel=post_channel)
            time.sleep(self.delay)

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
    text         = info['text']
    response_url = info['response_url']
    trigger_id   = info['trigger_id']
    return token, team_id, channel_id, user_id, text, response_url, trigger_id

######################

global server_port, AUTHED_USER_LIST, maps_api_key, DEBUG, logger_type
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
    "C95PNBBQA" : {
        "post_to": "G6DLY0GDA",
        "type": "raid"
    },
    "CBJRLE45U" : {
        "post_to": "G6DLY0GDA",
        "type": "mon"
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
    print("Webserver Started!\n")

    print("Setting Up Scanner ...", end=" ")
    Scan = Scanner(
        queue=scanner_queue, 
        maps_api_key=maps_api_key,
        cookies=cookies,
        scanner=scanner_token,
        sc=sc_posting,
        post_token=post_token
    )
    print("Set Up Complete!\n")

    for scan_channel, info in scanner_map.items():
        post_channel = info['post_to']
        scan_type = info['type']
        print(f"Adding Scan Channel {scan_channel}->{post_channel} with type {scan_type} ...", end=" ")
        Scan.add_scan_channel(scan_channel, post_channel, scan_type)
        print("Added!")

    print("\nStarting Scanner ...")
    Scan.start()
    print("Scanner Started!")

