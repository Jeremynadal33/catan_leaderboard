import pandas as pd
import numpy as np
import re
import smtplib, ssl
from email.message import EmailMessage
from classes import *
import os
# import requests
# from PIL import Image
#
# from io import BytesIO
# import streamlit as st

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

def upload_img(img, surname):
    file_name = surname.replace("\'","") +'.jpg'
    path = 'data/temp/'+file_name

    with open(path, "wb") as f :
        f.write(img.getbuffer())
    if os.path.exists(path):
        os.system("aws s3 cp "+path+' '+"s3://catan-bucket/public/"+file_name)
        os.system("aws s3api put-object-acl --acl public-read --bucket catan-bucket  --key public/"+file_name)
    # pic_path = "https://s3-eu-west-3.amazonaws.com/catan-bucket/public/" + surname.replace("\'","") + ".jpg"
    #
    # default = "https://s3-eu-west-3.amazonaws.com/catan-bucket/public/default.jpg"
    #
    # try:
    #     response = requests.get(pic_path)
    #     img = Image.open(BytesIO(response.content))
    #     st.image(img, width = 250, caption = surname)
    # except Exception as e:
    #     response = requests.get(default)
    #     img = Image.open(BytesIO(response.content))
    #     st.image(img, width = 250, caption = surname)



def get_players_from_subset_games(df):
    unique_names = {}
    names = []
    scores = []
    for indx in df.index:
        for name in df['names'][indx] :
            if name not in unique_names.keys() : unique_names[name] = Player(name)

    return unique_names


def send_mail(to_address, subject, text):
    msg = EmailMessage()
    msg.set_content(text)

    msg['Subject'] = subject
    msg['From'] = "streamlitmailsender@gmail.com"
    msg['To'] = to_address

    # Send the message via our own SMTP server.
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login("streamlitmailsender@gmail.com", "sEzju1-zoqcex-wuzjyj")
    server.send_message(msg)
    server.quit()


def send_daily_mail(games):
    #print('in daily mail')
    player = Player(surname= 'JMD', first_name = 'Jerem', last_name = 'Nadal', mail = 'jjjnadal33@gmail.com')
    send_welcome_email(player)



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
    for ind in games.index:
        for player in range(games['num_players'][ind]) :
            players[games['names'][ind][player]].add_game()
            players[games['names'][ind][player]].add_points( int(games['scores'][ind][player]) )
        longest = games['longest_road'][ind]
        if longest==longest : players[games['names'][ind][int(longest)]].add_longest()
        largest = games['longest_road'][ind]
        if largest==largest : players[games['names'][ind][int(largest)]].add_largest()
        scores = [int(score) for score in games['scores'][ind]]
        won = np.argmax(scores)
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

def add_player(df_player, player, path, img):
    to_append = {}
    to_append['surname'] = player.get_surname()
    to_append['first_name'] = player.get_first_name()
    to_append['last_name'] = player.get_last_name()
    to_append['mail'] = player.get_mail()
    df_player = df_player.append(to_append, ignore_index=True)

    df_player.to_csv(path, index = False)

    if img is not None:
        upload_img(img, player.get_surname())

    send_welcome_email(player)
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

    if to_append['group'] == "": to_append['group'] = None

    df_games = df_games.append(to_append, ignore_index=True)
    df_games.to_csv(path, index = False)
    send_game_mail(game)
    return True

def send_welcome_email(player):
    text = "Welcome " + str(player.get_surname())+".\n"
    text += "The Catan leaderboard application support is happy to count you as a Catan settler.\nWe are looking forward to play Catan with you. You can add games at the following address : http://52.47.40.217:8501"
    text += "\n\nKind regards,\Catan leaderboard application support."

    send_mail(to_address = player.get_mail(), subject='Welcome to Catan Leaderboard', text= text)

    text = "There is a new Catan player\n"
    text += "first_name \t" + str(player.get_first_name()) + "\n"
    text += "last_name \t" + str(player.get_last_name()) + "\n"
    text += "surname \t" + str(player.get_surname()) + "\n"
    text += "mail \t" + str(player.get_mail()) + "\n"

    text += "TO APPEND \n\n "
    text += str(player.get_first_name())+','+str(player.get_last_name())+','
    text += str(player.get_surname())+','+ str(player.get_mail())
    send_mail(to_address = "streamlitmailsender@gmail.com", subject='New player', text= text)

def send_game_mail(game):

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

    send_mail(to_address = 'streamlitmailsender@gmail.com', subject='New game', text= text)


if __name__ == '__main__':

    player = Player(surname= 'JMD', first_name = 'Jerem', last_name = 'Nadal', mail = 'jjjnadal33@gmail.com')
    send_welcome_email(player)
