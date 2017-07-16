import enum
#Define the current state of the program.
GameIsRunning = False
HasToQuit = False
IsConnected = False

class NetworkOP(enum.IntEnum):
    OP_CHALLENGE = 1 # No Value
    OP_CHALLENGERESPONSE = 2 # No Value
    OP_GETINFO = 3 # No Value
    OP_INFORESPONSE = 4 # Pickle array
    OP_UPDATEPLAYERPOS = 5 # Value => x,y
    OP_ADDBOMB = 7
    OP_REMOVETILE = 8
    OP_DIED = 9 # Value => ID
    OP_DISCONNECT = 6

SCREENWIDTH = 960
SCREENHEIGHT = 640