#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
import sys
import time
import smtplib
import getpass
import platform
import threading

class TextMessager():
	"""
	TextMessager is a class built to facilitate sending messages using an SMTP server.
	Although the SMTP server is simple and easy to understand, the purpose of this
	class is to further simplify it's use and allow a user an interactive environment
	to distribute the same message to a variety of users simply and without the messages
	being sent as a group message.

	The target user of this program is an HR Professional who is communicating with older
	employees who either do not have email addresses, do not know how to use their email address,
	or never check their email addresses. By loading a phone number in place of an email address,
	HR personel accomodate the preference of employees to use text messages while allowing them
	to send the messages from a computer and receive the response as an email.
	"""
	def __init__(self, mail_domain='smtp-mail.outlook.com', port=587, email=None):
		self.mail_domain       = mail_domain
		self.port              = port
		self.user_email        = email
		self.people            = []
		self.message_list      = []
		self.term_chars        = [' ', '.', ',', '!', '?']
		self.server            = None
		self.message           = None
		self.confirmation      = None
		self.max_length        = 155 # (155 total characters)
		self.header_length     = 15
		self.max_retries       = 5
		self.sleep_time        = 1
		self.subject           = "This is an automated message from HR."
		self.preview_header    = "-" * 75
		self.actual_max_length = self.max_length - self.header_length # (Factors in headers)
		self.default_path      = self.get_path()

	def Help(self):
		carrier_info = self.get_carrier_info()
		for key, value in carrier_info.items():
			print(f"Key: {key:<15} Value: {value:<15}")

	def get_carrier_info(self):
		"""
		Returns the @extension of each carrier's MMS line. Some carriers
		forward a SMS and MMS message to the recipient when emailing a
		phone number. This should prevent duplicate messages.
		"""
		carrier_info = {
			"AT&T"          : "@mms.att.net",
			"Boost Mobile"  : "@myboostmobile.com",
			"Cricket"       : "@mms.cricketwireless.net",
			"Sprint"        : "@pm.sprint.com",
			"T-Mobile"      : "@tmomail.net",
			"U.S. Cellular" : "@mms.uscc.net",
			"Verizon"       : "@vzwpix.com",
			"Virgin Mobile" : "@vmpix.com"
		}
		return carrier_info

	def get_path(self): # FIXME: Not Finished
		if 'windows' in (platform.system()).lower():
			# print('Connected to windows operating system.')
			return 'C:\\some\\windows\\path\\here\\'
		else:
			# print('Connected to UNIX operating system.')
			return f"/some/unix/path/here/"

	def set_email(self):
		retries = 0
		inp = input("Email Address: ")
		if self.verify(inp):
			return inp
		else:
			retries += 1
		if retries >= self.max_retries:
			self.quit("The email address provided doesn't appear to be a valid email.")

	def start_server(self):
		print("Setting up mail server ...", end=" ")
		try:
			self.server = smtplib.SMTP(self.mail_domain, self.port)
			self.server.starttls()
			print("Done!")
		except:
			print("ERROR")
			self.quit("Unable to start messaging server.")

	def login(self):
		if self.user_email is None:
			self.user_email = self.set_email()
		print("Attempting to log into email ...")
		try:
			self.server.login(self.user_email, getpass.getpass())
			# self.server.login(self.user_email, input("password"))
			print("Logged into email.")
		except:
			print("ERROR")
			print("Unable to login to email.")


	def load_files(self):
		for idx, value in enumerate(os.listdir()):
			print(f"{idx}: {value}")

	def message_from_text_file(self): # Finish module
		# self.load_files()
		print("This is not functional")

	def contacts_from_text_file(self): # Finish module
		# self.load_files()
		print("This is not functional")

	def add_person(self):
		person = input("Who do you want to add?\n>> ")
		if self.verify(person):
			if person not in self.people:
				self.people.append(person)
				print(f"{person} added to contacts list.")
			else:
				print(f"{person} is already in your contacts list.")
		else:
			print("Not a valid email address")
		if self.get_confirmation("\nWould you like to add another contact?"):
			self.add_person()

	def add_subject(self):
		while not self.confirmation:
			self.subject = input("Input the Subject for your message\n>> ")
			self.confirmation = self.get_confirmation("Is this correct?")
		self.confirmation = False # Reset to False
		print("Subject Saved.")

	def get_full_message_length(self):
		# DOES NOT factor in "(Message #/##) " (15 characters)
		return len(self.message)

	def trim_message(self, last_char_pos):
		"""
		Trims message to a max of self.max_length characters (including the subject)
		and sets the message list
		"""
		max_pos = last_char_pos + self.actual_max_length
		pos = max_pos if max_pos < len(self.message) else len(self.message) - 1
		while self.message[pos] not in self.term_chars:
			pos -= 1
			if pos == last_char_pos:
				self.quit("last_char_pos error")
		return self.message[last_char_pos : pos], pos

	def finalize_message(self, person):
		if self.message[-1] not in self.term_chars:
			self.message += "."
		if self.get_full_message_length() <= (self.actual_max_length):
			self.message_list.append(f"From: {self.user_email}\nTo: {person}\nSubject: Message 1/1\n\n{self.message}")
		else:
			last_char_pos = 0
			message_list = []
			while last_char_pos != len(self.message) - 1:
				msg, last_char_pos = self.trim_message(last_char_pos)
				message_list.append(msg)
			for idx, msg in enumerate(message_list):
				# print('here')
				self.message_list.append(f"From: {self.user_email}\nTo: {person}\nSubject: Message {idx + 1}/{len(message_list)}\n\n{msg}")

	def compose_message(self):
		while not self.confirmation:
			self.message = input("Input the message you want to Send\n>> ")
			self.confirmation = self.get_confirmation("Is this correct?")
		self.confirmation = False # Reset to False
		print("Message Saved.")

	def get_confirmation(self, prompt):
		inp = input(prompt + "\n(yes/no) >> ")
		if inp.lower() in ['y', 'yes']:
			return True
		else:
			return False

	def send_mail(self):
		if self.people != [] and self.message is not None and self.get_confirmation("Are you sure you want to send the message?"):
			self.message = self.subject + " " + self.message
			for person in self.people:
				self.finalize_message(person)
				for idx, message in enumerate(self.message_list):
					print(f"Sending message to {person} ...", end=" ")
					try:
						self.server.sendmail(self.user_email, person, message)
						print("Done!")
					except:
						print("Couldn't Send Message.")
			print("Message Sent Sucessfully.")
			self.message_list.clear()
			if self.get_confirmation("Would you like to quit the program?"):
				self.quit("Terminating Program...")
		elif self.people == []:
			print("No contacts added. Cannot send message.")
		else:
			print("Message Aborted.")

	def preview(self):
		if self.people == [] or self.message is None:
			print("Your message is not finished yet. Please finish before previewing.")
		else:
			print(self.preview_header + "Here is your previewed message" + self.preview_header)
			print(self.finalize_message(", ".join(self.people)))
			print(self.preview_header + "REMINDER: This message will be sent to each person individually so\nthey will not be able to see who else is receiving this message." + self.preview_header)
			input("Press enter to continue...")

	def verify(self, email):
		# Check for the input email being a valid email address. This is critical as
		# even the text numbers must be formatted as an email address.
		return re.search('^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$', email)

	def quit(self, msg):
		self.server.quit()
		print("Closed connection to mail server.")
		print(msg)
		os._exit(1)

	def interactive(self):
		while True:
			inp = input("""
 -----------
| Main Menu |
 -----------

1. Load Message From Text File
2. Load Contacts Trom Text File
3. Compose Message
4. Add Contact
5. Add Subject
6. Preview Message
7. Help
Type 'send' to send the message
Type 'quit' to exit

>> """)
			print()
			if inp == "1":
				self.message_from_text_file() # Make module
			elif inp == "2":
				self.contacts_from_text_file() # Make module
			elif inp == "3":
				self.compose_message()
			elif inp == "4":
				self.add_person()
			elif inp == "5":
				self.add_subject()
			elif inp == "6":
				self.preview()
			elif inp == "7":
				self.Help() # Make module
			elif inp in ['send', 'Send', 'SEND']:
				self.send_mail()
			elif inp in ["quit", "Quit", "QUIT"]:
				self.quit("Terminating Program...")
			else:
				print("Input Not Recognized")
			time.sleep(self.sleep_time)

def controller(max_timeout=600):
	"""
	Designed to be run as a thread to control the running of the script.
	After max_timeout seconds, this program will timeout with an error.
	"""
	seconds = 0
	while seconds < max_timeout:
		time.sleep(1)
		seconds += 1
	print("\nPROGRAM TERMINATED DUE TO TIMEOUT")
	os._exit(1)

if __name__ == '__main__':
	print("Getting Everything Set Up")

	# kwargs = parse_cli(sys.argv)

	Control = threading.Thread(target=controller)
	Control.start()

	Text = TextMessager()
	Text.start_server()
	Text.login()
	Text.interactive()
