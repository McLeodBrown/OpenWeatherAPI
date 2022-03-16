# -*- coding: utf-8 -*-
"""
Created on Mon Aug 30 14:24:15 2021

@author: cmcle
"""
# Import packages
import pandas as pd
import numpy as np
import requests 
from datetime import datetime
from datetime import timedelta
from datetime import date
#pd.options.display.float_format = '{:, .2f}'.format
# Cities to query
cities = ['Anchorage,Alaska,USA', 'Chennai,India','Jiangbei,China', 'Kathmandu,Nepal', 
          'Kothagudem,India', 'Lima,Peru', 'Manhasset,NewYork,USA', 'Mexico City,Mexico', 'Nanaimo,Canada', 'Peterhead,Scotland', 'Polevskoy,Russia',
          'Round Rock,Texas,USA', 'Seoul,SouthKorea', 'Solihull,England', 'Tel Aviv,Israel' ]
# Make current date
cur_dt = date.today()
# Create three empty dictionaries
# First to use for the 'list' dictionary
d = {}
# Second to use for the 'city' dictionary
e = {}
# Third for us to combine them
f = {}
def pull_weather(city):
    # Use API key
    api_key = 'c78b9aca65b1dfe6a0d0205666def0fd' 
    # List URL
    URL = 'https://api.openweathermap.org/data/2.5/forecast?'
    # Variable 'city' allow us to loop
    URL = URL + 'q=' + city + '&appid=' + api_key
    response = requests.get(URL)
    # Put JSON into variable
    data = response.json()
    # Begin pulling from dictionaries
    d[city] = pd.DataFrame.from_dict(pd.json_normalize(data['list']), orient = 'columns')
    e[city] = pd.DataFrame.from_dict(pd.json_normalize(data['city']), orient = 'columns')
    f[city] = pd.concat([d[city], e[city]], axis = 1)
    # Subset on columns
    f[city] = f[city][['dt_txt', 'main.temp_min', 'main.temp_max', 'name', 'country', 'timezone']]
    # Fill down empty rows
    f[city] = f[city].ffill()
    # Set initial value for local_time that we will overwrite
    f[city][['local_time']] = 0
    # Loop to identify if current day matches tomorrow day and, if it does, drop that row
    for t in range(0, len(f[city]['dt_txt'])):
        dt_str = f[city]['dt_txt'][t]
        dt_tm = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
        tz_offset = f[city]['timezone'][t]
        dt_tm = dt_tm + timedelta(seconds = tz_offset)
        local_str = dt_tm.strftime('%Y-%m-%d %H:%M:%S')
        f[city]['local_time'][t] = local_str
        if cur_dt.day == dt_tm.day:
            f[city] = f[city].drop(t)
        else:
            continue
    # Trim
    f[city]['dt_txt'] = f[city]['dt_txt'].str[:10]
    # Set as str and trim
    f[city]['local_time'] = f[city]['local_time'].astype(str)
    f[city]['local_time'] = f[city]['local_time'].str[:10]
    # Convert columns to Celsius
    f[city]['main.temp_min'] = f[city]['main.temp_min'] - 273.15
    f[city]['main.temp_max'] = f[city]['main.temp_max'] - 273.15
    # Find minimum of each day
    dfmin = f[city].groupby('local_time')['main.temp_min']
    f[city]['minimum_temp'] = dfmin.transform('min')
    # Find maximum of each day
    dfmax = f[city].groupby('local_time')['main.temp_max']
    f[city]['maximum_temp'] = dfmax.transform('max')
    # Drop duplicates
    f[city] = f[city].drop_duplicates(subset=['minimum_temp', 'maximum_temp']).reset_index(drop=True)
    # Create new columns that take values from minimum and maximum of each day
    for z in range(0, len(f[city]['dt_txt'])):
        f[city]['Min ' + str(z + 1)] = f[city]['minimum_temp'][z]
        f[city]['Max ' + str(z + 1)] = f[city]['maximum_temp'][z]
    f[city] = f[city].iloc[:, 9:]
    # Calculate average columns
    if set(['Min 5', 'Max 5']).issubset(f[city].columns):
        f[city]['Min Avg'] = round(f[city][['Min 1', 'Min 2', 'Min 3', 'Min 4', 'Min 5']].apply(np.mean).mean(), 2)
        f[city]['Max Avg'] = round(f[city][['Max 1', 'Max 2', 'Max 3', 'Max 4', 'Max 5']].apply(np.mean).mean(), 2)
    else:
        f[city]['Min Avg'] = round(f[city][['Min 1', 'Min 2', 'Min 3', 'Min 4']].apply(np.mean).mean(), 2)
        f[city]['Max Avg'] = round(f[city][['Max 1', 'Max 2', 'Max 3', 'Max 4']].apply(np.mean).mean(), 2)
    # Drop duplicates
    f[city] = f[city].drop_duplicates().reset_index(drop=True)
    return f[city]
# Pull city info  
for i in cities:
    pull_weather(i)   
# Pull dataframes out of dictionaries and combine them    
df = pd.concat(f.values(), keys = f.keys()).reset_index().drop(['level_1'], axis = 1).rename(columns = {'level_0': 'City'})  
# Hard code cities into City column to match formatting
df['City'] = ['Anchorage, USA', 'Chennai, India', 'Jiangbei, China',
              'Kathmandu, Nepal', 'Kothagudem, India', 'Lima, Peru',
              'Manhasset, USA', 'Mexico City, Mexico', 'Nanaimo, Canada',
              'Peterhead, Scotland', 'Polveskoy, Russia', 'Round Rock, USA',
              'Seoul, South Korea', 'Solihull, England', 'Tel Aviv, Isreal']
# Reorder columns
df = df[['City', 'Min 1', 'Max 1', 'Min 2', 'Max 2', 'Min 3', 'Max 3',
         'Min 4', 'Max 4', 'Min 5', 'Max 5', 'Min Avg', 'Max Avg']]
# Export to CSV
df.to_csv(r'C:\Users\cmcle\Documents\AA 502\Python\temp.csv', index = False, float_format='%.2f')