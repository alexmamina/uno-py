from enum import IntEnum

# Go - regular play, regular relay
# Debug - change turn, regular play, print data
# Challenge - only send packet to make player take two cards
# Challenge taken - confirmation of challenge complete
# Zerocards - one player is out of cards, forward to the other who will either take cards or send
# points
# Takecards - send back to player out of cards while waiting for the other to take more
# Calc - other player sends points
# Bye - a player said no new games, or an error occurred at one player
# Init - send initial information to setup a new game
# Seven - the 7 part of 7/0
# Zero - the 0 part of 7/0
# Numupdate - the finale of 7/0 to update all cards left
# Designupd - relay to all just to see cards move on screen
# Showchallenge - if player was honest, tell them someone else checked their cards


class Stage(IntEnum):
    INIT = -1
    GO = 0
    CHALLENGE = 1
    CHALLENGE_TAKEN = 6
    SHOWCHALLENGE = 810
    ZEROCARDS = 2
    DEBUG = 3
    TAKECARDS = 4
    CALC = 5
    SEVEN = 7
    ZERO = 70
    NUMUPDATE = 705
    BYE = 10
    DESIGNUPD = 123
