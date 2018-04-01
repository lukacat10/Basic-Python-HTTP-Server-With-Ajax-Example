#!/usr/bin/env python
"""
Hello!

Welcome to my ajax demonstrator!

Some info about the basic http server:
* do_GET and do_POST run when the the server receives a get or post request, respectevly.
* the object these methods receive, 'self', is described here: https://docs.python.org/2/library/basehttpserver.html
* self.path gets the requested path in the server. It is used to determine whatever the request was received from the master or the clients (NOT IMPORTANT)
* self.path is also used to determine if an ajax request was made. This is not neccasery at all, and sometimes ajax
requests are made to normal html pages if they contain inline server side code (like how php, c# .net web, jsp and others work).
* ajax requests are filtered by type. Each type is run by a different method at the bottom of this file, and all they methods return a TINY TEXT DATA. This
text data is structured as either plain text if it doesnt contain a lot of data OR as JSON - the easiest way to send data to javascript, which recieves
the data as the ajax initiator.
"""
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer
import json
import time;
class S(BaseHTTPRequestHandler):
    #=====================Global Variables=========================
    fake_server_status = False# <--- This is the fake server status retrieved from the server's control panel web page. When clicking the "Check Status" button, this value is retrieved via ajax.
    def checkStatus(self):
        return str(S.fake_server_status)
    """
    Gets the second keyvalue pair of the POST request. the first one is the type of ajax request, and the ones after it are the arguments...
    """
    def changeStatus(self, keyValuePair):
        print "before: " + str(S.fake_server_status)
        splittedKeyValuePair = keyValuePair.split("=")
        if splittedKeyValuePair[0] == "changevalue":
            if splittedKeyValuePair[1] == "true":
                S.fake_server_status = True
                print "after: " + str(S.fake_server_status)
            elif splittedKeyValuePair[1] == "false":
                S.fake_server_status = False
                print "after: " + str(S.fake_server_status)
    #Step 3 - clients
    clients = {}#key is name, value is an array with 3 values: (timeClientAddedToDictionary, timeOfLastKeepAlive, averageTimeBetweenKeepAlives)
    removedClients = {}#key is name, value is time when removed
    lastServerUpdate = None
    clientKeepAliveTimeout = 5
    def addClient(self, keyValuePair):
        
        splittedKeyValuePair = keyValuePair.split("=")
        name = None
        if splittedKeyValuePair[0] == "name":
            name = splittedKeyValuePair[1]
            for key in list(S.clients.keys()):
                S.keepalivetimeoutcheck(self, key)
        else:
            return str(False)
        
        if not S.clients.has_key(name):
            S.clients[name] = [time.time(), time.time(), -1]
            print "Client '" + name + "' added!"
            return str(S.clientKeepAliveTimeout)#Let the client know that we have some strict timeout rules!
        return str(False)
    #if onlyNewEntries is true, it saves bandwidth - serving the purpose of ajax :)
    def getClientsDictionary(self, onlyNewEntries=True):
        dicopy = S.clients.copy()
        if onlyNewEntries == True and not S.lastServerUpdate == None:
            for key, value in dicopy.iteritems():
                if S.keepalivetimeoutcheck(self, key):
                    del dicopy[key]
                else:
                    if value[1] < S.lastServerUpdate:
                        del dicopy[key]
                    else:
                        value[1] = time.asctime( time.localtime(value[1]))
        
        S.lastServerUpdate = time.time()
        if len(removedClients) > 0:
            for key, value in removedClients.iteritems():
                removedClients[key] = time.asctime( time.localtime(value))
        returnedString = json.dumps((dicopy, removedClients))
        removedClients.clear()
        return returnedString
    def keepalive(self, name):
        if S.clients.has_key(name) and not S.keepalivetimeoutcheck(self, name):
            value = S.clients[name]
            thisnewkeepalive = time.time()
            if value[2] == -1:
                value[2] = thisnewkeepalive - value[1]
            else:
                value[2] = value[2] + thisnewkeepalive - value[1]
                value[2] = value[2] / 2
            return str(True)
        return str(False)
    def keepalivetimeoutcheck(self, name):#client should exist in dictionary!
        value = S.clients[name]
        if time.time() - value[1] > S.clientKeepAliveTimeout:
            print "Client '" + name + "' has been automatically removed due to inactivity!"
            print "It's stats were: last keep alive at " +   time.asctime( time.localtime(value[1]))
            if value[2] != -1:
                print "and average keep alive rate of " + time.asctime( time.localtime(value[2]))
            del S.clients[name]
            S.removedClients[name] = time.time()
            return True
        return False
    #=====================End Of Global Variables Section=========================
    #=====================Request Handling Section================================
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        if self.path == "/master" or self.path == "/Master_Wait_Page.html" :
            with open('Master_Wait_Page.html', 'r') as content_file:
                content = content_file.read()
                self.wfile.write(content)
        else:
            with open('Join_The_Game.html', 'r') as content_file:
                content = content_file.read()
                self.wfile.write(content)

    def do_HEAD(self):
        self._set_headers()
        
        
    def do_POST(self):
        self._set_headers()
        print self.headers.get('Host')
        if self.path == "/ajaxrequests":# Data of post is structured this way: key1=value1&key2=value2&key3=value3&...etc...
            content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
            post_data = self.rfile.read(content_length) # <--- Gets the data itself in its normal structure
            splittedData = post_data.split("&")# Returns an array with each index containing 'key=value' pair
            firstPair = splittedData[0]#Gets the first pair
            firstPairSplit = firstPair.split("=")#Splits the first pair into an array with 2 objects: the key, and the value.
            if firstPairSplit[0] == "reqtype":
                if firstPairSplit[1] == "checkstatus":
                    self.wfile.write(self.checkStatus())
                if firstPairSplit[1] == "changestatus":
                    print splittedData[1]
                    self.wfile.write(self.changeStatus(splittedData[1]))
                if firstPairSplit[1] == "joinServer":
                    self.wfile.write(self.addClient(splittedData[1]))
                    
                
        
    #=====================END of Request Handling Section================================
def run(server_class=HTTPServer, handler_class=S, port=81):
    try:
        server_address = ('', port)
        httpd = server_class(server_address, handler_class)
        print 'Starting httpd...'
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('Shutting down due to Keyboard interrupt')
        server.shutdown()

if __name__ == "__main__":
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
