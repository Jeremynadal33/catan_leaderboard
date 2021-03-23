import pandas as pd
import streamlit as st
import numpy as np
import time
from datetime import date
import os

from streamlit.hashing import _CodeHasher
from utils import *

try:
    # Before Streamlit 0.65
    from streamlit.ReportThread import get_report_ctx
    from streamlit.server.Server import Server
except ModuleNotFoundError:
    # After Streamlit 0.65
    from streamlit.report_thread import get_report_ctx
    from streamlit.server.server import Server

home_path = "/Users/jeremynadal/Documents/catan_winners/database.csv"
pd.options.plotting.backend = "plotly"
###################### FUNCTIONS #################
#@st.cache
def get_data(path = 'home'):
    try:
        if path == 'home':
            data = pd.read_csv(home_path)
            assert np.all(data.columns == ['num_player', 'names', 'scores', 'date', 'longest_road', 'largest_army', 'to_win', 'extension']), "Columns of the .csv file must be : ['num_player', 'names', 'scores', 'date', 'longest_road', 'largest_army', 'to_win', 'extension']"
            data['extension'] = data['extension'].fillna('Base game')
            return data
        else :
            data = pd.read_csv(path)
            assert np.all(data.columns == ['num_player', 'names', 'scores', 'date', 'longest_road', 'largest_army', 'to_win', 'extension']), "Columns of the .csv file must be : ['num_player', 'names', 'scores', 'date', 'longest_road', 'largest_army', 'to_win', 'extension']"
            data['extension'] = data['extension'].fillna('Base game')
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

def jump():
    return st.write('\n')
################### Rest is for the application itself #################
def display_leaderboard(state):
    cols = st.beta_columns([1,1,1])
    with cols[0]:
        choice = st.selectbox('Sort by:',['Number of wins', 'Winning rate' ,'Average number of points', 'Number of largest army', 'Number of longest road'])
    with cols[1]:
        num_display = st.number_input('Display:',1,state.players_df.shape[0],3)
# 'Total games', 'Total of points', 'Num. longest road', 'Num. largest army'
    if choice == 'Number of wins':
        to_display = state.players_df.sort_values('Number of wins', ascending=False)
        to_display = to_display[['Surname', 'Number of wins', 'Total games', 'Total of points', 'Num. longest road', 'Num. largest army', 'Avg number of points', 'Winning rate']][:num_display]
        st.dataframe(to_display.assign(hack='').set_index('hack'))
    elif choice == 'Winning rate':
        st.dataframe(state.players_df.sort_values('Winning rate', ascending=False)[['Surname',  'Winning rate', 'Number of wins', 'Total games', 'Total of points', 'Num. longest road', 'Num. largest army', 'Avg number of points']][:num_display].assign(hack='').set_index('hack'))
    elif choice == 'Average number of points':
        st.dataframe(state.players_df.sort_values('Avg number of points', ascending=False)[['Surname', 'Avg number of points', 'Number of wins', 'Total games', 'Total of points', 'Num. longest road', 'Num. largest army', 'Winning rate']][:num_display].assign(hack='').set_index('hack'))
    elif choice == 'Number of largest army':
        st.dataframe(state.players_df.sort_values('Num. largest army', ascending=False)[['Surname', 'Num. largest army','Number of wins', 'Total games', 'Total of points', 'Num. longest road', 'Avg number of points', 'Winning rate']][:num_display].assign(hack='').set_index('hack'))
    elif choice == 'Number of longest road':
        st.dataframe(state.players_df.sort_values('Num. longest road', ascending=False)[['Surname',  'Num. longest road', 'Number of wins', 'Total games', 'Total of points', 'Num. largest army', 'Avg number of points', 'Winning rate']][:num_display].assign(hack='').set_index('hack'))

def menu_leaderboard(state):
    st.header("This is the leaderboard page")
    st.subheader("Here you can view in depth statistics on the loaded games")
    try:
        if state.players_df != None:
            display_leaderboard(state)
        else :
            st.write('Please, load a csv file on the _Home_ page first')
    except Exception as e:
        if not state.players_df.empty :
            display_leaderboard(state)
        else:
            st.write('Please, load a csv file first.')

