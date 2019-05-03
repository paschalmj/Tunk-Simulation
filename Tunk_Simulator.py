'''
Michael Paschal

This file runs a simulation of the game of Tunk
Tunk is a card game in which players try to minimize the total value of their hand each round.
Gameplay is as follows:
  - Players discard 1 or more cards each turn
  - Players draw one card from the top of the deck or from the top of the discard pile
  - Before discarding, players can call Tunk if they think they have the lowest hand
    - If they have the lowest hand, they get 0 points and everyone else adds the total value of their hand to their score
    - If they did not have the lowest hand, they alone get 30 points added to their score and all other players add 0
  - The game is over when someone's total score is over a threshold of points (standard threshold is 150 points)
'''

import random
import math
from collections import Counter
import numpy


DISCARD_PILE = []
PLAYER_1 = None
PLAYER_2 = None
PLAYER_3 = None
PLAYER_4 = None
THRESHHOLD = 150
TURN_ORDER = []
GAME_OVER = False
ROUND_OVER = False
BETA = 6
PLAYER_1_BETA = 9
LOSSES = [0,0,0,0]
WINS = [0,0,0,0]
CALLING_ARRAY = numpy.zeros((1000, 500))

class Card:
  '''
  s = card suit
  n = card name
  v = card value in tunk
  '''
  def __init__(self, s, n, v):
    self.suit = s
    self.name = n
    self.value = v

  def __str__(self):
    return '(' + self.name + ' of ' + self.suit + ')'

  def __repr__(self):
    return '(' + self.name + ' of ' + self.suit + ')'

  def __eq__(self, other):
    if self.name == other.name and self.value == other.value:
      return True
    return False

  def __hash__(self):
    return self.name.__hash__() + self.value.__hash__()


class Deck:
  '''
  Deck contains 52 standard cards + 2 jokers
  '''
  def __init__(self):
    self.suits = self.suits = ['Spades','Hearts','Diamonds','Clubs']
    self.names = ['Ace','2','3','4','5','6','7','8','9','10','Jack','Queen','King']
    self.cards = []
    for suit in self.suits:
      for name in self.names:
        if name == 'Ace':
          value = 1
        elif name in ['Jack', 'Queen','King']:
          value = 10
        else:
          value = int(name)
        card = Card(suit, name, value)
        self.cards.append(card)
    self.cards.append(Card('Red', 'Joker', 0))
    self.cards.append(Card('Black', 'Joker', 0))
    random.shuffle(self.cards)

  def draw(self):
    return self.cards.pop()

class Player:
  def __init__(self, game_strategy, player_name, player_num):
    self.name = player_name
    self.hand = []
    self.score = 0
    self.turn = False
    self.strategy = game_strategy
    self.number = player_num

  def get_hand_value(self):
    '''
    Get the total point value of the players hand
    '''
    hand_value = 0
    for card in self.hand:
      hand_value += card.value
    return hand_value

  def get_highest_card(self):
    '''
    Get highest value card in the players hand
    '''
    highest_card = self.hand[0]
    for card in self.hand:
      if card.value > highest_card.value:
        highest_card = card
    return highest_card

  def __eq__(self, other):
    if self.name != other.name:
      return False

  def __str__(self):
    return self.name

  def __hash__(self):
    return self.name.__hash__()


