"""
BlackJack Game
A python implementation of BlackJack.
:Project URL: https://github.com/nknantha/BlackJack
:Author: nknantha<nknanthakumar13@gmail.com>
:Date: 28-05-2021
"""

import colorama
import signal as _sig
import sys as _sys
import time as _tm
from random import shuffle as random_shuffle

colorama.init()


class Card:
    def __init__(self, rank, suit, value):
        self.rank = rank
        self.suit = suit
        self.value = value

    def __str__(self):
        return f'{self.rank} of {self.suit}'


class Deck:
    # Private for inside only use
    __SUITS = ('Spade', 'Clover', 'Diamond', 'Heart')
    __RANKS = ('A', '2', '3', '4', '5', '6',
               '7', '8', '9', '10', 'J', 'Q', 'K')

    def __init__(self, count=1):
        if count < 1:  # Handling Negetives and Zero
            raise ValueError('Atleast 1 deck needed to play')

        self.__deck = []
        self.__rdeck = []
        self.count = count

        for suit in self.__SUITS:
            for rank in self.__RANKS:
                if rank.isdecimal():
                    value = int(rank)
                elif rank == 'A':
                    value = 11
                else:
                    value = 10
                self.__deck.append(Card(rank, suit, value))

        self.__deck *= self.count
        random_shuffle(self.__deck)  # Shuffling at creation

    def get_card(self):
        try:
            card = self.__deck.pop()
        except IndexError:
            self.__deck = self.__rdeck
            self.__rdeck = []
            random_shuffle(self.__deck)
            card = self.__deck.pop()
        return card

    def return_cards(self, *cards):
        for card in cards:
            if isinstance(card, Card):
                self.__rdeck.append(card)
            else:  # For debug purpose
                raise Exception('Invalid card object')


class Hand:
    def __init__(self, bet, count=0):
        self.count = count
        self.bet = bet
        self.cards = []
        self.value = 0
        self.__aces = 0
        self.status = 'Live'  # Live, BlackJack, Bust, Stand, Double, Surrender, Win, Lost, -, Push

    def __calibrate(self):
        value = 0
        aces = 0
        for card in self.cards:
            aces += 1 if card.rank == 'A' else 0
            value += card.value
        self.__aces = aces
        self.value = value

        while self.__aces and self.value > 21:
            self.value -= 10
            self.__aces -= 1

    def __update_sts(self):
        if len(self.cards) == 2 and self.value == 21:
            self.status = 'BlackJack'
        elif self.value > 21:
            self.status = 'Bust'
            self.bet = 0

    def add_card(self, card):
        self.cards.append(card)
        self.__calibrate()
        self.__update_sts()

    def approx_val(self):
        if self.value < 22 and self.__aces:
            return f'{self.value - 10}/{self.value}'
        else:
            return str(self.value)

    def pop_card(self):
        card = self.cards.pop()
        self.__calibrate()
        return card


class Player:
    def __init__(self, name, balance=1000):
        if balance < 0:
            raise ValueError('Balance should not be negetive.')

        self.name = name
        self.balance = balance
        self.hands = []  # Upto 4 Hands

    def add_hand(self, bet):
        if self.have_bal(bet):
            self.balance -= bet
            hand_count = len(self.hands) + 1
            self.hands.append(Hand(bet, hand_count))
        else:  # For debug purpose
            raise ValueError('Bet not enough.')

    def have_bal(self, amount):
        return True if (0 < amount <= self.balance) else False


class Dealer:
    def __init__(self):
        self.name = 'Dealer'
        self.hand = None

    def add_hand(self):
        self.hand = Hand(0)


