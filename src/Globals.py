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

class PowerupType(enum.IntEnum):
    PW_NONE = 1
    PW_BOMB = 2 # Increase Max number of bomb that can be placed
    PW_SPEED = 3 # Increase player speed
    PW_RANGE = 4 # Increase bomb range

SCREENWIDTH = 1366#960
SCREENHEIGHT = 768#640