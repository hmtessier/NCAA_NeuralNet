# -*- coding: utf-8 -*-
"""
Created on Sat Mar  2 17:18:04 2019

@author: Henry
"""

import pandas as pd
import scipy.stats
from sklearn import linear_model
import scipy
import warnings
import requests
import numpy as np
import re
import datetime
import math
warnings.filterwarnings("ignore")
from bs4 import BeautifulSoup
from selenium import webdriver

def Scrape_All():
    # Base url, and a lambda func to return url for a given year
    base_url = 'http://kenpom.com/index.php'
    url_year = lambda x: '%s?y=%s' % (base_url, str(x) if x != 2019 else base_url)

    # Create a method that parses a given year and spits out a raw dataframe
    def import_raw_year(year):
    
        f = requests.get(url_year(year))
        soup = BeautifulSoup(f.text, "lxml")
        table_html = soup.find_all('table', {'id': 'ratings-table'})
        
        # Weird issue w/ <thead> in the html
        # Prevents us from just using pd.read_html
        # Let's find all the thead contents and just replace/remove them
        # This allows us to easily put the table row data into a dataframe using panda
        thead = table_html[0].find_all('thead')

        table = table_html[0]
        for x in thead:
            table = str(table).replace(str(x), '')

        df = pd.read_html(table)[0]
        df['year'] = year
        return df
    

    # Import all the years into a singular dataframe
    df = None
    pickyear = '2019'
    print("")
    print("Gathering most recent statistics...")
    df = pd.concat( (df, import_raw_year(pickyear)), axis=0) 

    # Column rename based off of original website
    df.columns = ['Rank', 'Team', 'Conference', 'W-L', 'AdjEM', 
             'AdjustO', 'AdjustO Rank', 'AdjustD', 'AdjustD Rank',
             'AdjustT', 'AdjustT Rank', 'Luck', 'Luck Rank', 
             'SOS_Pyth', 'SOS Pyth Rank', 'SOS OppO', 'SOS OppO Rank',
             'SOS OppD', 'SOS OppD Rank', 'NCSOS Pyth', 'NCSOS Pyth Rank', 'Year']
             
    # Lambda that returns true if given string is a number and a valid seed number (1-16)
    valid_seed = lambda x: True if str(x).replace(' ', '').isdigit() \
                and int(x) > 0 and int(x) <= 16 else False

    # Use lambda to parse out seed/team
    df['Seed'] = df['Team'].apply(lambda x: x[-2:].replace(' ', '') \
                              if valid_seed(x[-2:]) else np.nan )

    df['Team'] = df['Team'].apply(lambda x: x[:-2] if valid_seed(x[-2:]) else x)

    # Split W-L column into wins and losses
    df['Wins'] = df['W-L'].apply(lambda x: int(re.sub('-.*', '', x)) )
    df['Losses'] = df['W-L'].apply(lambda x: int(re.sub('.*-', '', x)) )
    df.drop('W-L', inplace=True, axis=1)


    df=df[[ 'Year', 'Rank', 'Team', 'Conference', 'Wins', 'Losses', 'Seed','AdjEM', 
             'AdjustO', 'AdjustO Rank', 'AdjustD', 'AdjustD Rank',
             'AdjustT', 'AdjustT Rank', 'Luck', 'Luck Rank', 
             'SOS_Pyth', 'SOS Pyth Rank', 'SOS OppO', 'SOS OppO Rank',
             'SOS OppD', 'SOS OppD Rank', 'NCSOS Pyth', 'NCSOS Pyth Rank']]
             
    df.Team = df.Team.str.rstrip()
    df.Team = df.Team.str.replace('.', '')

    df['WLPercentage'] = df.Wins / (df.Losses + df.Wins)
    df['Name'] = df.Team
    df = df.set_index('Name')

    df.to_csv('kpom19.csv')
    
    """
    # Massey scrape and text file creation
    page = requests.get('https://www.masseyratings.com/scores.php?s=305972&sub=11590&all=1')
    
    soup = BeautifulSoup(page.text, 'html.parser')
    strsoup = str(soup)
    indx = strsoup.find('2018')
    strsoup = strsoup[indx:]
    endindx = strsoup.find('Games')
    endindx = endindx - 2
    strsoup = strsoup[:endindx]

    if re.search("amp;", strsoup):
        r = re.compile(r"amp;")
        strsoup = r.sub(r'', strsoup)
    if re.search(";", strsoup):
        r = re.compile(r";")
        strsoup = r.sub(r'', strsoup)

    text_file = open("games19.txt", "w")
    text_file.write(strsoup)
    text_file.close()
    """
    
    # Clean data from MasseyRatings (formatted text file)
    gamesorig = pd.read_table('games19.txt', header = None, names = ['orig'])
    games = gamesorig
    games['date'] = games.orig.str[0:10]
    games['t1home'] = games.orig.str[11:12] 
    games['team1'] = games.orig.str[12:36]
    games.team1 = games.team1.str.rstrip()
    games['score1'] = games.orig.str[36:40]
    games['t2home'] = games.orig.str[40:41]
    games['team2'] = games.orig.str[41:65]
    games.team2 = games.team2.str.rstrip()
    games['score2'] = games.orig.str[65:69]
    games['playoffot'] = games.orig.str[69:73]
    games['playoff'] = games['playoffot'].str.startswith('P')
    games['ot'] = games['playoffot'].str.contains('O')
    games['t1home'] = games['t1home'].str.contains('@')
    games['t2home'] = games['t2home'].str.contains('@')
    games = games[['date','team1','team2','score1','score2','t1home','t2home','playoff','ot']]

    # Read KPom data to combine (from randomfrestdatacollectionKPom.py)
    kpom = pd.read_csv('kpom19.csv')
    kpomclean = kpom[['Team','AdjEM','AdjustO','AdjustD','AdjustT','Luck','SOS_Pyth','WLPercentage']]

    # Load massey -> kenpom names dictionary csv
    namesdict = pd.read_csv('namedict.csv')
    lookup = dict(zip(namesdict.massey, namesdict.kpom))

    # Convert massey names to kpom names
    games.team1 = games.team1.map(lookup)
    games.team2 = games.team2.map(lookup)

    # Drop all games against non D1 teams (not in dictionary)
    games = games.dropna()
    games = games.reset_index(drop = True)

    pts3 = requests.get('https://www.teamrankings.com/ncaa-basketball/stat/percent-of-points-from-3-pointers')
    ptsft = requests.get('https://www.teamrankings.com/ncaa-basketball/stat/percent-of-points-from-free-throws')
    pt3pct = requests.get('https://www.teamrankings.com/ncaa-basketball/stat/three-point-pct')
    pt2pct = requests.get('https://www.teamrankings.com/ncaa-basketball/stat/two-point-pct')
    ftpct = requests.get('https://www.teamrankings.com/ncaa-basketball/stat/free-throw-pct')
    rebound = requests.get('https://www.teamrankings.com/ncaa-basketball/stat/total-rebounding-percentage')
    block = requests.get('https://www.teamrankings.com/ncaa-basketball/stat/block-pct')
    steal = requests.get('https://www.teamrankings.com/ncaa-basketball/stat/steals-perpossession')
    asttorat = requests.get('https://www.teamrankings.com/ncaa-basketball/stat/assist--per--turnover-ratio')
    foulspergame = requests.get('https://www.teamrankings.com/ncaa-basketball/stat/personal-fouls-per-game')

    statlist = [pts3,ptsft,pt3pct,pt2pct,ftpct,rebound,block,steal,asttorat,foulspergame]
    statnames = ['pts3','ptsft','pt3pct','pt2pct','ftpct','rebound','block','steal','asttorat','foulspergame']


    full = pd.DataFrame()
    count = 0
    for stat in statlist:
        soup = BeautifulSoup(stat.text, 'html.parser')
        bballtwo = pd.DataFrame()
        for tr in soup.find_all('tr')[1:]:
            tds = tr.find_all('td')
            temp = pd.DataFrame([[tds[1].text,tds[2].text]])
            bballtwo = bballtwo.append(temp)
        bballtwo.columns = ['team',statnames[count]]
        count += 1
        if count == 1:
            full = bballtwo
        else:    
            full = full.merge(bballtwo, how = 'left')

    advstatnames = pd.read_csv('advstatnames.csv')
    lookup2 = dict(zip(advstatnames.original, advstatnames.kpom))

    # Convert advstat names to kpom names
    full.team = full.team.map(lookup2)

    full.pts3 = full['pts3'].str.replace(r'%','').astype('float')
    full.ptsft = full['ptsft'].str.replace(r'%','').astype('float')
    full.pt3pct = full['pt3pct'].str.replace(r'%','').astype('float')
    full.pt2pct = full['pt2pct'].str.replace(r'%','').astype('float')
    full.ftpct = full['ftpct'].str.replace(r'%','').astype('float')
    full.rebound = full['rebound'].str.replace(r'%','').astype('float')
    full.block = full['block'].str.replace(r'%','').astype('float')
    full.steal = full['steal'].str.replace(r'%','').astype('float')

    # Merge kenpom data with advanced stats
    kpomclean = pd.merge(kpomclean, full, how = "left", left_on = ['Team'], right_on = ['team'])
    kpomclean = kpomclean.drop(columns = 'team')

    return kpomclean, games

