import pandas as pd
import streamlit as st
import numpy as np
import time
from datetime import date
import datetime
import os
import requests
from PIL import Image

from io import BytesIO
from streamlit.hashing import _CodeHasher
from utils import *

import streamlit.components.v1 as components

try:
    # Before Streamlit 0.65
    from streamlit.ReportThread import get_report_ctx
    from streamlit.server.Server import Server
except ModuleNotFoundError:
    # After Streamlit 0.65
    from streamlit.report_thread import get_report_ctx
    from streamlit.server.server import Server

home_path = ["/Users/jeremynadal/Documents/catan_winners/data/database.csv","/home/ubuntu/catan_leaderboard/data/database.csv"]
player_path = ["/Users/jeremynadal/Documents/catan_winners/data/players.csv","/home/ubuntu/catan_leaderboard/data/players.csv"]

pd.options.plotting.backend = "plotly"
###################### FUNCTIONS #################
#@st.cache
def get_data(path):
    try:
        data = pd.read_csv(path)
        assert np.all(data.columns == ['num_players', 'names', 'scores', 'date', 'longest_road', 'largest_army', 'to_win', 'extension','group']), "Columns of the .csv file must be : ['num_players', 'names', 'scores', 'date', 'longest_road', 'largest_army', 'to_win', 'extension','group']"
        data['extension'] = data['extension'].fillna('Base game')
        data = data.drop_duplicates()
        return data
    except Exception as e:
        pass
    return pd.DataFrame()

#################### FOR SESSION STATE FROM ONE PAGE TO THE OTHER ###################
class _SessionState:
    def __init__(self, session, hash_funcs):
        """Initialize SessionState instance."""
        self.__dict__["_state"] = {
            "data": {},
            "hash": None,
            "hasher": _CodeHasher(hash_funcs),
            "is_rerun": False,
            "session": session,
        }

    def __call__(self, **kwargs):
        """Initialize state data once."""
        for item, value in kwargs.items():
            if item not in self._state["data"]:
                self._state["data"][item] = value

    def __getitem__(self, item):
        """Return a saved state value, None if item is undefined."""
        return self._state["data"].get(item, None)

    def __getattr__(self, item):
        """Return a saved state value, None if item is undefined."""
        return self._state["data"].get(item, None)

    def __setitem__(self, item, value):
        """Set state value."""
        self._state["data"][item] = value

    def __setattr__(self, item, value):
        """Set state value."""
        self._state["data"][item] = value

    def clear(self):
        """Clear session state and request a rerun."""
        self._state["data"].clear()
        self._state["session"].request_rerun()

    def sync(self):
        """Rerun the app with all state values up to date from the beginning to fix rollbacks."""

        # Ensure to rerun only once to avoid infinite loops
        # caused by a constantly changing state value at each run.
        #
        # Example: state.value += 1
        if self._state["is_rerun"]:
            self._state["is_rerun"] = False

        elif self._state["hash"] is not None:
            if self._state["hash"] != self._state["hasher"].to_bytes(self._state["data"], None):
                self._state["is_rerun"] = True
                self._state["session"].request_rerun()

        self._state["hash"] = self._state["hasher"].to_bytes(self._state["data"], None)

def _get_session():
    session_id = get_report_ctx().session_id
    session_info = Server.get_current()._get_session_info(session_id)

    if session_info is None:
        raise RuntimeError("Couldn't get your Streamlit Session object.")

    return session_info.session

def _get_state(hash_funcs=None):
    session = _get_session()

    if not hasattr(session, "_custom_session_state"):
        session._custom_session_state = _SessionState(session, hash_funcs)

    return session._custom_session_state

################### Rest is for the application itself #################
def display_leaderboard(state):
    cols = st.beta_columns([1,1,1])
    with cols[0]:
        choice = st.selectbox('Sort by:',['Number of wins', 'Winning rate' ,'Average number of points', 'Number of largest army', 'Number of longest road'])
    with cols[1]:
        num_display = st.number_input('Display:',1,state.players_df.shape[0],3)
    with cols[2]:
        groups = ['All']
        for g in state.games['group'].unique():
            if g==g : groups.append(g)
        group = st.selectbox("Group : ", groups)

    if group != 'All':
        games = state.games[state.games['group']==group]
        players = get_players_from_subset_games(games)

        players = update_players_from_db(players, games)
        df = get_players_dataframe(players)
    else :
        df = state.players_df
