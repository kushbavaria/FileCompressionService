'''
Author: Michael Carolin
Class: CS 346
Date: 10/9/15
'''
from flask import Flask
from flask import abort
import dropbox
import ConfigParser
import pprint
import time

app = Flask(__name__)
app.config['DEBUG'] = True

# dropbox connection, authentication, and configuration
config = ConfigParser.RawConfigParser()
config.read("settings.cfg")
token = config.get("dropbox", "token")
client = dropbox.client.DropboxClient(token)

# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.
#List of dropbox deltas as a FIFO structure
max_changes_to_keep = 20
file_deltas = []
cursor = None

def set_delta(file_deltas):
	#cursor = deltas.pop(0)['cursor'] if (len(deltas) > 0) else None
	deltas = []
	while True:
		delta = client.delta(cursor)
		deltas.append(delta)
		for file_list in delta['entries']:
			# enqueue the file to the FIFO list
		#		if file_list[1] is not None:	# avoid renamed files
			file_deltas.insert(0, file_list)
		global cursor 
		cursor = delta['cursor']
		if delta["has_more"] is False:
			break
		
	# keep only last 20 changes
	file_deltas = file_deltas[:max_changes_to_keep+1]

@app.route('/changes.txt')
def show_changes():
	set_delta(file_deltas)
	lines = "" 
	for delta in file_deltas:
		date = time.ctime()	# date this program accessed the file
		fileName = delta[0]
		action = "File was Modified"
		if delta[1] is None:
			action = "File was Deleted"
		elif "is_deleted" in delta[1]:
			action = "File was Deleted"

		line = date + "\t" + fileName + "\t" + action + "\n"
		lines += line
	
	return lines
	

@app.route('/')
def hello():
    """Return a friendly HTTP greeting."""
    return 'Hello World! This is Michael Carolin\'s third assignment for CS 346!'

@app.route("/<path:name>")
def find_dropbox_folder(name):
	filePath = "/" + name	
	try:
		f, metadata = client.get_file_and_metadata(filePath)
		return f.read()
	except dropbox.rest.ErrorResponse, e:
		# if file is a directory, search for its index.html child and try to return it
		try:
			indexFilePath = filePath + "/index.html"
			f = client.get_file(indexFilePath)
			return f.read()
		except:
			abort(404)
	except ValueError, v:
		abort(404)

@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, nothing exists at this URL.', 404




