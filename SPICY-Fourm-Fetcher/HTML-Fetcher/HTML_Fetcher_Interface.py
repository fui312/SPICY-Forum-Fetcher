
import urllib.request
from re import findall, search
import json
from tkinter import *

# Initalize variables we will be using
keywords = "" # Keywords to whitelist/blacklist
whitelist = False # Configures if the 'keywords' filter should blacklist or whitelist
activity = 10 # Minimum thread activity required to save
subfourm = "ck" # Default to a safe-ish board...
frequency = 60 # How often to run the script (in minutes)
maxposts = 3 # Max number of posts to retrieve within criteria
depth = 1 # How many pages deep to search

# Dependent variables
pgcount = 0

# Constant Variables
char_set = 'UTF-8'

# Function for creating Fetcher Configuration file
def SaveConfig(k=keywords, a=activity, s=subfourm, f=frequency, m=maxposts, d=depth, w=whitelist):
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
    del config

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
        del config
except:
    print("Config file not found, creating one...")
    SaveConfig()

# Config is loaded, now for the main body of the script
url = "http://boards.4chan.org/"

# Function attempts to locate keywords in a given chunk of string
# Returns true if it detects at least one, or false under the same conditions if 'inverse' is 'False'
def CheckForKeywords(kw, chunk, inverse):
    rtnVal = False
    for i in range(len(kw)):
        testStr = findall(kw[i], chunk)
        if len(testStr) > 0:
            if inverse:
                rtnVal = True
            else:
                rtnVal = False
            return rtnVal
    return rtnVal

# Function finds the number of replies on a thread
# Returns true if number of replies equals or exceeds supplied value
def CheckForActivity(minCount, chunk):
    # Since the HTML document isn't specialized for scripts, we'll need to improvise
    # Isolate section containing the thread summary
    commentCount = findall('(<span class="summary desktop">(.*?)\.)', chunk)
    for i in commentCount:
        s = i[0]
        # With the given section, limit the string again to just the number of replies
        findReplies = search('([0-9]+ replies)', s)
        if findReplies != None:
            # Splice it up futher more to get just the number
            getNumb = s[findReplies.start():findReplies.end()]
            actualNumb = search('([0-9]+)', getNumb)
            ii = int(getNumb[actualNumb.start():actualNumb.end()])
            # Finally, compare the number
            if minCount >= ii:
                return True
    return False

