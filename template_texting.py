from twilio.rest import TwilioRestClient
from flask import Flask, request, redirect
import twilio.twiml
import time 
from random import random
import math
from datetime import datetime
import os.path
import cPickle as pickle #retain state of program

#set account_sid and authtoken to appropriate value in Twilio account
account_sid = "xxx"
auth_token = "xxx"
client = TwilioRestClient(account_sid, auth_token)

last_day = time.strftime("%d/%m/%Y")
weekfive = False;
weeksix = False;
p = 1.5 # poisson probability (should be set to 1.5)

#use format "+15551234567" for numbers
client_numbers = ["+15551234567", "+15551234567"]
twilio_numbers = ["+15551234567"]

msg = "<my message to clients>"

#initialize/restore sys values
idx = 0
text_count = {}
twilio_match = {}
next_text_time = {}

for x in client_numbers:
	next_text_time[x] = 10 + 6*random() #10AM - 4PM
	text_count[x] = 0
	twilio_match[x] = twilio_numbers[idx] 
	idx = (idx + 1) % len(twilio_numbers)

if not os.path.isfile('save_idx.p'):
	pickle.dump(idx, open('save_idx.p','wb'))
if not os.path.isfile('save_tmatch.p'):
	pickle.dump(twilio_match, open('save_tmatch.p','wb'))
if not os.path.isfile('save_next_text_time.p'):
	pickle.dump(next_text_time, open('save_next_text_time.p','wb'))
if not os.path.isfile('save_text_count.p'):
	pickle.dump(text_count, open('save_text_count.p','wb'))
if not os.path.isfile('save_last_day.p'):
	pickle.dump(last_day, open('save_last_day.p','wb'))


text_count = pickle.load(open('save_text_count.p', 'rb'))
next_text_time = pickle.load(open('save_next_text_time.p', 'rb'))
twilio_match = pickle.load(open('save_tmatch.p', 'rb')) 
idx = pickle.load(open('save_idx.p', 'rb'))
last_day = pickle.load(open('save_last_day.p','rb'))

for x in client_numbers:
	if x not in twilio_match:
		twilio_match[x] = twilio_numbers[idx] 
		idx = (idx + 1) % len(twilio_numbers)
	if x not in text_count:
		text_count[x] = 0
	if x not in next_text_time:
		next_text_time[x] = 10 + 6*random()

pickle.dump(idx, open('save_idx.p','wb'))
pickle.dump(twilio_match, open('save_tmatch.p','wb'))

print "initialize/restored all system values"
print "text_count: "
print text_count
print "next_text_time: "
print next_text_time
print "twilio_match: "
print twilio_match

while True:
	cur_time = float(time.strftime("%H")) + float(time.strftime("%M"))/60 + float(time.strftime("%S"))/(60*60) # in hours
	validtime = cur_time < 24 and cur_time >= 10 and last_day == time.strftime("%d/%m/%Y")# 10AM - 10PM
	naptime = 12

	if validtime:
		for x in client_numbers:
			if cur_time >= next_text_time[x] and text_count[x] < 6:
				message = client.sms.messages.create(body=msg, to=x, from_=twilio_match[x]) 
				text_count[x]+=1
				next_text_time[x] = -math.log(random())/p + cur_time
				print "sent message to ", str(x), "from", twilio_match[x]
				print "next_text_time is", next_text_time[x], "and will be text number", text_count[x]
	else:
		"invalid time for text or restart day"
		last_day = time.strftime("%d/%m/%Y")
		for x in client_numbers:
			next_text_time[x] = 10 + 6*random() #10AM - 4PM
			text_count[x] = 0

	#find time until next scheduled event
	for x in client_numbers:
		if naptime > next_text_time[x] - float(cur_time) and text_count[x]<6:
			naptime = next_text_time[x] - cur_time

	if(naptime < 0): #just in case
		naptime = 0

	if sum(text_count[x] >= 6 for x in text_count) == len(text_count):
		print "sent all text for today", len(text_count)*6
		print text_count
		naptime = 10 - (cur_time - 24)

	# dump then go to sleep
	pickle.dump(next_text_time, open('save_next_text_time.p','wb'))
	pickle.dump(text_count, open('save_text_count.p','wb'))
	pickle.dump(last_day, open('save_last_day.p','wb'))


	print "next_text_time: ", next_text_time
	print "cur time: ", cur_time
	print "sleeping for", naptime*60, "minutes"
	time.sleep(naptime*60*60)
	