class Game:

  def __init__(self, strategies):
    '''Initializes the game by:
      - Creating the deck
      - Creating discard pile
      - Dealing players hands
      - Setting scores
      - Deciding who goes first
    '''
    global PLAYER_1, PLAYER_2, PLAYER_3, PLAYER_4, DISCARD_PILE, TURN_ORDER, LOSSES, WINS
    # fh.write('Initializing game.')
    self.deck = Deck()
    PLAYER_1 = Player(strategies[0], 'player_1', 0)
    PLAYER_2 = Player(strategies[1], 'player_2', 1)
    PLAYER_3 = Player(strategies[2], 'player_3', 2)
    PLAYER_4 = Player(strategies[3], 'player_4', 3)
    TURN_ORDER = [PLAYER_1, PLAYER_2, PLAYER_3, PLAYER_4]
    self.whose_turn = PLAYER_1
    DISCARD_PILE = []

  def deal(self):
    '''
    Deals a 5 card hand to each of the 4 players from the deck.
    '''
    global PLAYER_1, PLAYER_2, PLAYER_3, PLAYER_4
    PLAYER_1.hand = []
    PLAYER_2.hand = []
    PLAYER_3.hand = []
    PLAYER_4.hand = []
    for i in range(5):
      PLAYER_1.hand.append(self.deck.draw())
      PLAYER_2.hand.append(self.deck.draw())
      PLAYER_3.hand.append(self.deck.draw())
      PLAYER_4.hand.append(self.deck.draw())

  def discard(player_hand, cards):
    '''
    Discards the passed in cards from the players hand to the discard pile.
    '''
    global DISCARD_PILE
    for card in cards:
      DISCARD_PILE.append(card)
      player_hand.remove(card)
    return player_hand

  def next_player(self, player):
    '''
    Returns the player for the next turn.
    '''
    index = TURN_ORDER.index(player)
    if index == 3:
      return PLAYER_1
    else:
      return TURN_ORDER[index+1]


  def is_game_over(self):
    '''
    Checks whether the current game is over.
    If any of the players scores are over THRESHHOLD returns
      True and the list of losing players
    Else returns false and the game continues.
    '''
    global ROUND_OVER, GAME_OVER
    losing_players = []
    if PLAYER_1.score >= THRESHHOLD:  # Player 1 loses
      losing_players.append(PLAYER_1)
    if PLAYER_2.score >= THRESHHOLD:  # Player 2 loses
      losing_players.append(PLAYER_2)
    if PLAYER_3.score >= THRESHHOLD:  # Player 3 loses
      losing_players.append(PLAYER_3)
    if PLAYER_4.score >= THRESHHOLD:  # Player 4 loses
      losing_players.append(PLAYER_4)
    if losing_players:                # If there are losing players then the game is over
      winning_players = []
      for player in TURN_ORDER:
        if player not in losing_players:
          winning_players.append(player)
      GAME_OVER = True
      return (losing_players, winning_players)
    else:
      ROUND_OVER = False
      return (None, None)

  def call_tunk(self, player):
    '''
    At the beginning of a players turn, they can call tunk.
    - This immediately ends the current round and the current players hand value is
      compared to the other players hand values.
    - If the players hand value is the lowest, each other player adds their current hand value
      to their score
    - If not add 30 points to the current players score.
    '''
    global PLAYER_1, PLAYER_2, PLAYER_3, PLAYER_4, ROUND_OVER

    # fh.write(player.name + ' has called tunk.\n')

    player_lowest = True
    player_hand_value = player.get_hand_value() # Get the current players hand value
    other_min_hand = PLAYER_2
    other_min_hand_value = PLAYER_2.get_hand_value()
    for other in TURN_ORDER: # check all other players hand value against the current players hand value
      if player != other:
        other_hand_value = other.get_hand_value()
        if player_hand_value > other_hand_value:
          player_lowest = False
          if other_hand_value < other_min_hand_value:
            other_min_hand = other
            other_min_hand_value = other_hand_value
    if not player_lowest: # Current player loses the round.
      # fh.write(player.name + ' was not the lowest and adds 30 points to their score.\n')
      player.score += 30 # Add 30 points to their score
      self.whose_turn = other_min_hand
    else: # Current player wins the round. All other players add their hand value to their score
      # fh.write(player.name + ' was the lowest, all other players add their hand value to their score.\n')
      for other in TURN_ORDER:
        if player != other:
          other.score += other.get_hand_value()
      self.whose_turn = player
    ROUND_OVER = True # This ends the round.
    # fh.write('\n')

  def end_round(self):
    '''
    This method is called when a round ends and the deck is empty.
    If the deck runs out before someone calls tunk, each player adds the
      value of their hand to their score.
    The player with the lowest hand value adds and additional 15 points to their score.
    '''
    global ROUND_OVER
    # fh.write('Deck is empty, round ends with no player calling tunk.\n')
    # fh.write('All players add their hand value to their score.\n')
    min_player_hand = PLAYER_1                          # PLAYER_1 is set as the default lowest hand
    min_player_hand_value = PLAYER_1.get_hand_value()   # PLAYER_1 hand value
    for other in [PLAYER_2,PLAYER_3,PLAYER_4]:          # Loop through the other players hands and check the values
      other_hand_value = other.get_hand_value()
      if other_hand_value < min_player_hand_value:      # If a players hand is lower than the current min, set the current players hand as the min
        min_player_hand = other
        min_player_hand_value = other_hand_value
    for player in TURN_ORDER:                           # Add points to players hands
      player_hand_value = player.get_hand_value()
      if player == min_player_hand:
        # fh.write(player.name + ' had the lowest hand and adds 15 extra points to their score.\n')
        player.score += 15                              # Add additional 15 points to player with lowest hand
      player.score += player_hand_value
    # fh.write('\n')
    go_around = 0
    ROUND_OVER = True # End the current round



  def take_turn(self, player):
    '''
    Take a turn for the current player.
    Each turn involves the following:
      - Discard 1 or more cards
      - Draw a card from the top of the deck or the top of the discard pile.
    '''
    global PLAYER_1, PLAYER_2, PLAYER_3, PLAYER_4, DISCARD_PILE, BETA
    if not self.deck.cards:
      self.end_round()
    elif player.get_hand_value() <= 7: # If the players hand is 7 points or below, call tunk and end the round
      self.call_tunk(player)
    else:

# ---------------------------- Begin discarding cards section ----------------------------------------------

      fh.write(player.name + '\'s turn:\n')

      # Discard either any cards that are multiples or highest value card in the current players hand

      discard_cards = [] # Stores the cards to be discarded, needed to keep card ordering in the discard pile correct

      card_counts = Counter(player.hand).most_common(5) # Count the number of occurrences of each card in a players hand
      most_common_card = card_counts[0][0]               # Get the first card
      most_common_card_count = card_counts[0][1]         # Get the number of occurrences of the first card
      for card_occurrences in card_counts:             # Loop through the remaining occurrences, if the # of occurrences of that card >= #
                                                              #   of occurrences of the most common card and the value is greater, set the current card as the most common
        if card_occurrences[0].value > most_common_card.value and card_occurrences[1] >= most_common_card_count:
          most_common_card = card_occurrences[0]
          most_common_card_count = card_occurrences[1]
      if most_common_card_count > 1 and most_common_card.value > 5: # If the hand has multiples, discard all of them
        for i in range(most_common_card_count):
          discard_cards.append(player.hand.pop(player.hand.index(most_common_card)))
      else: # If the hand does not have multiples, discard the highest value card in the hand.
        highest_card = player.get_highest_card() # Get the card to discard from the players hand
        player.hand.remove(highest_card) # Remove the highest card from the players hand
        discard_cards.append(highest_card) # Discard card(s)