# 'Total games', 'Total of points', 'Num. longest road', 'Num. largest army'
    if choice == 'Number of wins':
        to_display = df.sort_values(['Number of wins','Avg number of points'], ascending=False)
        to_display = to_display[['Surname', 'Number of wins', 'Total games', 'Total of points', 'Num. longest road', 'Num. largest army', 'Avg number of points', 'Winning rate']][:num_display]
        st.dataframe(to_display.assign(hack='').set_index('hack'))
    elif choice == 'Winning rate':
        st.dataframe(df.sort_values(['Winning rate', 'Avg number of points'], ascending=False)[['Surname',  'Winning rate', 'Number of wins', 'Total games', 'Total of points', 'Num. longest road', 'Num. largest army', 'Avg number of points']][:num_display].assign(hack='').set_index('hack'))
    elif choice == 'Average number of points':
        st.dataframe(df.sort_values(['Avg number of points','Winning rate'], ascending=False)[['Surname', 'Avg number of points', 'Number of wins', 'Total games', 'Total of points', 'Num. longest road', 'Num. largest army', 'Winning rate']][:num_display].assign(hack='').set_index('hack'))
    elif choice == 'Number of largest army':
        st.dataframe(df.sort_values(['Num. largest army','Winning rate'], ascending=False)[['Surname', 'Num. largest army','Number of wins', 'Total games', 'Total of points', 'Num. longest road', 'Avg number of points', 'Winning rate']][:num_display].assign(hack='').set_index('hack'))
    elif choice == 'Number of longest road':
        st.dataframe(df.sort_values(['Num. longest road','Winning rate'], ascending=False)[['Surname',  'Num. longest road', 'Number of wins', 'Total games', 'Total of points', 'Num. largest army', 'Avg number of points', 'Winning rate']][:num_display].assign(hack='').set_index('hack'))

def get_top(df, col, name):
    temp = df.sort_values(col, ascending = False).reset_index()
    return round(100*temp.index[temp["Surname"] == name].tolist()[0]/df.shape[0])


def display_player(state, player):
    st.write("##")
    surname = player.get_surname()
    pic_path = "https://s3-eu-west-3.amazonaws.com/catan-bucket/public/" + surname.replace("\'","") + '.jpg'

    print(pic_path)
    default = "https://s3-eu-west-3.amazonaws.com/catan-bucket/public/" + "default.jpg"

    cols = st.beta_columns(3)
    with cols[1]:
        try:
            response = requests.get(pic_path)
            img = Image.open(BytesIO(response.content))
            st.image(img, width = 250, caption = surname)
        except Exception as e:
            response = requests.get(default)
            img = Image.open(BytesIO(response.content))
            st.image(img, width = 250, caption = surname)


    cols = st.beta_columns(3)
    with cols[0]: st.write("")
    with cols[1]: st.write('Score ')
    with cols[2]: st.write('Top ')

    t = datetime.datetime.fromtimestamp(time.time())

    if 7 <= t.hour <= 21 :
        components.html("<hr size = '1', color = black>")
    else:
        components.html("<hr size = '1', color = white>")

    df = state.players_df.copy()

    cols = st.beta_columns(3)
    with cols[0]:
        st.write("Number of games :")
        st.write("Number of wins :")
        st.write("Win rate :")
        st.write("Total num. of points :")
        st.write("Average num. of points :")
        st.write("Number of longest road :")
        st.write("Longest road rate :")
        st.write("Number of largest army :")
        st.write("Largest army rate :")
    with cols[1]:
        st.write(str(player.get_num_games()))
        st.write(str(player.get_win()))
        st.write(str(round(100*player.get_win()/player.get_num_games()))+'%')
        st.write(str(player.get_total_points()))
        st.write(str(round(player.get_total_points()/player.get_num_games(),2)))
        st.write(str(player.get_longest()))
        st.write(str(round(100*player.get_longest()/player.get_num_games()))+'%')
        st.write(str(player.get_largest()))
        st.write(str(round(100*player.get_largest()/player.get_num_games() ))+'%')
    with cols[2]:
        st.write( str(get_top(df, "Total games", surname))+'%' )
        st.write( str(get_top(df, "Number of wins", surname))+'%' )
        st.write( str(get_top(df, "Winning rate", surname))+'%' )
        st.write( str(get_top(df, "Total of points", surname))+'%' )
        st.write( str(get_top(df, "Avg number of points", surname))+'%' )
        st.write( str(get_top(df, "Num. longest road", surname))+'%' )
        st.write( str(get_top(df, "Longest road rate", surname))+'%' )
        st.write( str(get_top(df, "Num. largest army", surname))+'%' )
        st.write( str(get_top(df, "Largest army rate", surname))+'%' )


