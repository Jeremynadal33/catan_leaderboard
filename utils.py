import pandas as pd
import numpy as np
import re
import smtplib, ssl

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
        split = df['scores'][indx][1:-1].replace(' ','').replace('\'','').split(',')

        scores.append(split)

    df['names'] = names
    df['scores'] = scores
    return df, unique_names


def create_players(path='home'):
    dico = {}
    if path == 'home':
        df = pd.read_csv("/Users/jeremynadal/Documents/catan_winners/data/players.csv")
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
        for player in range(games['num_players'][ind]) :
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

def add_player(df_player, player, path):
    to_append = {}
    to_append['surname'] = player.get_surname()
    to_append['first_name'] = player.get_first_name()
    to_append['last_name'] = player.get_last_name()
    to_append['mail'] = player.get_mail()
    df_player = df_player.append(to_append, ignore_index=True)

    df_player.to_csv(path, index = False)
    return df_player

def save_game(df_games, game, path):
    to_append = {}
    to_append['num_players'] = game.get_num_players()
    to_append['names'] = game.get_names()
    to_append['scores'] = game.get_scores()
    to_append['date'] = game.get_date()
    to_append['longest_road'] = game.get_longest_road()
    to_append['largest_army'] = game.get_largest_army()
    to_append['to_win'] = game.get_to_win()
    to_append['extension'] = game.get_extension()
    to_append['group'] = game.get_group()

    df_games = df_games.append(to_append, ignore_index=True)
    df_games.to_csv(path, index = False)
    send_game_mail(game)
    return True

def send_game_mail(game):
    # on rentre les renseignements pris sur le site du fournisseur
    smtp_address = 'smtp.gmail.com'
    smtp_port = 465
    # on rentre les informations sur notre adresse e-mail
    email_address = 'streamlitmailsender@gmail.com'
    email_password = 'sEzju1-zoqcex-wuzjyj'
    # on rentre les informations sur le destinataire
    email_receiver = 'streamlitmailsender@gmail.com'
    # on crée la connexion
    context = ssl.create_default_context()
    text = "num_players: " + str(game.get_num_players())
    text += "\nnames \t=\t" + str(game.get_names())
    text += "\nscores \t=\t" + str(game.get_scores())
    text += "\ndate \t=\t" + str(game.get_date())
    text += "\nlongest_road \t=\t" + str(game.get_longest_road())
    text += "\nlargest_army \t=\t" + str(game.get_largest_army())
    text += "\nto_win \t=\t" + str(game.get_to_win())
    text += "\nextension \t=\t" + str(game.get_extension())
    text += "\ngroup \t=\t" + str(game.get_group())
    text += "\n\nTO APPEND \n\n"
    text += str(game.get_num_players())+',"'+str(game.get_names())+'","'+str(game.get_scores())+'",'
    text += str(game.get_date())+','+str(game.get_longest_road())+','+str(game.get_largest_army())+','
    text += str(game.get_to_win())+','+str(game.get_extension())+','+str(game.get_group())

    print(text)


    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.login(email_address, email_password)
    server.sendmail(email_address, email_receiver, text)
    server.quit()
    # with smtplib.SMTP_SSL(smtp_address, smtp_port, context=context) as server:
    #     # connexion au compte
    #     server.login(email_address, email_password)
    #     # envoi du mail
    #
    #     server.sendmail(email_address, email_receiver, text)

if __name__ == '__main__':
    import datetime
    data = pd.read_csv("/Users/jeremynadal/Documents/catan_winners/data/database.csv")
    assert np.all(data.columns == ['num_players', 'names', 'scores', 'date', 'longest_road', 'largest_army', 'to_win', 'extension','group']), "Columns of the .csv file must be : ['num_players', 'names', 'scores', 'date', 'longest_road', 'largest_army', 'to_win', 'extension','group']"
    data['extension'] = data['extension'].fillna('Base game')

    data, players = reform_arrays(data)
    # players = create_players()
    # print(players)
    print(data)
    players = update_players_from_db(players, data)
    print(players)

    print(type(players))
    print(players.values())
    game = Game(num_players=3, names=['a','b','c'], scores=[1,1,1], date=datetime.date(2021, 3, 22), longest_road=1, largest_army=1, to_win = 10, extension = 'Base game', group = 'LPMC')
    send_game_mail(game)
    # test = []
    # for key, value in players.items():
    #     test.append(value)
    #     print(value.display())
    # print('_________________________________________')
    # test.sort(key=lambda x: x.get_win()/x.get_num_games(), reverse=True)
    # print(test)
    # for t in test :
    #     print(t.display())