# --------------------------- Begin strategies about picking up cards section ------------------------------

      top_card_in_discard_pile = DISCARD_PILE.pop()
      if not player.hand: # Player has 1 card left in their hand
        if top_card_in_discard_pile.value < discard_cards[0].value: # Check the card in their hand against the top card in the discard pile
          draw_card = top_card_in_discard_pile # Take the top card in the discard pile if it is lower than the card in their hand
          drawn_from = 'discard pile'
        else:
          draw_card = self.deck.draw() # If not lower take the top card from the deck
          drawn_from = 'deck'
      elif player.strategy == 'expert': # Consider top discard pile card under beta or draw from deck
        # ADD IF THE CARD JUST DISCARDED IS A MATCH WITH THE HIGHEST CARD IN THE HAND, DRAW THE DISCARD CARD
        # AND DROP THE NEXT HIGHEST CARD IN THE HAND
        if len(discard_cards) == 1 and discard_cards[0].value == top_card_in_discard_pile.value: # Highest card is a match with the card in the discard pile and the player will want to drop two cards
          next_highest_card = player.get_highest_card() # Get the next highest card to discard from the players hand
          player.hand.remove(next_highest_card) # Remove the next highest card from the players hand
          discard_cards.remove(highest_card)
          player.hand.append(highest_card) # The player wants to keep the highest card in their hand
          discard_cards.append(next_highest_card) # Discard the next highest card in the players hand
          draw_card = top_card_in_discard_pile # Take the top card from the discard pile
          drawn_from = 'discard pile'
        else:
          card_matches = False
          for card in player.hand: # Check if the top card in the discard pile matches anything in the current players hand
            if top_card_in_discard_pile == card:
              card_matches = True
          if player.name == 'player_1' and (card_matches or (top_card_in_discard_pile.value < PLAYER_1_BETA and top_card_in_discard_pile.value < player.get_highest_card().value)): # Discard card value must be lower than the
                                                                                                                                                                           # highest card in the players hand and below beta
            draw_card = top_card_in_discard_pile # Take the top card from the discard pile
            drawn_from = 'discard pile'
          elif card_matches or (top_card_in_discard_pile.value < BETA and top_card_in_discard_pile.value < player.get_highest_card().value): # Discard card value must be lower than the
                                                                                                                                             # highest card in the players hand and below beta
            draw_card = top_card_in_discard_pile # Take the top card from the discard pile
            drawn_from = 'discard pile'
          else:
            DISCARD_PILE.append(top_card_in_discard_pile) # Put the top card from the discard pile back
            draw_card = self.deck.draw()        # Draw the next card from the deck
            drawn_from = 'deck'
      elif player.strategy == 'intermediate': # Consider top discard pile if lower than current highest card
        if top_card_in_discard_pile.value < discard_cards[0].value:
          draw_card = top_card_in_discard_pile # Take the top card from the discard pile
          drawn_from = 'discard pile'
        else:
          DISCARD_PILE.append(top_card_in_discard_pile) # Put the top card from the discard pile back
          draw_card = self.deck.draw()        # Draw the next card from the deck
          drawn_from = 'deck'
      else: # strategy is basic strategy
        DISCARD_PILE.append(top_card_in_discard_pile) # Put the top card from the discard pile back
        draw_card = self.deck.draw()        # Draw the next card from the deck
        drawn_from = 'deck'
      for card in discard_cards:
        fh.write(player.name + ' is discarding ' + card.__str__() + '\n')
        DISCARD_PILE.append(card) # Discard the highest card
      fh.write(player.name + ' drew ' + draw_card.__str__() + ' from the ' + drawn_from + '\n')
      player.hand.append(draw_card)  # Put the drawn card in the players hand
      fh.write('\n')

  def play_game(self):
    '''
    Runs the game of tunk.
    Keeps track of the number of rounds and the cards left in the deck.
    '''
    global GAME_OVER, WINS, LOSSES, SCORE_COUNTS, go_around, round_count
    SCORE_COUNTS = numpy.zeros((50, 500)) #track average scores... rows are rounds columns are go arounds
    round_count = 0
    spot_on_table = 1 #keep track of which players turn it is easily
    sum_scores = 0 #store sum of scores after each go around

    while not GAME_OVER:
      round_count += 1
      go_around = 0
      fh.write('Round ' + str(round_count) + '\n')
      # for player in TURN_ORDER:
        # fh.write(player.name + ' score: ' + str(player.score) + '\n') # # # fh.write each players current score
      # fh.write('Dealing players hands.\n')
      # fh.write('\n')
      self.deck = Deck() # Create a new deck each round
      self.deal()        # Redeal players hands
      DISCARD_PILE.append(self.deck.cards.pop()) # Put top card on the deck in the discard pile for first player to consider
      while not ROUND_OVER:
        fh.write('Cards left in the deck: ' + str(len(self.deck.cards)) + '\n')  # # # fh.write the number of cards left in the deck
        fh.write('spot ' + str(spot_on_table) + '\n')
        fh.write(str(self.whose_turn) + '\n')
        self.take_turn(self.whose_turn)
        if spot_on_table < 4:
            spot_on_table += 1
        else:
            sum_scores = PLAYER_1.get_hand_value()+PLAYER_2.get_hand_value()+PLAYER_3.get_hand_value()+PLAYER_4.get_hand_value()
            SCORE_COUNTS[round_count-2,go_around] = sum_scores*1./4 #add score for this go around of the round to the array
            spot_on_table = 1
            go_around += 1
            fh.write('hello, the go around ' + str(go_around) + ' average was: ' + str(sum_scores*1./4) + '\n') #write avg after each go around
        # fh.write('\n')
        self.whose_turn = self.next_player(self.whose_turn) # Set the next players turn
      (losing_players, winning_players) = self.is_game_over() # Check if the game is over
    fh.write('Game is over.\n')
    # fh.write('Players who lost:\n')
    # for player in losing_players:
      # fh.write(player.name + ' lost with a score of ' + str(player.score) + ' points.\n')
    # fh.write('\n')
    # fh.write('Players who won:\n')
    # for player in winning_players:
      # fh.write(player.name + ' won with a score of ' + str(player.score) + ' points.\n')
    for player in TURN_ORDER:
      if player in losing_players:
        LOSSES[player.number] += 1
      else:
        WINS[player.number] += 1