def menu_leaderboard(state):
    st.header("This is the leaderboard page")
    st.subheader("Here you can view in depth statistics on the loaded games")
    if np.any(state.games):
        st.subheader('Total number of games : {}'.format(state.games.shape[0]))
    try:
        if state.players_df != None:
            display_leaderboard(state)
        else :
            st.write('Please, load a csv file on the _Home_ page first')
    except Exception as e:
        if not state.players_df.empty :
            display_leaderboard(state)
        else:
            st.write('Please, load a csv file or add new games first.')



def menu_players(state):
    temp = None
    st.header("This is the players' page")
    st.subheader("Here you can view statistics on a selected player or add a new player")
    st.write('This page is currently on the making')
    cols = st.beta_columns([1,1,1])

    if state.players != None:
        with cols[0]:
            player = st.selectbox( "Select a player", ['']+list(state.players.keys()) )
        if player != '' :
            display_player(state, state.players[player])
    else :
        st.write('Please, load a csv file on the _Home_ page first')

    st.write("#")
    st.write("#")
    with st.beta_expander("Add new player"):
        st.subheader('Here you can add a new player. Each surname and mail adress must be unique.')

        cols = st.beta_columns([2,1])
        with cols[0]:
            st.subheader("The surname is what will be displayed on the app.")
            surname = st.text_input("Surname",value = "", max_chars=30)
            first_name = st.text_input("First name",value = "", max_chars=20)
            last_name = st.text_input("Last name",value = "", max_chars=20)
            mail = st.text_input("Mail adress",value = "", max_chars=40)
            img = st.file_uploader('Profile pic', type = ['jpg','png','jpeg','pdf'])
            player = Player(surname, first_name, last_name, mail)

        cols = st.beta_columns([3,1,1])

        with cols[0]:
            if np.all(state.players_info) != None and os.path.exists(state.player_path):
                if st.button("Save"):
                    if player.get_surname() in list(state.players_info['surname']) or player.get_surname()=="" or player.get_surname()==" ":
                        st.error("Surname must be unique and not null. Please choose another one.")
                    elif player.get_mail() in list(state.players_info['mail']) or player.get_mail()=="" or player.get_mail()==" ":
                        st.error("Mail must be unique and not null. Please choose another one.")
                    elif not re.match('[^@]+@[^@]+\.[^@]+',player.get_mail()):
                        st.error("Mail looks invalid, if it is not, please contact streamlitmailsender@gmail.com")
                    else:
                        temp = add_player(state.players_info, player, state.player_path , img)
                        st.warning("Sucessfully added {} to the players database".format(player.get_surname()))
    time.sleep(1)
    if np.all(temp) :
        state.players_info = temp

    with st.beta_expander("Warning"):
        st.warning("Each player must have its own surname and mail adress")

def menu_games(state):
    temp = False
    longest = ""
    largest = ""
    st.header("This is the Games' page")
    st.subheader("Here you can add, modify or delete a game")
    with st.beta_expander("Warning"):
        st.warning("You cannot enter a game with unregistered players")

    with st.beta_expander("Add a new game"):
        cols = st.beta_columns([1,1,1])
        with cols[0]:
            num_persons = st.slider("Number of players", 3, 6, 3, 1)
            extension = st.selectbox('Extension:',('Base game', 'Villes et chevaliers','Marins'))
        with cols[1]:
            game_date = st.date_input('Date', date.today() )
            to_win = st.number_input('Number of points to win',7,20,10)
        with cols[2]:
            group = st.text_input("Group:","")

        cols = st.beta_columns([1,1,1])
        names = []
        scores = []
        with cols[0]:
            for player in range(num_persons):
                if np.all(state.players_info) != None:
                    names.append(st.selectbox(f"Player {player+1}:",['']+[surname for surname in list(state.players_info['surname']) if surname not in names]))
                else:
                    names.append(st.text_input(f"Player {player+1}:",max_chars = 30))
        with cols[1] :
            for player in range(num_persons):
                scores.append(st.number_input(f"Score {player+1}:",0,to_win+1,0 ))


        if names[0] != "":
            longest = st.selectbox("Longest road", ['']+names)
            largest = st.selectbox("Largest army", ['']+names)

        if longest == '':
            longest = None
        else :
            longest = int(names.index(longest))


        if largest == '':
            largest = None
        else:
            largest = int(names.index(largest))

        game = Game(num_players = num_persons, names = names,
                    scores = scores , date = game_date,
                    longest_road = longest , largest_army = largest ,
                    to_win = to_win, extension = extension,
                    group = group)

        if st.button("Save"):
            if not ( np.any(np.array(game.get_scores()) >= game.get_to_win()) ) :
                st.error("No one won yet")
            elif sorted(scores)[-1] == sorted(scores)[-2]:
                st.error("A player must have more points than all others.")
            elif not np.all([False for name in names if name == ""]):
                st.error("Name(s) is(are) missing")
            else:
                st.info("Sucessfully added game to database")
                save_game(state.games, game, state.db_path)

        time.sleep(1)

    games = get_data(path = state.db_path)
    games, players = reform_arrays(games)
    players = update_players_from_db(players, games)

    state.games = games
    state.players = players
    state.players_df = get_players_dataframe(state.players)


