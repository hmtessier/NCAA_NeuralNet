# -*- coding: utf-8 -*-
"""
Created on Sat Mar  2 20:06:04 2019

@author: Henry
"""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from Scrape import *
import numpy as np
import pandas as pd
import scipy
from sklearn.preprocessing import StandardScaler

kpomclean, games = Scrape_All()

def Team(team):
    return(getteam(team, games, kpomclean))

def Opp(team, loc):
    return(getopp(team, loc, kpomclean))
    
#neut, home, away options for loc
    
def neural_net(team, opp, loc):
    
    record = Team(team)
    record.home = record.home.astype(float)
    record.neutral = record.neutral.astype(float)
    
    #ignore previous times they've played each other
    record = record[record.opp != opp]
    if team == 'Duke':
        record.iloc[:25].append(record.iloc[31:])
    
    result = np.array(record[['result']]).astype(float)
    record = record.drop(columns = ['result','opp'])
    
    opponent = Opp(opp, loc)
    opponent.home = opponent.home.astype(float)
    opponent.neutral = opponent.neutral.astype(float)
    
    scaler = StandardScaler()
    scaler.fit(record)
    recordarr = scaler.transform(record)
    opponentarr = scaler.transform(opponent)
    
    
    def build_model():
        model = keras.Sequential([
                layers.Dense(200, activation=tf.nn.relu, input_shape=[19]),
                layers.Dense(10, activation=tf.nn.relu),
                layers.Dense(1)
                ])
        optimizer = tf.keras.optimizers.RMSprop(0.0005)
        model.compile(loss='mean_squared_error',
                optimizer=optimizer,
                metrics=['mean_absolute_error', 'mean_squared_error'])
        return model
    
    model = build_model()

    EPOCHS = 5000

    history = model.fit(
            recordarr, result,
            epochs=EPOCHS, verbose=0)
    hist = pd.DataFrame(history.history)
    for index, row in hist.iterrows():
        if (index % 1000 == 0):
            print(row.loss)
    
    test_predictions = model.predict(opponentarr)
    return test_predictions.tolist()[0][0]
    
def nn_get_line(tm1, tm2, tm1loc):
    tm1res = neural_net(tm1, tm2, tm1loc)
    if tm1loc == 'home':
        tm2res = neural_net(tm2, tm1, 'away')
    elif tm1loc == 'away':
        tm2res = neural_net(tm2, tm1, 'home')
    elif tm1loc == 'neut':
        tm2res = neural_net(tm2, tm1, 'neut')
    print(tm1res)
    print(tm2res)
    return((tm1res - tm2res)/2)
    
def sim(tm1, tm2, tm1loc):
    lines = []
    for x in range(8):
        val = nn_get_line(tm1,tm2,tm1loc)
        print("RESULT: ", val)
        lines += [val]
    lines.remove(max(lines))
    lines.remove(min(lines))
    return(sum(lines)/6)
    
def get_odds(line):
    odds = scipy.special.expit(line*4/25)
    return(odds)