if __name__ == '__main__':
  global fh
  file_1 = "tunk_output_basic.txt"
  file_2 = "tunk_output_intermediate.txt"
  file_3 = "tunk_output_expert.txt"
  file_4 = "tunk_output_basic_vs_intermediate"
  file_5 = "tunk_output_basic_vs_expert"
  file_6 = "tunk_output_intermediate_vs_basic"
  file_7 = "tunk_output_intermediate_vs_expert"
  file_8 = "tunk_output_expert_vs_basic"
  file_9 = "tunk_output_expert_vs_intermediate"
  files = [file_1,file_2,file_3,file_4,file_5,file_6,file_7,file_8,file_9]


  all_basic_strategies = ['basic','basic','basic','basic']
  all_intermediate_strategies = ['intermediate','intermediate','intermediate','intermediate']
  all_expert_strategies = ['expert','expert','expert','expert']
  basic_vs_intermediate = ['basic','intermediate','intermediate','intermediate']
  basic_vs_expert = ['basic','expert','expert','expert']
  intermediate_vs_basic = ['intermediate','basic','basic','basic']
  intermediate_vs_expert = ['intermediate','expert','expert','expert']
  expert_vs_basic = ['expert','basic','basic','basic']
  expert_vs_intermediate = ['expert','intermediate','intermediate','intermediate']
  strategies = [all_basic_strategies, all_intermediate_strategies, all_expert_strategies, basic_vs_intermediate, basic_vs_expert, intermediate_vs_basic, intermediate_vs_expert, expert_vs_basic, expert_vs_intermediate]


  #-------------------------------- Comparing strategies against each other----------------------------------------------------
  for i in range(0,9): #pick the combination of strategies
    fh = open(files[2], "w")
    for j in range(1000): #pick games to play wth each strategy
      game = Game(strategies[2])
      game.play_game()
      # fh.write('\n')
      # fh.write('GAME DATA: \n')
      # fh.write('Rounds: ' + str(round_count) + '\n')
      # fh.write('Score Counts: \n')

      # TAKE THE SCORE COUNTS FROM EACH ROUND OF THIS GAME AND AVERAGE THEM
      # THEN ADD THIS TO CALLING_ARRAY SO WE CAN KEEP TRACK OF TOTALS ACROSS ALL GAMES
      CALLING_ARRAY[j,:] = SCORE_COUNTS.sum(0)*1./round_count
      print(str(i) + ' ' + str(j))
      if go_around > 100:
        print(str(i))


      # fh.write(str(SCORE_COUNTS) + '\n')
      GAME_OVER = False
    # fh.write('\n')
    for player in TURN_ORDER:
      fh.write( player.name + ' wins: ' + str(WINS[player.number]) + '\n')
      fh.write(player.name + ' losses: ' + str(LOSSES[player.number]) + '\n')
      fh.write(player.name + ' win ratio: ' + str(WINS[player.number]*1./10000) + '\n')
      fh.write('\n')
    fh.close()
    LOSSES = [0,0,0,0]
    WINS = [0,0,0,0]
    print('Restarted iteration, LOSSES = ' + str(LOSSES[0]) + ', WINS = ' + str(WINS[0]))

# --------------------- Comparing player_1 with changing beta against 3 other expert players with constant beta values ------------------------------
##  fh = open('Expert_Beta_Value_Test', "w")
##  for i in range(0,11): #pick the combination of strategies
##    PLAYER_1_BETA = i
##    fh.write('Player_1_BETA = ' + str(PLAYER_1_BETA) + '\n')
##    for j in range(10): #pick games to play wth each strategy
##      game = Game(strategies[3])
##      game.play_game()
##      # fh.write('\n')
##      # fh.write('GAME DATA: \n')
##      # fh.write('Rounds: ' + str(round_count) + '\n')
##      # fh.write('Score Counts: \n')
##
##      # TAKE THE SCORE COUNTS FROM EACH ROUND OF THIS GAME AND AVERAGE THEM
##      # THEN ADD THIS TO CALLING_ARRAY SO WE CAN KEEP TRACK OF TOTALS ACROSS ALL GAMES
##      CALLING_ARRAY[j,:] = SCORE_COUNTS.sum(0)*1./round_count
##      # fh.write(str(SCORE_COUNTS) + '\n')
##      GAME_OVER = False
##    fh.write('\n')
##    for player in TURN_ORDER:
##      fh.write( player.name + ' wins: ' + str(WINS[player.number]) + '\n')
##      fh.write(player.name + ' losses: ' + str(LOSSES[player.number]) + '\n')
##      fh.write(player.name + ' win ratio: ' + str(WINS[player.number]*1./11) + '\n')
##      fh.write('\n')
##    CALLING_ARRAY.sum(0)*1./11
##    fh.write('Average hand score per table go around: ' + str(CALLING_ARRAY) + '\n')
##    CALLING_ARRAY = numpy.zeros((11, 25))
##    LOSSES = [0,0,0,0]
##    WINS = [0,0,0,0]
##    print('Restarted iteration, LOSSES = ' + str(LOSSES[0]) + ', WINS = ' + str(WINS[0]))
##
##  fh.close()







