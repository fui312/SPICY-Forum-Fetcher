
import urllib.request
from re import findall
import json
from tkinter import *

# Initalize variables we will be using
keywords = "" # Keywords to whitelist/blacklist
whitelist = False # Configures if the 'keywords' filter should blacklist or whitelist
activity = 10 # Minimum thread activity required to save
subfourm = "ck" # Default to a safe-ish board...
frequency = 60 # How often to run the script (in minutes)
maxposts = 1 # Max number of posts to retrieve within criteria
depth = 1 # How many pages deep to search

# Dependent variables
pgcount = 0

# Function for creating Fetcher Configuration file
def SaveConfig(k=keywords, a=activity, s=subfourm, f=frequency, m=maxposts, d=depth, w=False):
    # We need a map to collate our config settings...
    config = {}
    config['keyword']   = k
    config['whitelist'] = w
    config['activity']  = a
    config['subfourm']  = s
    config['frequency'] = f
    config['maxposts']  = m
    config['depth']     = d
    # Dump configs in console for debugging
    print(config)
    # Then we just need to 'dump' the contents of the map into the config file
    with open('config.json', 'w') as newcfg:
        json.dump(config, newcfg) # This will place our config map in json format in file
    # The 'open' function also works to create files, hence its use here

# Check for config file, if it doesn't exist, create one
try:
    # Convert string contained in file to map format,
    # Then pull data from the new map into the independent variables
    print("Loading Config settings...")
    with open('config.json') as json_config:
        config = json.load(json_config)
        keywords    = config['keyword']
        whitelist   = config['whitelist']
        activity    = config['activity']
        subfourm    = config['subfourm']
        frequency   = config['frequency']
        maxposts    = config['maxposts']
        depth       = config['depth']
        # Debug: Dump json contents for debugging
        print(config)
except:
    print("Config file not found, creating one...")
    SaveConfig()

# Config is loaded, now for the main body of the script
url = "http://boards.4chan.org/"

# Splices up board html into per-thread chunks, returning it in a map/json
def HtmlToJson(string):
    chunks = findall('(<div class=\"thread\" id=\"t[0-9]+\">(.*?)<hr>)', string)
    return chunks

# Pulls the entire HTML from the board on a given page
def PullHtml(page, cset = 'UTF-8'):
    from urllib.request import urlopen, Request
    # Build the url
    buildurl = url + subfourm + "/"
    if page > 1:
        buildurl += str(page)

    # Request HTML
    req = Request(url + subfourm)
    req.add_header('User-Agent', 'Mozilla/5.0') # <-- a little naughty...
    webcontents = urlopen(req)
    webstring = webcontents.read().decode(cset) # Convert to string
    
    # Save HTML to a temporary file
    with open('temp\html' + str(page) + '.xhtml', 'w', encoding=cset) as file:
        file.write("Pulled from: " + buildurl + "\n" + webstring)

def FetchThreads(d=1):
    i = 0
    print("Attempting to pull " + str(d) + " page/s...")
    while i < d:
        PullHtml(i+1) # Save html to document
        print("Pulled page: " + str(i))
        i += 1
    if i == d:
        print("Successfully pulled all requested HTML")

# Window
cnf = {'bg': 'white', 'fg': 'black'}

class Application(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.grid()

        # Variable definitions
        self.filterStr = StringVar()
        self.filterStr.set(keywords)
        self.activityInt = IntVar()
        self.fourmStr = StringVar()
        self.countInt = IntVar()
        self.depthInt = IntVar()

        # Create the window UI
        self.createWidgets()
    def createWidgets(self):

        # Word Filter Box
        self.filterLabel = Label(self, text="Filter Words:")
        self.filterLabel.grid(row=0, sticky=W, padx=(10, 10))
        self.filterWords = Entry(self, cnf, width=30, textvariable=self.filterStr)
        self.filterWords.grid(row=1, sticky=E+W, padx=(10, 10))
        self.filterScroll = Scrollbar(self, orient=HORIZONTAL, command=self.__scrollHandler)
        self.filterScroll.grid(row=2, sticky=E+W, padx=(10, 10))
        self.filterWords["xscrollcommand"] = self.filterScroll.set

        # Word Filter Black/Whitelist
        self.blacklistBox = Checkbutton(self, text="Blacklist Words")
        self.blacklistBox.grid(row=3, sticky=W, padx=(10, 10))
        if whitelist:
            self.blacklistBox.deselect()
        else:
            self.blacklistBox.toggle()

        # Minimum Activity
        self.activityLabel = Label(self, text="Thread Activity:")
        self.activityLabel.grid(row=4, sticky=W, padx=(10, 10))
        self.activityCount = Spinbox(self, cnf, width=10, textvariable=self.activityInt)
        self.activityCount.grid(row=5, sticky=W, padx=(10, 10))
        self.activityCount.insert(0, activity)

        # SubFourm
        self.fourmLabel = Label(self, text="Board:")
        self.fourmLabel.grid(row=6, sticky=W, padx=(10, 10))
        self.selectFourm = Entry(self, cnf, width=15, textvariable=self.fourmStr)
        self.selectFourm.grid(row=7, sticky=W, padx=(10, 10))
        self.selectFourm.insert(0, subfourm)

        # Max Thread Count
        self.countLabel = Label(self, text="Max Threads:")
        self.countLabel.grid(row=8, sticky=W, padx=(10, 10))
        self.maxCount = Spinbox(self, width=10, textvariable=self.countInt)
        self.maxCount.grid(row=9, sticky=W, padx=(10, 10))
        self.maxCount.insert(0, maxposts)

        # Depth
        self.depthLabel = Label(self, text="Depth:")
        self.depthLabel.grid(row=10, sticky=W, padx=(10, 10))
        self.searchDepth = Spinbox(self, from_=0, to=10, width=10, textvariable=self.depthInt)
        self.searchDepth.grid(row=11, sticky=W, padx=(10, 10))
        self.searchDepth.delete(0,"end")
        self.searchDepth.insert(0, depth)

        # Fetch Threads
        self.findThreads = Button ( self, text="Fetch Threads", command=self.UpdateVariables )
        self.findThreads.grid(padx=(10, 10), pady=(30, 10))
    def __scrollHandler(self, *L):
        op, howMany = L[0], L[1]

        if op == "scroll":
            units = L[2]
            self.filterWords.xview_scroll (howMany, units)
        elif op == "moveto":
            self.filterWords.xview_moveto (howMany)
    def UpdateVariables(self):
        keywords = self.filterStr.get()
        print("Keywords: " + keywords)
        activity = self.activityInt.get()
        print("Activity Count: " + str(activity))
        subfourm = self.fourmStr.get()
        print("Board: /" + subfourm + "/")
        maxposts = self.countInt.get()
        print("Max Posts to Search: " + str(maxposts))
        depth    = self.depthInt.get()
        print("Search Depth: " + str(depth))
        SaveConfig(keywords, activity, subfourm, maxposts, depth)
        FetchThreads(depth)

app = Application() # Instantiate the application class
app.master.title("HTML Fetcher")
app.mainloop() # Wait for events