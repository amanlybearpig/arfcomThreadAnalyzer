from __future__ import annotations
import re
import argparse
import requests
from bs4 import BeautifulSoup

import sqlite3
from sqlite3 import Error

import pandas as pd

import seaborn as sb

import matplotlib.pyplot as plt


def sql_connection(db) -> sqlite3.Connection:
    try:
        con = sqlite3.connect(db)
        return con
    except Error:
        print(Error)
        
def sql_table(con) -> None:
    cursorObj = con.cursor()
    
    cursorObj.execute("CREATE TABLE posts(id integer PRIMARY KEY, author text, time text, postText text, page integer)")
    
    con.commit()
    
def sql_insert(con, entities) -> None:
    cursorObj = con.cursor()
    
    cursorObj.execute('INSERT INTO posts(id, author, time, postText, page) VALUES(?, ?, ?, ?, ?)', entities)
    
    con.commit()
    
class Post():
    def __init__(self, post, pagenum) -> None:
        self.id = None
        self.page = int(pagenum)
        self.author = None
        self.time = None
        self.text = None
        
        if not post:
            return None
        
        idNumPost = post.find_all('div', class_='small-2 large-6 columns text-right')
        for idv in idNumPost:
            idf = re.search('[\#[0-9]+]', idv.text)
            if idf:
                if idf.group()[0]=='[':
                    self.id = 50*(int(pagenum)-1) + int(idf.group()[2:-1])
        
        # If we can't find a post id, this isn't a post
        if not self.id:
            return None
        
        # Check for anchor tag with author
        try:
            self.author = post.find('a').text.strip()
        # If we can't find it then this is not a valid post
        except AttributeError:
            return None
        
        if len(self.author) <= 0:
            return None
        
        # Do similar process for post time, get time, return None if not found
        try:
            # Keep time as a string for now
            timestr = post.find('div', class_='timestamp').contents[1].text.strip()
            self.time = " ".join(timestr.split()[1:-1])
        except IndexError:
            print('Post time not found')
            return None
        except AttributeError:
            print('Post time not found')
            return None
        
        if len(self.time) <= 0:
            # One final check of time
            return None
            
        # lastly get post text in similar manner, return None if not found
        try:
            self.text = post.find('div', class_='body').text.strip()
        except KeyError:
            return None
        
        # Don't return None for len(text) == 0, it may be an img or something 
        # stripped but is still a valid post

class ArfcomThread():
    
    def __init__(self, databaseName) -> None:
        
        self.database = databaseName
        conn = sqlite3.connect(databaseName)
        df = pd.read_sql(sql="SELECT * FROM posts", con=conn, parse_dates=['time'])
        print(f'Top posters in {self.database.split(".")[0]}:\n{self.getTopPosters(df)}')
        self.plotPostsPerDay(df)
  

    def getTopPosters(self, threadDataFrame) -> list:

        topposters = threadDataFrame['author'].value_counts()
        return topposters[0:10]

    def plotPostsPerDay(self, threadDataFrame) -> None:

        threadDataFrame['date'] = pd.to_datetime(threadDataFrame['time'])

        ppd = threadDataFrame['date'].dt.floor('d').value_counts().rename_axis('date')
        
        linecolor = sb.color_palette('Paired')[1] # Dark2
        areacolor = sb.color_palette('Paired')[0] #Pastel1 2  #Accent
        
        ax = ppd.plot(color=areacolor, kind='area', lw=2, figsize=(12,9), title=f'Posts Per Day for {self.database.split(".")[0]} Thread') #,

        ppd.plot(ax=ax, color=linecolor, lw=2, figsize=(12,9))

        plt.ylabel('Posts per Day')
        plt.xlabel('Date')
        plt.show()

    
    @classmethod
    def download(cls, threadPage, dbName=None) -> ArfcomThread:
        if not dbName:
            dbName = f'{threadPage.split("/")[-3]}.db'

        session = requests.Session()
        sqlName = f'{dbName}.db'
        sqlCon = sql_connection(sqlName)
        
        sql_table(sqlCon)
    
        lastPage = 1000
    
        page = 1
        print('Beginning download and processing...')
        while page <= lastPage:
            # Simple output while running
            if page%10 == 0: print('Analyzing page', page)
            
            # First page has different config than remainder
            if page == 1:
                url = threadPage
            else:
                url = f'{threadPage}?page={page}'
    
            # Get html data from page
            response = session.get(url)
            
            # Analyze data
            soup = BeautifulSoup(response.text, 'html.parser')
            
            if page == 1:
                # get last page
                lastPage = int(soup.find('select', class_='pages').text.strip().split()[-1])
                print(f'There are a total of {lastPage} pages to analyze')
    
            divsFound = soup.find_all('div', class_='expanded row')
            
            # Loop over possible posts
            for post in divsFound:
                if post:
                    # Create post instance
                    newpost = Post(post, pagenum=page)
                    # Double check all post components are present and insert into db
                    if newpost.author and newpost.time and newpost.text:
                        postEntities = (newpost.id, newpost.author, newpost.time, newpost.text, newpost.page)
                        sql_insert(sqlCon, postEntities)
            page += 1
        print('Completed webpage parsing')
        return cls(sqlName)
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download arfcom thread arguments')
    parser.add_argument('thread_link', help='Link to first page of thread')
    parser.add_argument('--databaseName', required=False, help='Name of database file')

    args = parser.parse_args()
    ArfcomThread.download(args.thread_link, args.databaseName)

