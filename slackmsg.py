#!/usr/bin/env python3

import os
import sys
import time
import getpass

def usage(msg):
	future_menu_items = """
	-u,  --user 			Declares the user you are sending the message to"""
	sys.exit(f"""{msg}
Usage:
	slackmsg [options] <filename>
	slackmsg [options] <filename1,filename2,etc.>
	slackmsg [options] all

	[] denote optional arguments
	<> denote required positional arguments

Options:
	-h,  --help 			Shows this message
	-T,  --Tutorial 		Prints the detailed tutorial message
	-ac, --at_channel  		Alerts everyone in the channel
	-c,  --channel 			Provides a list of all channels in the team and
					allows the user to send a message to that channel
					(Default channel: #virtual-peptide)
	-m,  --msg 			Prompts the user for a message to send to send along
					with the uploaded file.
	-t,  --thread 			Declares the timestamp (in epoch time) for the message
					you want the thread the files to
	-d,  --delimiter 		Declares the filename delimiter (Default is a comma)
					This is only really useful if your filename has a comma in it.
	     --TOKEN 			Provides the input token. Not recommended -- use
                           	        '.TOKEN' text file to store tokens instead.
					Note: the binary file has the token built into it.
	     --debug 	                Toggles debugging. If an error message is recieved
        	                        in the Slack API call, the full JSON error message
                	                will be printed and the program will abort.
	     --GUI 			Toggles the GUI. All other command-line args will be ignored.

""")

def tutorial():
	sys.exit("""
 -------------------------
| An Tutorial of slackmsg |
 -------------------------

Intro:
    slackmsg is a command line tool designed to make it easy to upload files to Slack
    directly from the command line. slackmsg is platform independent and has zero
    dependencies, allowing it to be used on any system at any time. This allows you
    to upload any sort of file (picture, text file, script, etc.) from both the your
    local machine or the server by typing only a few words.

    While slackmsg provides you with the oportunity to alert a particular user of the
    file you are sending, it is not configured to send messages to direct message
    channels. This is advantageous because it forces files to be published in a public
    channel where all team members have the ability to access a particular file. Often,
    files need to be sent to different people at different times and this allows people
    to search for files already posted within slack in a manner that is much easier than
    searching through a shared folder on the supercomputer. This will also limit the
    amount of memory taken up on shared supercomputer drives.

    By default, files are posted to #virtual_peptide and you will be prompted for which
    Slack user you want to alert of your message. It's important to note that you can tag
    any user in any channel, even if they are not in the channel. If a user is not in the
    channel, they will not get the notification unless you invite them to that channel.
    Using the -ac/--at_channel flag will tag @channel rather than an individual user. This
    will send a notification to every member of the channel. Be aware of this when posting
    files with these flags as it can quickly become annoying.

    The -t/--thread flags are also a particularly useful options as they add the message as
    a thread to a previous message. The timestamp must be in unix time (IE: 1580837811.0515).
    This timestamp must be exact, otherwise it is ignored. This feature is usually only
    used for repeat file postings. After a file is posted, the timestamp from that file
    is posted to the terminal output. Additionally, when posting multiple files,
    subsequent files are posted in the thread of the first file.

    The --GUI flag triggers the GUI. This requires the `tkinter` module. If `tkinter` is not
    installed, slackmsg will attempt to install it using pip. If it fails to do so, the program
    will exit with a notification to install tkinter using pip.

    NOTE: Installing modules requires you to be using a virtual environment. If you are not
    using a virtual environment, you will not be able to install the `slackclient` or `tkinter`
    modules.

Detailed Usage Information:
    slackmsg [options] <filename>
    slackmsg [options] <filename1,filename2,etc.>
    slackmsg [options] all

    The file name (including a list of files the 'all' keyword) is required for this script
    to function. The last command argument is assumed to be the filename. Failure to include
    command line args will cause the script to terminate with an error. If command line args
    are included, but the filename is not, the final argument will be assumed to be the file.
    An error will occur when uploading the file if the file cannot be found. In an attempt to
    prevent errors files not in the directory will be ignored in runtime.

Basic Usage Examples:
    slackmsg prod0.mdcrd      Uploads `prod0.mdcrd` to the default channel.
    slackmsg -c prod0.mdcrd   Prompts user for a channel, uploads `prod0.mdcrd` to that channel.
    slackmsg -ac prod0.mdcrd  Uploads `prod0.mdcrd` to the default channel, tagging all users.
    slackmsg -m prod0.mdcrd   Prompts user for a message, uploads `prod0.mdcrd` to default channel.
    slackmsg all              Prompts user for a channel, uploads all files in the working directory.

Advanced Usage Example:
    slackmsg -c -ac -m prod0.mdcrd,prod1.mdcrd,prod2.mdcrd

    This prompts the user for a message and a channel. All files are posted to the selected channel
    with prod1.mdcrd and prod2.mdcrd being placed in the thread. The whole channel is notified of
    the file being posted.

Debugging Other Scripts:

    If you have difficulties with a specific error or script, It's useful to get all of the
    information possible. What are you trying to do? What did you run from the command line?
    Consider adding ` | tee failure.log` to your failed command line command to log the full
    error. Sending this can greatly help to solve problems. If a file named `failure.log` is
    in the directory, it will automatically be uploaded when this script is run.

""")

