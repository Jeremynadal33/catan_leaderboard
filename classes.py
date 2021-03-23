import numpy as np

class Player:
    def __init__(self, surname, first_name = None, last_name = None, mail = None):
        #mail will be the unique identifier
        self.first_name = first_name
        self.last_name = last_name
        self.surname = surname
        self.mail = mail

        self.num_games = 0
        self.num_win = 0
        self.num_largest = 0
        self.num_longest = 0
        self.total_points = 0

    def add_game(self):
        self.num_games += 1
    def add_win(self):
        self.num_win += 1
    def add_largest(self):
        self.num_largest += 1
    def add_longest(self):
        self.num_longest += 1
    def add_points(self, points):
        self.total_points += points

    def get_num_games(self):
        return self.num_games
    def get_win(self):
        return self.num_win
    def get_largest(self):
        return self.num_largest
    def get_longest(self):
        return self.num_longest
    def get_points(self):
        return self.total_points
    def get_surname(self):
        return self.surname

    def display(self):
        assert self.num_games != 0, 'Update players before display'
        print('Player {} won {} out of {} games with average number of points of {}'.format(self.surname, self.num_win, self.num_games, self.total_points/self.num_games))
        return 'Player {} won {} out of {} games with average number of points of {:.3}'.format(self.surname, self.num_win, self.num_games, self.total_points/self.num_games)

    def to_dict(self):
        return {'Surname': self.surname,
                'Number of wins': self.num_win,
                'Total games': self.num_games,
                'Total of points': self.total_points,
                'Num. longest road': self.num_longest,
                'Num. largest army': self.num_largest}



class Game:
    def __init__(self, num_player, names, scores, date, longest_road, largest_army, to_win = 10, extension = None):
        assert len(names)==num_player, 'Error, number of players doesnot correspond to names'
        self.num_player = num_player
        self.scores = scores
        self.names = names
        self.date = date
        self.longest_road = longest_road
        self.largest_army = largest_army
        self.to_win = to_win
        self.extension = extension

    def display_game(self):
        print('This game was played on the {} and featured {} persons : '.format(self.date,self.num_player), self.names)
        print('{} had longest road and {} had largest army.'.format(self.names[self.longest_road], self.names[self.largest_army]))
        print('{} won with {} points'.format(self.names[np.argmax(self.scores)], np.max(self.scores)))

    def get_game(self):
        return self.num_player, self.names, self.scores, self.date, self.longest_road, self.largest_army, self.to_win, self.extension