def menu_home(state):
    games = pd.DataFrame()
    home = False
    # Home page : presentation, loading available, display of the loaded .csv and quick display of the leaderboard
    st.write("Welcome to this _easy to use_ Catan leaderboard. \n")
    st.write("Here you can see, amongst your friends, who is the best settler.")
    with st.beta_expander("Overview of the application :", expanded = False):
        st.write(
            """
    - Home:
        - Welcome page
        - See number of games and number of games per day
        - Upload your own .csv file
        - See the current .csv file
    - Leaderboard:
        - Display number of games
        - Choose on what players must be ranked
        - Display table of winners
    - Players:
        - Select a player to see in depth statistics (ondoing)
        - Add a new player
    - Games:
        - Add new games to database
        - Modify or delete a game
            """
        )

    if state.players != None:
        state.players_df = get_players_dataframe(state.players)

    if np.all(state.games) != None :
        st.subheader("Total of played games : "+str(state.games.shape[0]))
        if not state.games.empty :
            st.plotly_chart(state.games.groupby('date').size().to_frame(name='Number of games').plot.bar(title='Number of games per day').update_layout(xaxis_title='Number of games'))

    if np.all(state.games) != None :
        with st.beta_expander("See .csv file"):
            num_display = st.number_input('Display:',1,state.games.shape[0],5)
            st.dataframe(state.games.tail(num_display).assign(hack='').set_index('hack'))

    with st.beta_expander("Upload your own .csv file"):
        st.warning("WARNING : \nThe .csv file must have the following columns :\n[num_players,names,scores,date,longest_road,largest_army,to_win,extension,group]")
        csv = st.file_uploader('Upload your .csv file', type = ['csv'])
        # if file is uploaded
        if csv is not None:
            file_details = {'file_name ': csv.name,
                            'file_size ': csv.size,
                            'file_type ': csv.type}

            games = get_data(csv)
            games, players = reform_arrays(games)

            players = update_players_from_db(players, games)

            state.games = games
            state.players = players
            state.players_df = get_players_dataframe(state.players)
    st.markdown("#")
    st.info("This is an ongoing project, if you have any idea on how to improve it, feel free to contact us at streamlitmailsender@gmail.com")


def main():
    state = _get_state()
    for path in home_path:
        if os.path.exists(path):
            state.db_path = path
            games = get_data(path = state.db_path)
            games, players = reform_arrays(games)
            players = update_players_from_db(players, games)
            state.games = games
            state.players = players
    for path in player_path:
        if os.path.exists(path):
            state.player_path = path
            state.players_info = pd.read_csv(path)

    st.title("Catan winners : let's see who is the best settler")
    possibilities = ["Home", "Leaderboard", "Players", "Games"]
    choice = st.sidebar.selectbox("Menu",possibilities)

    t = datetime.datetime.fromtimestamp(time.time())


    if choice == 'Home':
        menu_home(state)
    elif choice == 'Leaderboard':
        menu_leaderboard(state)
    elif choice == 'Players':
        menu_players(state)
    elif choice == 'Games':
        menu_games(state)

    # Mandatory to avoid rollbacks with widgets, must be called at the end of your app
    state.sync()


if __name__ == "__main__":
    main()