def check_setup(dir, setup_dir='.slackmsg', token_file='.TOKEN'):
	return os.path.exists(os.path.join(dir, setup_dir)) and os.path.exists(os.path.join(dir, setup_dir, token_file))

def run_setup(dir, setup_dir='.slackmsg', token_file='.TOKEN'):
	new_dir = os.path.join(dir, setup_dir)
	new_token_file = os.path.join(new_dir, token_file)
	try:
		os.mkdir(new_dir)
	except:
		sys.exit(f"Couldn't make directory: {new_dir}")
	try:
		token = input("Please enter your Slack Token: ")
		print()
		with open(new_token_file, 'w') as f:
			f.write(token)
	except:
		sys.exit(f"Couldn't make token file: {new_token_file}")


def install_module(module):
	try:
		subprocess.call(['pip', '-q', 'install', module])
	except:
		venv = (hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))
		venv_msg = f"you are {'' if venv else 'NOT '}running a virtual environment"
		sys.exit(f"Module: {module} could not be found or installed using pip and {venv_msg}.\nPlease install before continuing using:\n\tpip install {module}")

def import_tk(install=False, retries=0):
	if install:
		install_module("tkinter")
	try:
		global Tk, Label, Button, Combobox
		from tkinter import Tk, Label, Button
		from tkinter.ttk import Combobox
		return True
	except:
		if retries < 2:
			return import_tk(install=True, retries=(retries+1))
		else:
			return False

def import_slack(install=False, retries=0):
	if install:
		install_module("slackclient==1.3.0")
	try:
		global SlackClient
		from slackclient import SlackClient
		return True
	except:
		if retries < 2:
			return import_slack(install=True, retries=(retries+1))
		else:
			return False

class GUI:
    def __init__(self, master):
        self.master = master
        self.exit_attempts = 0
        self.filler = "Select a File"
        self.file_list = os.listdir()
        self.file_list.insert(0, self.filler)
        self.selected_files = []

        master.title("slackmsg GUI (beta)")

        self.label = Label(self.master, text="Select Your Files!")
        self.add_file_button = Button(self.master, text="Add File", command=self.add_file)
        self.close_button = Button(self.master, text="Submit", command=self.submit)
        self.selected_file_label = Label(self.master, text="")
        self.combo = Combobox(self.master)

        self.reload_combo()
        self.load()
    def exit(self, text):
        # self.selected_file_label.configure(text=text)
        print(text)
        self.master.quit()

    def submit(self):
        if self.selected_files != []:
            self.exit("Submitting file(s): " + ", ".join(self.selected_files))
        elif self.exit_attempts > 0:
            self.exit("Aborting program per user request.")
        else:
            self.selected_file_label.configure(text="No files selected.\nEither add a file or press submit again to exit.")
            self.exit_attempts += 1

    def add_file(self):
        filename = self.combo.get()
        if filename != self.filler:
            idx = self.file_list.index(filename)
            filename = self.file_list.pop(idx)
            self.selected_files.append(filename)
            self.refresh_selected()
            self.reload_combo()

    def refresh_selected(self):
        text = "Selected File(s): " + ", ".join(self.selected_files)
        self.selected_file_label.configure(text=text)

    def reload_combo(self):
        self.combo['values'] = self.file_list
        self.combo.current(0) #set the selected item

    def load(self):
        self.label.pack()
        self.combo.pack()
        self.add_file_button.pack()
        self.close_button.pack()
        self.selected_file_label.pack()

    def run(self):
        self.master.mainloop()

    def get_data(self):
        return self.selected_files