def getteam(team, games, kpomclean):
    opp = []
    result = []
    home = []
    neutral = []
    teamsgames = games[(games['team1'] == team) | (games['team2'] == team)]
    if len(teamsgames) == 0:
        return('Team not found')
    else:
        for index, row in teamsgames.iterrows():
            if row.team1 == team:
                opp += [row.team2]
                result += [int(row.score1) - int(row.score2)]
                if row.t1home == True:
                    home += [True]
                else:
                    home += [False]
            elif row.team2 == team:
                opp += [row.team1]
                result += [int(row.score2) - int(row.score1)]
                if row.t2home == True:
                    home += [True]
                else:
                    home += [False]
            if (row.t1home == False) & (row.t2home == False):
                neutral += [True]
            else:
                neutral += [False]
        teamsgames['opp'] = opp
        teamsgames['result'] = result
        teamsgames['home'] = home
        teamsgames['neutral'] = neutral
        teamsgames = teamsgames[['opp','result','home','neutral']]
        teamsgames = teamsgames.reset_index(drop = True)
        merged = pd.merge(teamsgames, kpomclean, how = 'left', left_on = ['opp'], right_on = ['Team'])
        merged = merged.drop(columns = 'Team')
        return(merged)

def getopp(team, location, kpomclean):
    teamtouse = kpomclean[kpomclean.Team == team]
    if location == 'neut':
        teamtouse['neutral'] = True
        teamtouse['home'] = False
    elif location == 'home':
        teamtouse['neutral'] = False
        teamtouse['home'] = True
    elif location == 'away':
        teamtouse['neutral'] = False
        teamtouse['home'] = False 
    teamtouse = teamtouse[['home','neutral','AdjEM','AdjustO','AdjustD','AdjustT','Luck','SOS_Pyth','WLPercentage',
                           'pts3','ptsft','pt3pct','pt2pct','ftpct','rebound','block','steal','asttorat','foulspergame']]
    return(teamtouse)