def menu_players(state):
    st.header("This is the players' page")
    st.subheader("Here you can view statistics on a selected player or add a new player")

    cols = st.beta_columns([1,1,1])

    if state.players != None:
        with cols[0]:
            player = st.selectbox( "Select a player", ['']+list(state.players.keys()) )
        if player != '' : st.write( state.players[player].display() )
    else :
        st.write('Please, load a csv file on the _Home_ page first')

    st.write("#")
    st.write("#")
    with st.beta_expander("Add new player"):
        st.write("Not available for the moment")
    with st.beta_expander("Warning"):
        st.warning("Each player must have its own surname and mail adress")

def add_game(state):
    st.header("This is the add game page")
    st.subheader("Here you can add games")
    with st.beta_expander("Warning"):
        st.warning("You cannot enter a game with unregistered players")
    cols = st.beta_columns([1,1,1])
    with cols[0]:
        num_persons = st.slider("Number of players", 3, 6, 3, 1)
        extension = st.selectbox('Extension:',('Base game', 'Villes et chevaliers','Marins'))
    with cols[1]:
        game_date = st.date_input('Date', date.today() )
        to_win = st.number_input('Number of points to win',7,20,10)

    cols = st.beta_columns([1,1,1])
    names = []
    scores = []
    with cols[0]:
        for player in range(num_persons):
            if state.players != None:
                names.append(st.selectbox(f"Player {player+1}:",['']+list(state.players.keys())))
            else:
                names.append(st.text_input(f"Player {player+1}:"))
    with cols[1] :
        for player in range(num_persons):
            scores.append(st.number_input(f"Score {player+1}:",0,to_win,0 ))

    if names[0] != "":
        longest = st.selectbox("Longest road", names+[''])
        largest = st.selectbox("Largest army", names+[''])

    #cols = st.beta_columns([1,1,1])
    #with cols[1]:
    if st.button("Save"):
        st.write('Unavailable for the moment')
        save_game()

def save_game():
    pass

def menu_home(state):
    games = pd.DataFrame()
    home = False
    # Home page : presentation, loading available, display of the loaded .csv and quick display of the leaderboard
    st.markdown("Welcome to this _easy to use_ Catan leaderboard. ")
    st.markdown("Here you can load your own Catan games and see, amongst your friends who is the best settler.")

    with st.beta_expander("Warning: constraints on the .csv file"):
        st.warning("The .csv file must have the following columns :\n[num_player,names,scores,date,longest_road,largest_army,to_win,extension]")
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

    # If one wants to use the existing .csv
    if os.path.exists(home_path):
        col1, col2, col3  = st.beta_columns(3)
        with col1:
            pass
        with col3:
            pass
        with col2 :
            if st.button("Use database's .csv"):
                home = True

    if home :
        games = get_data()
        games, players = reform_arrays(games)
        players = update_players_from_db(players, games)

        state.games = games
        state.players = players

    if np.all(state.games) != None :
        with st.beta_expander("See .csv file"):
            st.dataframe(state.games.head().assign(hack='').set_index('hack'))
    #players = create_players()
    if state.players != None:
        state.players_df = get_players_dataframe(state.players)

    if np.all(state.games) != None :
        st.plotly_chart(state.games.groupby('date').size().to_frame(name='Number of games').plot(title='Number of games per day').update_layout(xaxis_title='Number of games'))


def main():
    state = _get_state()
    st.title("Catan winners : let's see who is the best settler")
    possibilities = ["Home", "Leaderboard", "Players", "Add game"]
    choice = st.sidebar.selectbox("Menu",possibilities)

    if choice == 'Home':
        menu_home(state)
    elif choice == 'Leaderboard':
        menu_leaderboard(state)
    elif choice == 'Players':
        menu_players(state)
    elif choice == 'Add game':
        add_game(state)

    # Mandatory to avoid rollbacks with widgets, must be called at the end of your app
    state.sync()


if __name__ == "__main__":
    main()