class SlackFile:
	"""
	SlackFile is a class to handle file uploading to a slack team.
	"""
	def __init__(self, TOKEN=None, token_path=None, token_file='.TOKEN', headers=None, filename=None, sender=None, channel=None, file_list=None, msg=None, thread_ts=None, debug=None, user=None):
		# Setup
		self.token_path = token_path if token_path is not None else os.path.expanduser("~")
		self.TOKEN = TOKEN if TOKEN is not None else self.get_token(os.path.join(self.token_path, token_file))
		self.sc = SlackClient(self.TOKEN)
		self.file_list = file_list
		self.filename = filename
		self.thread_ts = thread_ts
		self.debug = debug
		self.file_tuple = None
		self.comment = None
		self.sent_ts = None
		# The initial plan was for the user to input their own username as the `sender` from the
		# command line arguments, but this could lead to sending messages on behalf of another user.
		# It's easier to just send it using the user's computer login name as the username. This isn't
		# pretty, but it works until a directory matching slack usernames and computer logins can be made.
		self.sender = sender if sender is not None else getpass.getuser()
		self.channel = channel if channel is not None else self.set_channel()
		self.user = user if user is not None else self.set_user()
		self.msg = msg if msg is None else self.set_message()

	def manage_sent_msg(self):
		# Retrieve timestamp of sent message
		try:
			# Check Public Channel First
			self.sent_ts = self.resp['file']['shares']['public'][self.channel][0]['ts']
		except:
			# If not public, It's Private!
			self.sent_ts = self.resp['file']['shares']['private'][self.channel][0]['ts']
		self.thread_ts = self.sent_ts # Handles repeat messages
		self.msg = None # Resets user message
		self.comment = self.comment.replace(" <!channel>", "") # Prevents spamming @channel for future messages.

	def check_response(self):
		# Function for handling successful and failed file uploads
		if bool(self.resp["ok"]):
			print("File sent!", end=" ") # Prints sucess message
			if self.thread_ts is None and self.sent_ts is None:
				self.manage_sent_msg()
				print(f"To add a file to this thread use the flag `-t {self.sent_ts}`") # Makes threading easier in the future
			else:
				print()
		else:
			# Handles failled API calls. This _should_ be rare!
			if not self.debug:
				# If not in debugging mode, error message prints, proceeds to next file
				print("ERROR! -- Could not upload file")
			else:
				# Prints JSON error message, aborts program.
				print("ERROR! -- Printing Slack Response: \n")
				sys.exit(self.resp)

	def set_channel(self):
		# FIXME: Combine set_user and set_channel -- they share a lot of the same code
		self.get_channels()
		print("Getting all Channels in Your Slack Team\n")
		channel_list = [i for i in self.resp['channels'] if not i['is_archived']] # IMPORTANT: HANDLE ARCHIVED CHANNELS!!
		for idx, chan in enumerate(channel_list): # Iterate over entire channel list
			# Formatting -- The channel name better be less than 30 characters!
			print(f"{idx:>3}: {chan['name']:30}", end= "\t" if idx %2 == 0 else "\n")

		if idx % 2 == 0:
			print() # Because formatting...
		inp = "-1"
		while not inp.isdigit() or 0 > int(inp) > len(channel_list) - 1:
			# This handles incorrect user input which never happens right? ;)
			inp = input(f"\nEnter the ID for the channel you want the message to go to\n> ")
		return f"{channel_list[int(inp)]['id']}"

	def set_user(self):
		# FIXME: Combine set_user and set_channel -- they share a lot of the same code
		self.get_users()
		print("Getting all Users in Your Slack Team\nReminder: The user you select may not be in the channel you are posing in\n")
		for idx, member in enumerate(self.resp['members']): # Iterate over entire member's list
			# Formatting -- Let's be real, if your username is over 30 characters, you are just bein mean...
			print(f"{idx:>3}: {member['real_name']:30}", end= "\t" if idx %2 == 0 else "\n")

		if idx % 2 == 0:
			print() # Because formatting...
		inp = "-1"
		while not inp.isdigit() or 0 > int(inp) > len(self.resp['members']) - 1:
			# This handles incorrect user input which never happens right? ;)
			inp = input(f"\nEnter the ID for the User you want to send the Message to\n> ")
		return f"<@{self.resp['members'][int(inp)]['id']}>"

	def set_message(self):
		print("\nWhat message do you want to send with your file?")
		return input("> ")

	def get_token(self, token_file):
		#Reads the provided token_file (should be '.TOKEN') and returns the slack token for sending messages
		with open(token_file, 'r') as f:
			return f.readline().replace('\n', '').strip()

	def get_channels(self):
		# Slack's API call to scan the channels of the team associated with the slack token
		self.resp = self.sc.api_call("channels.list")

	def get_users(self):
		# Slack's API call to scan the users of the team associated with the slack token
		self.resp = self.sc.api_call("users.list")

	def set_comment(self):
		# Sets up default comment to be uplaoded with the file.
		# General format: '`Sender's name` uploaded a file for `recipient's name`' + any message
		self.comment = f"{self.sender} uploaded a file for {self.user}{self.msg if self.msg is not None else ''}"

	def post_file(self):
		if self.comment is None:
			self.set_comment()

		# Actual API call. Calls Slack's files.upload method
		self.resp = self.sc.api_call(
			"files.upload",
			initial_comment = self.comment,
			channels        = self.channel,
			filename        = self.filename,
			file            = self.file_tuple,
			thread_ts       = self.thread_ts
			)

		self.check_response()

	def msg_setup(self):
		# Adds the custom message.
		if self.msg is not None:
			self.msg = " with the following message: " + self.msg

	def send_msg(self):
		self.msg_setup()
		print()
		for file in self.file_list:
			if file not in os.listdir():
				# Handles filenames that are not in the direcotry
				print(f"File: '{file}' not found in directory. Ignoring.")
			else:
				self.file_tuple = (file, open(file, 'rb')) # Formatting for slack's api method
				print(f"Attempting to send file: {file} --", end=" ")
				self.post_file()

