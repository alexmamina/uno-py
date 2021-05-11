# Go - regular play, regular relay
# Debug - change turn, regular play, print data
# Challenge - only send packet to make player take two cards
# Zerocards - one player is out of cards, forward to the other who will either take cards or send
# points
# Takecards - send back to player out of cards while waiting for the other to take more
# Calc - other player sends points

INIT = -1
GO = 0
CHALLENGE = 1
ZEROCARDS = 2
DEBUG = 3
TAKECARDS = 4
CALC = 5
