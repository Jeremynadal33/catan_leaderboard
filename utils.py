import pandas as pd
import numpy as np
import re

from classes import *

def reform_arrays(df):
    unique_names = {}
    names = []
    scores = []
    for indx in range(df.shape[0]):
        split = df['names'][indx][1:-1].replace('\'', '').replace(' ','').split(',')
        names.append(split)
        for s in split :
            if s not in unique_names.keys() : unique_names[s] = Player(s)
        split = df['scores'][indx][1:-1].replace(' ','').split('.')[:-1]
        scores.append(split)

    df['names'] = names
    df['scores'] = scores
    return df, unique_names


def create_players(path='home'):
    dico = {}
    if path == 'home':
        df = pd.read_csv("/Users/jeremynadal/Documents/catan_winners/players.csv")
        print(df.columns)
        for ind in range(df.shape[0]):
            player = Player(first_name = df['first_name'][ind] ,
                            last_name = df['last_name'][ind],
                            surname = df['surname'][ind],
                            mail = df['mail'][ind])
            dico[player.get_surname()] = player
        return dico
    else :
        print('not implemented for the moment')
        return dico

def update_players_from_db(players, games):
    for ind in range(games.shape[0]):
        for player in range(games['num_player'][ind]) :
            players[games['names'][ind][player]].add_game()
            players[games['names'][ind][player]].add_points( int(games['scores'][ind][player]) )
        longest = games['longest_road'][ind]
        players[games['names'][ind][longest]].add_longest()
        largest = games['longest_road'][ind]
        players[games['names'][ind][largest]].add_largest()
        won = np.argmax(games['scores'][ind])
        players[games['names'][ind][won]].add_win()

    return players

def get_players_dataframe(players):
    df = pd.DataFrame(columns=['Surname', 'Number of wins', 'Total games', 'Total of points', 'Num. longest road', 'Num. largest army'])
    for player in players.values():
        df = df.append(player.to_dict(), ignore_index = True)
        
    df['Avg number of points'] = (df['Total of points']/df['Total games']).astype('float64').round(2)
    df['Winning rate'] = (df['Number of wins']/df['Total games']).astype('float64').round(2)
    df['Longest road rate'] = (df['Num. longest road']/df['Total games']).astype('float64').round(2)
    df['Largest army rate'] = (df['Num. largest army']/df['Total games']).astype('float64').round(2)
    return df



if __name__ == '__main__':
    data = pd.read_csv("/Users/jeremynadal/Documents/catan_winners/database.csv")
    assert np.all(data.columns == ['num_player', 'names', 'scores', 'date', 'longest_road', 'largest_army', 'to_win', 'extension']), "Columns of the .csv file must be : ['num_player', 'names', 'scores', 'date', 'longest_road', 'largest_army', 'to_win', 'extension']"
    data['extension'] = data['extension'].fillna('Base game')

    data, players = reform_arrays(data)
    # players = create_players()
    # print(players)
    players = update_players_from_db(players, data)
    print(players)

    print(type(players))
    print(players.values())
    # test = []
    # for key, value in players.items():
    #     test.append(value)
    #     print(value.display())
    # print('_________________________________________')
    # test.sort(key=lambda x: x.get_win()/x.get_num_games(), reverse=True)
    # print(test)
    # for t in test :
    #     print(t.display())