if __name__ == '__main__':
	# Set Default variables
	args 		= sys.argv[1:]
	channel 	= 'CQU9HJF2L'   # Set default channel here
	delimiter 	= ','
	home        = os.path.expanduser("~")
	token       = None
	msg 		= None
	thread_ts 	= None
	user 		= None
	debug 		= False

	if '--TOKEN' not in args and not check_setup(home):
		print('Setup not detected. Attempting to setup this script.')
		run_setup()

	elif len(args) < 1:
		# Handles incorrect usage
		usage("Error! No filename included.\n\nHelp Menu")

	elif '-h' in args or '--help' in args:
		# Handles help menu
		usage("Help Menu")

	elif "-T" in args or "--Tutorial" in args:
		# Handles tutorial
		tutorial()

	elif "--GUI" in args:
		if import_tk():
			print("Starting GUI")
			print("NOTE: THE GUI IS IN BETA AND HAS ONLY BEEN SET UP TO HANDLE FILE SELECTION")
			time.sleep(1)
			root = Tk()
			root.geometry("400x400")
			gui = GUI(root)
			gui.run()
			file_list = gui.get_data()
		else:
			sys.exit("TK ERROR!!!")


	else:

		for i, arg in enumerate(args):

			if arg in ['-d', '--delimiter']: # Option to set delimiter
				delimiter = str(args[i + 1])

			elif arg in ['-ac', '--at_channel']: # Option to toggle @channel
				user = "everyone <!channel>"

			elif arg in ['-c', '--channel']: # Option for overriding default channel
				channel = None

			elif arg in ['-t', '--thread']: # Option for Threading a message
				thread_ts = args[i + 1]

			elif arg in ['-m', '--msg']: # Toggles interactive message prompt
				msg = "interactive"

			elif arg in ['--TOKEN']: # Sets slack token -- It's recommended to just use the '.TOKEN' file to store the token (for security)
				token = args[i + 1]

			elif arg in ['--debug']:
				debug = True

			elif i == len(args) - 1:
				if args[i].lower() in ['all']:
					file_list = os.listdir()
				else:
					file_list = [ args[i] ] if delimiter not in args[i] else args[i].split(delimiter)

	if 'failure.log' in os.listdir() and 'failure.log' not in file_list:
		file_list.append('failure.log')
	if import_slack():
		S = SlackFile(file_list=file_list, user=user, channel=channel, msg=msg, thread_ts=thread_ts, debug=debug, token_path=home)
		# sys.exit(f"file_list={file_list}\nuser={user}\nchannel={channel}\nmsg={msg}\nthread_ts={thread_ts}\ndebug={debug}")
		S.send_msg()
