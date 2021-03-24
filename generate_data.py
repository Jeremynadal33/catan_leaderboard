import random
import numpy as np
import pandas as pd
import datetime
from classes import *

def random_date(start_date=None, end_date=None):
    if start_date == None : start_date = datetime.date(2021, 2, 24) #YYYY, MM, DD

    if end_date == None: end_date = datetime.date(2021, 3, 22)

    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    random_date = start_date + datetime.timedelta(days=random_number_of_days)

    return random_date

players = ['Jeremynadal', 'Lousgarcia', 'Marinevialemaringe', 'Marineduret', 'Melinelarrieu', 'Louisgodin']

to_win = 10
data = pd.DataFrame(columns = ['num_players', 'names', 'scores', 'date', 'longest_road', 'largest_army', 'to_win', 'extension','group'])
for i in range(100):
    num_players = np.random.randint(3,6)
    names = []
    scores = np.zeros(num_players)
    #Randomly select player names
    while(len(names)<num_players):
        name = np.random.choice(players)
        if name not in names : names.append(name)
    #Randomly choose who gets longest_road and largest_army
    longest_road = np.random.randint(num_players)
    largest_army = np.random.randint(num_players)
    scores[longest_road] += 2
    scores[largest_army] += 2
    #Randomly put scores
    while (np.all(scores<10)):
        scores[ np.random.randint(num_players) ] += 1
    game = Game( num_players, names, scores, random_date(), longest_road, largest_army)
    data.loc[i] = list(game.get_game())
data.to_csv('/Users/jeremynadal/Documents/catan_winners/database.csv', index = False)