class UserInterface:
    # ASCII Escape Sequences
    ERASE_LINE = '\x1b[2K'
    CURSOR_UP = '\x1b[1A'
    CARRIAGE_RETURN = '\x0D'

    F_RESET = colorama.Fore.RESET
    # Color Configuration for entire game
    VB = f'{colorama.Fore.BLUE}|{colorama.Fore.RESET}'
    COLOR = {
        'Live': colorama.Fore.CYAN,
        'BlackJack': colorama.Fore.GREEN,
        'Bust': colorama.Fore.RED,
        'Stand': colorama.Fore.YELLOW,
        'Double': colorama.Fore.MAGENTA,
        'Surrender': colorama.Fore.RED,
        'Win': colorama.Fore.GREEN,
        'Lost': colorama.Fore.RED,
        '-': colorama.Fore.CYAN,
        'Push': colorama.Fore.BLUE,
        'H': colorama.Fore.GREEN,
        'S': colorama.Fore.YELLOW,
        'D': colorama.Fore.MAGENTA,
        'L': colorama.Fore.BLUE,
        'R': colorama.Fore.RED,
    }

    def __init__(self, title=''):
        self.title = title
        self.__lines = 0
        self.round_count = 0
        self.deck_count = 0
        self.print(colorama.Style.BRIGHT)
        self.clear()

    def __dealer_stats(self, dealer, hide=True):
        string = "\n Dealer's Hand:"

        if hide:
            val_str = '1/11' if dealer.hand.cards[0].rank == 'A' else str(dealer.hand.cards[0].value)
            sts_str = 'Stand'
        else:
            val_str = dealer.hand.approx_val()
            sts_str = dealer.hand.status

        # Getting maximum width
        max_width = 7  # "Value: "

        # For value string
        value = len(val_str) + 7  # "Value: "
        if value > max_width:
            max_width = value

        # For status string
        value = len(sts_str) + 8  # "Status: "
        if value > max_width:
            max_width = value

        # For Card string length
        if hide:
            value = len(str(dealer.hand.cards[0]))
            if value > max_width:
                max_width = value

            value = len('<-Hidden Card->')  # For hiding card
            if value > max_width:
                max_width = value
        else:
            for card in dealer.hand.cards:
                value = len(str(card))
                if max_width < value:
                    max_width = value

        # Horizontal Bar
        h_bar = self.__wrap_hb(f" +-{'-' * max_width}-+")
        string += f"\n{h_bar}"

        # Value Line
        val_line = f" {self.VB} {('Value: ' + val_str).center(max_width)} {self.VB}"
        string += f"\n{val_line}"

        # Status Line
        sts_line = f" {self.VB} {('Status: ' + sts_str).center(max_width)} {self.VB}"
        string += f"\n{self.__wrap_word(sts_line, sts_str)}"

        # Seperator Line
        string += f"\n{h_bar}"

        # Cards Lines
        if hide:
            card1 = f"\n {self.VB} {str(dealer.hand.cards[0]).center(max_width)} {self.VB}"
            card2 = f"\n {self.VB} {'<-Hidden Card->'.center(max_width)} {self.VB}"
            string += card1 + card2
        else:
            for card in dealer.hand.cards:
                string += f"\n {self.VB} {str(card).center(max_width)} {self.VB}"

        # End Line
        string += f"\n{h_bar}"

        return string

    def __line_counter(self, string):
        length = len(string.splitlines())
        self.__lines += length if length else 1  # Handling empty string being printed
        if string.endswith('\n'):  # Handling stripped trail \n on splitlines
            self.__lines += 1

    def __player_stats(self, player):
        string = f'\n {player.name}: [ Balance: {player.balance} ]'

        # Getting max height, width for align
        max_width = []
        max_cards = 0
        for hand in player.hands:
            width = 7  # "Hand n:"

            # For Bet string length
            value = len(str(hand.bet)) + 5  # "Bet: "
            if width < value:
                width = value

            # For Value string length
            value = len(hand.approx_val()) + 7  # "Value: "
            if width < value:
                width = value

            # For Status string length
            value = len(hand.status) + 8  # "Status: "
            if width < value:
                width = value

            # For Card string length
            for card in hand.cards:
                value = len(str(card))
                if width < value:
                    width = value

            # For no of cards (height)
            value = len(hand.cards)
            if max_cards < value:
                max_cards = value

            max_width.append(width)

        # Horizontal Bar
        h_bar = ' +'
        for w in max_width:
            h_bar += f"-{'-' * w}-+"
        h_bar = self.__wrap_hb(h_bar)

        # First Line
        string += f"\n{h_bar}"

        # Hand Line
        hand_line = f' {self.VB}'
        for i in range(len(player.hands)):
            hand_str = f"Hand {player.hands[i].count}:".center(max_width[i])
            hand_line += f" {hand_str} {self.VB}"
        string += f"\n{hand_line}"

        # Bet Line
        bet_line = f' {self.VB}'
        for i in range(len(player.hands)):
            bet_str = f"Bet: {player.hands[i].bet}".center(max_width[i])
            bet_line += f" {bet_str} {self.VB}"
        string += f"\n{bet_line}"

        # Value Line
        val_line = f' {self.VB}'
        for i in range(len(player.hands)):
            val_str = f"Value: {player.hands[i].approx_val()}".center(max_width[i])
            val_line += f" {val_str} {self.VB}"
        string += f"\n{val_line}"

        # Status Line
        sts_line = f' {self.VB}'
        for i in range(len(player.hands)):
            sts_str = f"Status: {player.hands[i].status}".center(max_width[i])
            sts_line += f" {self.__wrap_word(sts_str, player.hands[i].status)} {self.VB}"
        string += f"\n{sts_line}"

        # Seperator Line
        string += f"\n{h_bar}"

        # Cards List
        for i in range(max_cards):
            cards_line = f' {self.VB}'
            for j in range(len(player.hands)):
                if i < len(player.hands[j].cards):
                    card_str = f"{player.hands[j].cards[i]}".center(max_width[j])
                else:
                    card_str = "".center(max_width[j])
                cards_line += f" {card_str} {self.VB}"
            string += f"\n{cards_line}"

        # End Line
        string += f"\n{h_bar}"

        return string

    def __print_error(self, msg):
        self.input(f'{colorama.Fore.RED}{msg}'
                   f', press [Enter] to try again... {colorama.Fore.RESET}')
        self.clear(2)

    def __wrap_handop(self, op_lst):
        string = f"[ {self.COLOR['H']}[H]{self.F_RESET}it," \
                 f" {self.COLOR['S']}[S]{self.F_RESET}tand"

        if 'D' in op_lst:
            string += f", {self.COLOR['D']}[D]{self.F_RESET}ouble-Down"

        if 'L' in op_lst:
            string += f", Sp{self.COLOR['L']}[L]{self.F_RESET}it"

        if 'R' in op_lst:
            string += f", Su{self.COLOR['R']}[R]{self.F_RESET}render"

        return string + ' ]'

    def __wrap_hb(self, hb):
        color = colorama.Fore.BLUE
        return color + hb + self.F_RESET

    def __wrap_word(self, string, word):
        color = self.COLOR.get(word)
        post = self.F_RESET if color else ''
        w_word = f'{color}{word}{post}'
        return string.replace(word, w_word)

    def clear(self, lines=None):
        if lines is not None and not (-1 < lines < (self.__lines + 1)):
            raise ValueError('Invalid Lines ' + lines)

        if lines is None:
            length = self.__lines
        else:
            length = lines

        string = (self.CURSOR_UP + self.ERASE_LINE) * length
        print(string + self.CARRIAGE_RETURN, end='')
        self.__lines -= length

    def get_bet(self, player):
        maximum = 1000
        if maximum > player.balance:
            maximum = player.balance
        minimum, multiples = 10, 2

        self.print(f' {player.name} -> [Balance: {player.balance}]')
        prompt_label = f' {player.name} -> Enter bet [Min: {minimum}, Max: {maximum}, x{multiples}]: '
        while True:
            amount = self.get_int(prompt_label, minimum, maximum, multiples)
            if player.have_bal(amount):
                self.clear(1)
                return amount
            else:
                self.__print_error(' Balance not enough')

    def get_decision(self, player, hand, op_lst):
        self.print(f'\n {player.name}\'s Hand {hand.count} ->')
        label = f'  Choose a Option {self.__wrap_handop(op_lst)}: '
        while True:
            selection = self.input(label).upper()
            if len(selection) and selection[0] in op_lst:
                self.clear(2)
                return selection[0]
            else:
                self.__print_error(' Invalid input')

    def get_int(self, label, low, high, multiples=0):
        if multiples:
            label_str = label
        else:
            label_str = f' Enter {label} [{low} - {high}]: '
            multiples = 1

        while True:
            num = self.input(label_str)
            if num.isdecimal() and (low <= int(num) <= high) and (int(num) % multiples) == 0:
                self.clear(1)
                return int(num)
            else:
                self.__print_error(' Invalid input')

    def get_name(self, count):
        label = f' Enter Player {count} Name: '
        while True:
            name = self.input(label)
            if 0 < len(name) < 9:
                return name
            else:
                self.__print_error(' Invalid name')

    def input(self, label=''):
        self.__line_counter(label)
        print(label, end='', flush=True)
        try:
            data = input().strip()
        except Exception:  # Handling EOF and other Errors
            data = ''
        return data

    def print(self, string=''):
        self.__line_counter(string)
        print(string, flush=True)

    def print_round(self, pcount):
        self.print(f"\n {colorama.Fore.CYAN}Round {self.round_count}: "
                   f"[ Decks: {self.deck_count} | Players: {pcount} ]{self.F_RESET}\n")

    def print_stats(self, dealer, players, hide=True):
        self.clear()
        self.print_title()
        self.print_round(len(players))
        self.print(f' GAME TABLE: ')
        string = self.__dealer_stats(dealer, hide)
        for player in players:
            string += '\n' + self.__player_stats(player)
        self.print(string)

    def print_title(self):
        self.print(self.title)

    def set_con_title(self, string):
        self.print(f'\x1b]2;{string}\x07')
        self.clear(1)

    def tell_info(self, label, time=5):
        if not isinstance(time, int) or time <= 0:
            raise ValueError('Invalid time argument ' + time)

        if label.startswith('\n'):
            self.print()
            label = label[1:]

        while time:
            print(f'{self.ERASE_LINE}{self.CARRIAGE_RETURN}{label}({time})', end='', flush=True)
            time -= 1
            _tm.sleep(1)

        # Manual handling because of __line_counter stripping the carriage return
        print(self.ERASE_LINE + self.CARRIAGE_RETURN + label)
        self.__lines += 1


