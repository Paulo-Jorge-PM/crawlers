#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import ndjson
import time
import os
from requests_html import HTMLSession, HTML

import tools

#session = HTMLSession()
#r = session.get(a_page_url)

class htmlCrawler:

    def __init__(self, url=None):

        self.session = HTMLSession()


        #self.NDJSON_FILE = "output/links/publico.ndjson"
        self.BASE_DOMAINS = ["publico.pt", "publico.clix.pt"]#for checking if it is not an external link
        self.SAVE_DIR = "output/html/publico/"

        ###LET IT EMPTY IF CRAWLING WEB. Make it "https://arquivo.pt/noFrame/replay/" if crawling arquivo.pt global links, 
        #so that the script can now which is the arquivo.pt url and which is the website link and split them
        #self.BASE_URL = "https://arquivo.pt/noFrame/replay/"
        self.BASE_URL = ""

        #self.url = ""
        self.totalLinks = []
        self.homepageLinks = []
        self.savedLinks = []
        #self.savedFiles = {}#dumped and saved with the files as metadata
        #self.logFile = ""
        self.end = False

        self.rederJS = True

        ### START FLOW
        ### THE FILE homepages.txt MUST HAVE ALL THE HOMEPAGE LINKS TO START CRAWL FOR THE 1st TIME

        #self.json = self.openJson()
        #snapshots = self.linksFromJSON(self.json)

        self.loadLinks()

        #self.totalLinks = self.totalLinks + snapshots
        #self.homepageLinks = self.homepageLinks + snapshots

        #self.loadDoneFiles()
        
        ### LET THE MAGIC BEGIN
        try:
            self.startCrawl()
        except:
            #in case connection time out repeat a 2nd time (for crawl during the night)
            self.startCrawl()
        else:
            #A 3rd try for the night
            self.startCrawl()


    """def openJson(self, file="link.txt"):
        with open(self.NDJSON_FILE) as f:
            data = ndjson.load(f)
            return data

    def linksFromJSON(self, json):
        linksList = []
        for row in json:
            link = self.BASE_URL + row["timestamp"] + "/" + row["url"]
            linksList.append(link)
            print("LINK ADDED: " + link)
        return linksList"""


    def loadLinks(self):
        ###a+ so it can read but also creat if not exist. f.seek(0) to simulate the read and 
        with open(self.SAVE_DIR + "homepages.txt", "a+") as f:
            f.seek(0)
            lines = [line.rstrip() for line in f]
            for l in lines:
                self.homepageLinks.append(l)

        with open(self.SAVE_DIR + "savedLinks.txt", "a+") as f:
            f.seek(0)
            lines = [line.rstrip() for line in f]
            for l in lines:
                self.savedLinks.append(l)

        with open(self.SAVE_DIR + "totalLinks.txt", "a+") as f:
            f.seek(0)
            lines = [line.rstrip() for line in f]
            for l in lines:
                self.totalLinks.append(l)

        for link in self.homepageLinks:
            if link not in self.totalLinks:
                self.totalLinks.append(link)
                with open(self.SAVE_DIR + "totalLinks.txt", "a+") as f:
                    f.write(link+"\n")


    def startCrawl(self):
        print("CRAWLING...")
        while self.end == False:

            count=0
            for link in self.totalLinks:

                if link not in self.savedLinks:

                    try:
                        #GET HTML
                        resp = self.getHtml(link, render=self.rederJS)
                        #html = resp.text
                        html = resp.html.html

                        #SAVE HTML
                        if self.BASE_URL != "":
                            originalUrl = link.split(self.BASE_URL, 1)[1]
                            domain = originalUrl.split("/", 1)[1].replace("https://", "").replace("http://", "").replace("www", "").split("/", 1)[0]
                        else:
                            originalUrl = link
                            domain = originalUrl.replace("https://", "").replace("http://", "").replace("www", "").split("/", 1)[0]

                        if link in self.homepageLinks:
                            domain = "homepages/"
                        else:
                            domain = "sublinks/" + domain
                        fName = originalUrl.replace("/", "\\")[:220]#220 because filenames in some OS are limited to 255. \\ because / is not allowed in linux

                        #add the original link to the 1st line as comment
                        html = "<!--"+link+"-->\n" + html
                        path = self.saveHtml(html, self.SAVE_DIR + "/" + domain, fileName=fName)

                        #ADD TO THE SAVED LIST and LOG:
                        self.savedLinks.append(link)
                        with open(self.SAVE_DIR + "savedLinks.txt", "a+") as f:
                            f.write(link+"\n")

                        #self.logFile += link + " :::|::: " + path + "\n"
                        with open(self.SAVE_DIR + "log_saved_files.txt", "a+") as f:
                            f.write(link + " :::|:::> " + path + "\n")

                        #EXTRACT NEW LINKS:
                        self.extractLinks(resp)

                        count += 1
                    except:
                        print("ERROR connecting to: " + link)
                        with open(self.SAVE_DIR + "failedLinks.txt", "a+") as f:
                            f.write(link+"\n")

            #if no more links to work end the loop
            if count == 0:
                self.end = True
                #with open(self.SAVE_DIR + "log_saved_files.txt", "w") as f:
                #    f.write(self.logFile)
                print("== FINISHED!!!!!!!!!!!!! ===")



    def getHtml(self, link, render=False):
        js = '''
        () => {
            return {
                width: 555,
            }
        }
            '''
        #html = HTML(html=link)
        #val = html.render(script=script, reload=False)
        #print(val)


        resp = self.session.get(link)
        if render == True:
            #resp.html.render()
            js = '''
           () => {
                  $(document).ready(function() {                        
                       $("#comments-more").click();
                       $(".button--comments").click();
                       $("#comments-comments-label").click();
                       $(".button--comments").text("kika8");
                  })
            }
            '''

            #js = '''
            #() => {
            #    $(".button--comments").text("kika8");
            #    return {
            #        source: document.body.innerHTML,
            #   }
            #}
            '''

            #js = '''
            #const item = document.getElementsByClassName("button--comments");
            #if(item) {
            # item.click()
            #}
            #'''
            resp.html.render(sleep=2, script=js, reload=True)#wait=2, sleep=4, script=js, reload=True 
        return resp

    def saveHtml(self, data, dir, fileName=""):
        timestamp = time.time()
        if not os.path.exists(dir):
            os.makedirs(dir)

        fName = fileName+"_"+str(timestamp)+".html"
        path = dir + "/" + fName
        with open(path, "w") as f:
            f.write(data)
            print("HTML SAVED AT: " + dir + "/" + fName)
        return path

    def extractLinks(self, resp):
        links = resp.html.absolute_links

        for link in links:
            if link not in self.totalLinks and link[:4] == "http":
                try:
                    if self.BASE_URL != "":
                        originalUrl = link.split(self.BASE_URL, 1)[1]
                        domain = originalUrl.split("/", 1)[1].replace("https://", "").replace("http://", "").replace("www", "").split("/", 1)[0]
                    else:
                        originalUrl = link
                        domain = originalUrl.replace("https://", "").replace("http://", "").replace("www", "").split("/", 1)[0]

                    #if not an external link
                    #note: can be a sub-domain like: desporto.publico.pt in the publico.pt main domain
                    for base in self.BASE_DOMAINS:
                        if base in domain:
                            self.totalLinks.append(link)
                            with open(self.SAVE_DIR + "totalLinks.txt", "a+") as f:
                                f.write(link+"\n")
                            print("EXTRACTED LINK: " + link)
                except:
                    print("EXCEPTION extractLinks failed: " + link)
                    with open(self.SAVE_DIR + "failedLinks.txt", "a+") as f:
                        f.write(link+"\n")


    #NOT USED, I created a txt extractedLinks.txt instead for persistent storage
    """def loadDoneFiles(self):
        doneFiles = tools.getListOfFiles(os.path.abspath(self.SAVE_DIR))
        print("== LOADING ALREADY DONE FILES ==")
        for f in doneFiles:
            link = f.rsplit("/",1)[1].rsplit("_", 1)[0].replace("\\","/")

            if len(link) <= 220:#path names can't be more than 255, so we limited the link to 220, if longer we can't know
                #if link not in self.savedLinks:
                self.savedLinks.append(link)
                print("Link added to done: " + link)
            else:
                print("---> Filename too big, can't get link: " + link)"""


htmlCrawler()

#if __name__ == '__main__':
#    main = Crawler()