# Splices up board html into per-thread chunks, returning it in a map/json
# The data from this function is what will eventually be sent to the C++ program
def SortHtml():
    editingFile = 0
    foundThreads = 0
    # Clear keywordArray first before setting it
    keywordArray = findall('(.*?);', keywords)
    for i in range(len(keywordArray)):
        resStr = keywordArray[i].replace(';', '')
        keywordArray[i] = resStr
    print(keywordArray)

    filteredData = []
    filteredThrough = 0
    # Loop through all xhtml documents for threads, stopping if we run out, or fill our cap
    while True:
        if foundThreads >= maxposts:
            break # Don't try to pull more threads once we reach our cap
        string = ""
        try:
            # Open file
            openFile = 'temp\html' + str(editingFile+1) + '.xhtml'
            print("Attempting to open file: " + openFile)
            data = open(openFile, 'r', encoding=char_set)
            # Put file contents into variable
            string = data.read()
        except:
            print("All possible documents exhausted")
            break # Ran out of documents to test, stop trying and return whatever we have
        if data != "":
            # Locate all the thread chunks
            chunks = findall('(<div class=\"thread\" id=\"t[0-9]+\">(.*?)<hr>)', string)
            totalChunks = len(chunks)
            print("Found " + str(totalChunks) + " chunks in document number " + str(editingFile+1))
            # Increment working file for next iteration
            editingFile += 1
            # Scan the data chunks for anything that fills our criteria
            for i in chunks:
                filteredThrough += 1
                d = i[0] # <-- Personal takeaway: 'findall' function returns an array with its contents containing another list
                valid = {}
                valid['keywords'] = False
                valid['activity'] = False
                # Check to see if we're under our cap
                if foundThreads >= maxposts:
                    break
                # There's a hidden benifit to having these conditionals lined up this way:
                # If the first statement returns true, the second one is never processed.
                # This only works because the comparator is an 'or' statement
                if len(keywordArray) == 0 or CheckForKeywords(keywordArray, d, whitelist):
                    valid['keywords'] = True
                if activity == -1 or CheckForActivity(activity, d):
                    valid['activity'] = True
                # Passed all our checks, debug output
                if valid['keywords'] == True and valid['activity'] == True:
                    filteredData.append(d)
    del keywordArray
    if len(filteredData) > 0:
        print("Managed to filter down " + str(filteredThrough) + " threads to " + str(len(filteredData)) + "!")
        for x in filteredData:
            print("Filtered Thread No." + str(filteredData.index(x)) + ": \n" + x)

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
        self.blkBool = IntVar()
        self.blkBool.set(int(whitelist))
        self.activityInt = IntVar()
        self.activityInt.set(activity)
        self.fourmStr = StringVar()
        self.fourmStr.set(subfourm)
        self.countInt = IntVar()
        self.countInt.set(maxposts)
        self.depthInt = IntVar()
        self.depthInt.set(depth)

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
        self.blacklistBox = Checkbutton(self, text="Blacklist Words", variable=self.blkBool)
        self.blacklistBox.grid(row=3, sticky=W, padx=(10, 10))

        # Minimum Activity
        self.activityLabel = Label(self, text="Thread Activity:")
        self.activityLabel.grid(row=4, sticky=W, padx=(10, 10))
        self.activityCount = Spinbox(self, cnf, width=10, textvariable=self.activityInt)
        self.activityCount.grid(row=5, sticky=W, padx=(10, 10))

        # SubFourm
        self.fourmLabel = Label(self, text="Board:")
        self.fourmLabel.grid(row=6, sticky=W, padx=(10, 10))
        self.selectFourm = Entry(self, cnf, width=15, textvariable=self.fourmStr)
        self.selectFourm.grid(row=7, sticky=W, padx=(10, 10))

        # Max Thread Count
        self.countLabel = Label(self, text="Max Threads:")
        self.countLabel.grid(row=8, sticky=W, padx=(10, 10))
        self.maxCount = Spinbox(self, width=10, textvariable=self.countInt)
        self.maxCount.grid(row=9, sticky=W, padx=(10, 10))

        # Depth
        self.depthLabel = Label(self, text="Depth:")
        self.depthLabel.grid(row=10, sticky=W, padx=(10, 10))
        self.searchDepth = Spinbox(self, from_=0, to=10, width=10, textvariable=self.depthInt)
        self.searchDepth.grid(row=11, sticky=W, padx=(10, 10))

        # Fetch Threads
        self.findThreads = Button ( self, text="Fetch Threads", command=self.UpdateVariables )
        self.findThreads.grid(padx=(10, 10), pady=(30, 10))
    # Allow keyword scrolling
    def __scrollHandler(self, *L):
        op, howMany = L[0], L[1]

        if op == "scroll":
            units = L[2]
            self.filterWords.xview_scroll (howMany, units)
        elif op == "moveto":
            self.filterWords.xview_moveto (howMany)
    def UpdateVariables(self):
        # Overwrite config data
        keywords = self.filterStr.get()
        print("Keywords: " + keywords)
        whitelist = bool(self.blkBool.get())
        activity = self.activityInt.get()
        print("Activity Count: " + str(activity))
        subfourm = self.fourmStr.get()
        print("Board: /" + subfourm + "/")
        maxposts = self.countInt.get()
        print("Max Posts to Search: " + str(maxposts))
        depth    = self.depthInt.get()
        print("Search Depth: " + str(depth))
        SaveConfig(keywords, activity, subfourm, maxposts, depth, whitelist)

        # Fetch raw HTML
        #FetchThreads(depth)
        SortHtml()

app = Application() # Instantiate the application class
app.master.title("HTML Fetcher")
app.mainloop() # Wait for events