def double_down(player, hand, card):
    if hand in player.hands and len(player.hands) == 1 and len(hand.cards) == 2 \
            and player.have_bal(hand.bet):
        player.balance -= hand.bet
        hand.bet += hand.bet
        hand.status = 'Double'
        hand.add_card(card)
    else:  # Debug purpose
        raise Exception("Double can't be performed.")


def hand_options(player, hand):
    if hand not in player.hands:
        raise Exception('Hand not in player object.')

    def_options = ['H', 'S']
    initial = len(hand.cards) == 2

    if initial and len(player.hands) == 1 and player.have_bal(hand.bet):
        def_options.append('D')

    if initial and hand.cards[0].value == hand.cards[1].value \
            and len(player.hands) < 4 and player.have_bal(hand.bet):
        def_options.append('L')

    if initial and len(player.hands) == 1:
        def_options.append('R')

    return def_options


def rules_display(ui, rules):
    rules_split = rules.splitlines()
    title_max = max(map(len, ui.title.splitlines()))
    rules_max = max(map(len, rules_split))

    filler = '\n' + ' ' * (abs(title_max - rules_max) // 2)
    rules = filler.join(rules_split)

    ui.print_title()
    ui.print(rules)

    label = 'Press [Enter] to Start Game... '
    filler = '\n' + ' ' * (abs(title_max - len(label) - 1) // 2)
    label = filler + label
    ui.input(label)
    ui.clear()


def split(player, hand, h_card1, h_card2):
    if hand in player.hands and len(hand.cards) == 2 and len(player.hands) < 4:
        card = hand.pop_card()

        player.add_hand(hand.bet)
        player.hands[-1].add_card(card)

        hand.add_card(h_card1)
        player.hands[-1].add_card(h_card2)
    else:  # For debug purpose
        raise Exception("Split can't be performed.")


def surrender(player, hand):
    if hand in player.hands and len(player.hands) == 1:
        hand.bet //= 2
        hand.status = 'Surrender'
    else:  # Debug purpose
        raise Exception("Surrender can't be performed.")


def exit_handl(signal, frame):
    print(f'\n\n{colorama.Fore.RED} Ctrl + C triggered, Exitting Game...')
    _sys.exit()


def game():

    ui = UserInterface()

    ui.set_con_title('BlackJack Game')

    ui.title = f'''{colorama.Fore.GREEN}
 888888b.   888                   888   888888                   888
 888  "88b  888                   888     "88b                   888
 888  .88P  888                   888      888                   888
 8888888K.  888  8888b.   .d8888b 888  888 888  8888b.   .d8888b 888  888
 888  "Y88b 888     "88b d88P"    888 .88P 888     "88b d88P"    888 .88P
 888    888 888 .d888888 888      888888K  888 .d888888 888      888888K
 888   d88P 888 888  888 Y88b.    888 "88b 88P 888  888 Y88b.    888 "88b
 8888888P"  888 "Y888888  "Y8888P 888  888 888 "Y888888  "Y8888P 888  888
                                         .d88P
 .d8888    .d8b.  .d8   8b. .d888.    .d88P"
 88   db. 8b._.d8 88 "8" 88 888      888P"
 "Y888P"  88   88 88     88 "Y888"  {colorama.Fore.BLUE}https://github.com/nknantha/BlackJack
{colorama.Fore.RESET}'''
    game_rules = f'''{colorama.Fore.CYAN}
Rules:
 - BlackJack pays 3:2
 - Split allowed, Re-split upto 3 hands
 - Splitted hands only allowed hit or stand
 - Dealer must stand on all 17\'s
 - Players name limit 8 characters
 - Bet minimum=10, maximum=1000 and multiples of 2
{colorama.Fore.YELLOW} 
Tips:
 - Maximize console for better experience
 - Use CTRL + C to exit game during gameplay
{colorama.Fore.WHITE}'''

    # Rules Display & Confirmation
    rules_display(ui, game_rules)

    ui.print_title()

    ui.deck_count = ui.get_int('Deck Count', 1, 8)
    deck = Deck(ui.deck_count)

    players = [Player(ui.get_name(i+1)) for i in range(ui.get_int('Player Count', 1, 7))]

    dealer = Dealer()

    while True:  # Gameplay Loop

        ui.round_count += 1
        ui.clear()
        ui.print_title()
        ui.print_round(len(players))

        # Getting Bets and Creating Hands
        dealer.add_hand()
        for player in players:
            player.add_hand(ui.get_bet(player))

        # Initial Gameplay
        for _ in range(2):
            dealer.hand.add_card(deck.get_card())
            for person in players:
                person.hands[0].add_card(deck.get_card())

        # Player decision & gameplay
        for player in players:
            for hand in player.hands:

                while hand.status[:2] == 'Li':  # For multiple hits
                    ui.print_stats(dealer, players)
                    op_lst = hand_options(player, hand)
                    selection = ui.get_decision(player, hand, op_lst)

                    if selection == 'H':
                        hand.add_card(deck.get_card())
                    elif selection == 'S':
                        hand.status = 'Stand'
                    elif selection == 'D':
                        double_down(player, hand, deck.get_card())
                    elif selection == 'L':
                        split(player, hand, deck.get_card(), deck.get_card())
                    elif selection == 'R':
                        surrender(player, hand)
                    else:  # For debug purpose
                        raise Exception(f'Problem on Looping Gameplay\nPlayer={player.name} '
                                        f'Hand={hand.name} Selection={selection}')

        # Before Dealers Gameplay
        ui.print_stats(dealer, players)
        ui.tell_info(f"\n {colorama.Fore.GREEN}Dealer's Gameplay...{ui.F_RESET}")

        # Dealer Gameplay
        hand_values = [hand.value for player in players for hand in player.hands if hand.value < 22]
        if hand_values:  # Checking if dealer needs to play
            player_max = max(hand_values)
            while dealer.hand.value < 18 and dealer.hand.value < player_max:
                dealer.hand.add_card(deck.get_card())
            if dealer.hand.status[:2] == 'Li':
                dealer.hand.status = 'Stand'
        else:
            dealer.hand.status = 'Win'

        # Winning & Bonus Distribution
        if dealer.hand.value > 21:  # Dealer Busts
            for player in players:
                for hand in player.hands:
                    if hand.value < 22:  # Filtering Non-Bust
                        if hand.status[:2] == 'Bl':
                            hand.bet = round(hand.bet * 2.5)
                        elif hand.status[:2] != 'Su':
                            hand.status = 'Win'
                            hand.bet *= 2
        else:  # Dealer not Busts
            for player in players:
                for hand in player.hands:
                    if hand.value < 22 and hand.status[:2] != 'Su':  # Filtering Non-Bust and Non-Surrender
                        if hand.value > dealer.hand.value:
                            if hand.status[:2] == 'Bl':
                                hand.bet = round(hand.bet * 2.5)
                            else:
                                hand.status = 'Win'
                                hand.bet *= 2
                            dealer.hand.status = '-'
                        elif hand.value == dealer.hand.value:
                            if hand.status[:2] == 'Bl' and dealer.hand.status[:2] != 'Bl':
                                hand.bet = round(hand.bet * 2.5)
                                dealer.hand.status = '-'
                            elif hand.status[:2] != 'Bl' and dealer.hand.status[:2] == 'Bl':
                                hand.status = 'Lost'
                                hand.bet = 0
                            else:
                                hand.status = 'Push'
                                dealer.hand.status = '-'
                        else:
                            hand.status = 'Lost'
                            hand.bet = 0

            if dealer.hand.status != '-':
                dealer.hand.status = 'Win'

        # Final Stats
        ui.print_stats(dealer, players, False)
        ui.input('\n Press [Enter] to next round... ')

        # Clearing Hands and Pushing Bets to Player
        deck.return_cards(*dealer.hand.cards)
        for player in players:
            for hand in player.hands[:]:
                player.balance += hand.bet
                deck.return_cards(*hand.cards)
                player.hands.remove(hand)

        # Checking for betting capacity
        ui.print()
        is_removed = False
        for player in players[:]:
            if not player.have_bal(10):  # Checking minimum balance
                ui.print(f' {colorama.Fore.RED}Player {player.name} '
                         f'kicked, having below minimum balance.{ui.F_RESET}')
                players.remove(player)
                is_removed = True

        if is_removed:
            ui.tell_info('\n Going to next round...')

        # Changing players order and Gameplay exit
        if players:
            if len(players) > 1:
                players = players[1:] + players[:1]
        else:
            ui.tell_info(f'\n {colorama.Fore.RED}All players left, exitting game...')
            break


if __name__ == '__main__':
    _sig.signal(_sig.SIGINT, exit_handl)
    __title__ = 'BlackJack'
    __version__ = '1.0'
    __author__ = 'nknantha'

    game()
