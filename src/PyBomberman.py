import pygame
import Globals
import Inputbox
import enum
import xml.etree.ElementTree
from pygame import Rect
import socket
import random
import pickle
import uuid
import math

ImageCache = {}
MenuFont = None
NumFrames = 0

class MapObject(object):
    def Draw(self,Screen):
        if self.PowerUp is not Globals.PowerupType.PW_NONE :
            Screen.blit(ImageCache[Globals.PowerupType(self.PowerUp).name], (self.x, self.y))
            return
        Screen.blit(ImageCache['FixedTile'], (self.x, self.y))
    def __init__(self,x = 0,y = 0,PowerUp = Globals.PowerupType.PW_NONE):
        self.x = x
        self.y = y
        self.Breakable = False
        self.Remove = False
        self.PowerUp = PowerUp;

class Explosion(object):
  #def TimeToDraw(self) :
  #  self.LastFrameTime += 16.0
   # print("Frame:",self.LastFrameTime)
    #if( self.LastFrameTime < 350 ) :
     # return False
    #self.Frame += 1
    #if( self.Frame == 3 ) :
     # self.Frame = 0
    #self.LastFrameTime = 0.
    #return True
  
  def Draw(self,Screen) :
    #if( not(self.TimeToDraw())) :
     # return;
    #print("Frame:",self.Frame)
   # LastFrameTime += 16.0
   # if( self.LastFrameTime < 350 ) :
    #  return;
    CurrentImage = ImageCache['BombAnim']
    if( self.Health <= 0 ) :
      ExplosionList.remove(self)
    u = self.Frame * 139.
    v = 0.
    #MaxU = (self.Frame * 139.f) + 134.f
    #MaxV = 134.f
    AtlasRect = Rect(u,v,134.,134.)
    FrameImage = pygame.Surface(AtlasRect.size,pygame.SRCALPHA, 32).convert_alpha()
    FrameImage.set_alpha(255)
    FrameImage.blit(CurrentImage, (0, 0), AtlasRect)
    Screen.blit(FrameImage, (self.x - 48, self.y - 48))
    self.Health -= 1
    self.Frame += 1
     
  def __init__(self,x,y) :
    self.x = x
    self.y = y
    self.Health = 350
    self.Frame = 0
    self.LastFrameTime = 0.
    

class Bomb(object):
    def AdjustOwnerBombCount(self):
        global Players
        for player in Players :
            if not(player.Used) :
                continue
            if player.ID == self.OwnerID :
                player.NumUsedBombs -= 1
    def Explode(self):
        global Players
        # Determine if we have to remove any tile within our range.
        BRects = [ Rect(self.x + 32, self.y, 32, 32), Rect(self.x - 32, self.y, 32, 32),
                   Rect(self.x, self.y + 32, 32, 32), Rect(self.x, self.y - 32, 32, 32)]
        for Tile in Map :
            if Tile.Breakable == False :
               continue
            TRect = Rect(Tile.x, Tile.y, 32, 32)
            if TRect.collidelist(BRects) != -1 :
                RandomPowerUp = Globals.PowerupType(random.choice(list(Globals.PowerupType)))
                if(  not(RandomPowerUp == Globals.PowerupType.PW_NONE) ) :
                    Map.append(MapObject(Tile.x,Tile.y,RandomPowerUp))
                Map.remove(Tile)
        self.AdjustOwnerBombCount()
        for player in Players :
            PRect = Rect(player.x, player.y, 32, 32)
            if PRect.collidelist(BRects) != -1 or (player.x == self.x and player.y == self.y):
                # Player died.
                # Find the owner
                #if self.OwnerID == player.ID :
                    #print("Player suicided.")
                #else :
                    #print("Client ID ", self.OwnerID, " killed ", player.ID)
                    #if self.OwnerID == NetInterface.ID :
                     #   GetMainPlayer().NumKills += 1
                 #    print("YAY KILLED!")
                 if player.ID == GetMainPlayer().ID :
                     continue
                 if not(player.Used) :
                     continue
                 player.Used = False
                 print("Player died");
                 GetMainPlayer().NumKills += 1
                 NetInterface.PackAndWriteOp(Globals.NetworkOP.OP_DIED, 
                                             player.ID.to_bytes(8,'little'),player.Address)
            
    def Draw(self, Screen):
        Screen.blit(ImageCache['Bomb'], (self.x, self.y))
        self.Time -= 1
    def __init__(self, OwnerID, x, y):
        self.x = x
        self.y = y
        self.OwnerID = OwnerID
        self.Time = 350

ExplosionList = []
BombList = []
Map = []
MenuLabels = {}
Players = []
# Temp
# TMap = None
def AddBomb(OwnerID, x, y):
    # Sanity check
    for Tile in Map :
        if Tile.x == x and Tile.y == y :
            print("Bad bomb position (In Tile).")
            break
    for B in BombList :
        if B.x == x and B.y == y :
            print("Bad bomb position (Already Exists).")
            break
    else :
        BombList.append(Bomb(OwnerID, x, y))
        print("Done!")
        return True
    return False
class Player(object):
    '''
    classdocs
    '''

    class Direction(enum.IntEnum):
        DIR_FRONT = 1
        DIR_BACK = 2
        DIR_LEFT = 3
        DIR_RIGHT = 4


    def CollectPowerUp(self,Tile):
        if Tile.PowerUp == Globals.PowerupType.PW_BOMB :
            self.NumBombs += 1
        if Tile.PowerUp == Globals.PowerupType.PW_SPEED:
            self.ChangeSpeed(8)
        if Tile.PowerUp == Globals.PowerupType.PW_RANGE:
            self.BombRange += 16
        Map.remove(Tile)


    def CheckCollisions(self):
        Player = Rect(self.x, self.y, 32, 32)
        for Tile in Map :
            TileRect = Rect(Tile.x, Tile.y, 32, 32)
            HasCollided = Player.colliderect(TileRect)
            if HasCollided:
                if( Tile.PowerUp is not Globals.PowerupType.PW_NONE) :
                    self.CollectPowerUp(Tile)
                    return False
                if self.Dir == self.Direction.DIR_LEFT:
                    self.x = TileRect.right
                if self.Dir == self.Direction.DIR_RIGHT:
                    self.x = TileRect.left - Player.width
                if self.Dir == self.Direction.DIR_FRONT:
                    self.y =  TileRect.top - Player.height
                if self.Dir == self.Direction.DIR_BACK:
                    self.y = TileRect.bottom
                return True
        return False
    def Move(self,Key):
        LocalKey = pygame.key.get_pressed()
        if LocalKey[pygame.K_RIGHT]:
            self.Dir = self.Direction.DIR_RIGHT
            self.x += self.Speed
            self.CheckCollisions()
        if LocalKey[pygame.K_LEFT]:
            self.Dir = self.Direction.DIR_LEFT
            self.x -= self.Speed
            self.CheckCollisions()
        if LocalKey[pygame.K_UP]:
            self.Dir = self.Direction.DIR_BACK
            self.y -= self.Speed
            self.CheckCollisions()
        if LocalKey[pygame.K_DOWN]:
            self.Dir = self.Direction.DIR_FRONT
            self.y += self.Speed
            self.CheckCollisions()
        if LocalKey[pygame.K_SPACE]:
            if self.NumUsedBombs < self.NumBombs :
                if AddBomb(self.ID, self.x, self.y):
                    for player in Players:
                        if player.ID == self.ID:
                            continue
                        if not (player.Used):
                            continue
                        NetInterface.PackAndWriteOp(Globals.NetworkOP.OP_ADDBOMB,
                                                pickle.dumps((self.ID, self.x, self.y)), player.Address)
                    self.NumUsedBombs += 1
        if LocalKey[pygame.K_PLUS] :
            self.ChangeSpeed(8)
        if LocalKey[pygame.K_MINUS]:
            self.ChangeSpeed(-8)

    def Draw(self,Delta,Screen):
        if not(self.Used) :
            return
        pygame.draw.rect(Screen, (0, 0, 255), (self.x, self.y, 32, 32), 1)
        if self.Dir == self.Direction.DIR_FRONT :
            Screen.blit(ImageCache['PlayerFront'], (self.x, self.y))
        if self.Dir == self.Direction.DIR_BACK :
            Screen.blit(ImageCache['PlayerBack'], (self.x, self.y))
        if self.Dir == self.Direction.DIR_LEFT:
            Screen.blit(ImageCache['PlayerSideLeft'], (self.x, self.y))
        if self.Dir == self.Direction.DIR_RIGHT :
            Screen.blit(ImageCache['PlayerSideRight'], (self.x, self.y))
    def ChangeSpeed(self,NSpeed):
        Temp = self.Speed + NSpeed
        if( Temp > self.MAX_SPEED or Temp <= 0) :
            return
        self.Speed = Temp
    # Init a new player at given position.
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y
        self.ID = 1
        self.Address = ('0.0.0.0', 0)
        self.Used = False
        self.NumKills = 0
        self.Speed = 8
        self.NumBombs = 1
        self.BombRange = 16
        self.NumUsedBombs = 0
        self.Dir = self.Direction.DIR_FRONT
        self.MAX_SPEED = 56

# MainPlayer = None
class NetChannel():
    def ParseMessage(self, Address, Message):
        global Players
        #print("Got message ", Address, " ", Message)
        #print("Client ID: ", self.ID)
        Bytes = bytearray(Message)

        ClientID = int.from_bytes(Bytes[:8], 'little')
        OpCode = int.from_bytes(Bytes[8:12], 'little')
        #print("OpCode: ", OpCode)
        if OpCode == Globals.NetworkOP.OP_CHALLENGE :
            # TODO:Check if there is room for the client...
            for player in Players :
                if not(player.Used) :
                    player.ID = ClientID
                    player.Address = Address
                    player.Used = True
                    break
            self.WriteOp(Globals.NetworkOP.OP_CHALLENGERESPONSE, 0, Address)
            return
        if OpCode == Globals.NetworkOP.OP_CHALLENGERESPONSE :
            self.WriteOp(Globals.NetworkOP.OP_GETINFO, 0, Address)
            self.Challenging = False
            return;
        if OpCode == Globals.NetworkOP.OP_GETINFO :
            self.PackAndWriteOp(Globals.NetworkOP.OP_INFORESPONSE, pickle.dumps(Players), Address)
            return
        if OpCode == Globals.NetworkOP.OP_INFORESPONSE :
            Players = pickle.loads(Bytes[12:])
            StartNewGame()
            for player in Players :
                if player.ID == ClientID :
                    player.Address = Address
            return            
        if OpCode == Globals.NetworkOP.OP_UPDATEPLAYERPOS :
            for player in Players :
                if player.ID == ClientID :
                    player.x, player.y = pickle.loads(Bytes[12:])
            return
        if OpCode == Globals.NetworkOP.OP_DISCONNECT :
            print(self.ID)
            print(ClientID)
            for pl in Players :
                print(pl.ID)
                if pl.ID == ClientID :
                    pl.Used = False
            if( GetConnectedPlayers() <= 1 ) :
              Globals.GameIsRunning = False
        if OpCode == Globals.NetworkOP.OP_DIED :
            PId = int.from_bytes(Bytes[12:], 'little')
            for p in Players :
                if p.ID == PId :
                    p.Used = False
        if OpCode == Globals.NetworkOP.OP_ADDBOMB :
            ID, x, y = pickle.loads(Bytes[12:])
            BombList.append(Bomb(ID, x, y))
        if OpCode == Globals.NetworkOP.OP_REMOVETILE :
            x, y = pickle.loads(Bytes[12:])
            for tile in Map :
                if tile.x == x and tile.y == y :
                    Map.remove(tile)
                    
    def GetPackets(self):
        while True :
            try:
                Message, Address = self.Socket.recvfrom(4096)
                # Message = Message.decode('utf-8')
                # Process message
                self.ParseMessage(Address, Message)
            except socket.error:
                return
    def WriteInfoRequest(self, IpDest):
        self.WriteString(IpDest, "GetInfo")
        self.WaitingInfo = True
    
    def WriteString(self, Address, Message):
        #print("Writing!" , Message, Address)
        self.Socket.sendto(Message.encode(), Address)
    def WriteData(self, Address, Data):
        self.Socket.sendto(Data, Address)
    
    # IpDest => Tuple
    def WriteOp(self, Op, Value, IpDest):
       # print("Writing OP: ", Op, "Value: ", Value, "To: ", IpDest)
        Data = self.PackData(Op, Value)
        self.Socket.sendto(Data, IpDest)
    def PackAndWriteOp(self, Op, Value, IpDest):
       # print("Writing Packed OP: ", Op, "Value: ", Value, "To: ", IpDest)
        Data = self.PackInfo(Op, Value)
        self.Socket.sendto(Data, IpDest)
    # Create new struct first field is always the ID.
    def PackData(self, Key, Value):
        Data = bytearray()
        # Data.append(self.ID.to_bytes(8, 'little'))
        GUID = bytearray(self.ID.to_bytes(8, 'little'))
        Op = bytearray(Key.to_bytes(4, 'little'))
        Data += GUID
        Data += Op
        # Data.append(GUID)
        Data.append(Value)
        return Data
    def PackInfo(self, Key, PInfo):
        Data = bytearray()
        # Data.append(self.ID.to_bytes(8, 'little'))
        GUID = bytearray(self.ID.to_bytes(8, 'little'))
        Op = bytearray(Key.to_bytes(4, 'little'))
        Data += GUID
        Data += Op
        Data += PInfo
        return Data
    # def WritePlayerInfo(self,player):
     #   self.
    def Init(self,HasToBind) :
        self.ServerAddress = '0.0.0.0'
        self.Port = 54290
        self.Socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.Socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.Socket.setblocking(False)
        if( HasToBind ) :
           self.Socket.bind((self.ServerAddress, self.Port))
        self.Challenging = False
        self.WaitingInfo = False
    def __init__(self,HasToBind = True):
        # Bind to any
        self.Init(HasToBind)
        self.ID = uuid.uuid1().int >> 64
        
NetInterface = NetChannel()
def LoadImage(Name, Path):
    Image = pygame.image.load(Path)
    ImageCache[Name] = Image

def StartNewGame():
    TMap = LoadMap("Maps/TestMap.xml")
    Globals.GameIsRunning = True
    global Players
    print("StartNewGame: ", GetConnectedPlayers())
    if not(GetMainPlayer()) :
        for player in Players :
            if not(player.Used) :
                # Assign it to us.
                player.ID = NetInterface.ID
                player.Used = True
                player.x += 32
                player.y -= 32
                print("StartNewGame: ", GetConnectedPlayers())
                return
def GetMainPlayer():
    for p in Players :
        if p.ID == NetInterface.ID :
            return p
    return None
def CheckGameEvent():
    # Check event from the network if in multiplayer.
    for Event in pygame.event.get():
        if Event.type == pygame.QUIT :
           for player in Players :
              if player.ID == NetInterface.ID or player.Used == False:
                 continue
              NetInterface.WriteOp(Globals.NetworkOP.OP_DISCONNECT, 0, player.Address)
           Globals.HasToQuit = True
        if Event.type == pygame.KEYDOWN :
            if Event.key == pygame.K_ESCAPE :
                Globals.GameIsRunning = False
    GetMainPlayer().Move(0)

def CheckMenuEvent(Screen, MenuFont):
    for Event in pygame.event.get():
        if Event.type == pygame.QUIT :
            Globals.HasToQuit = True
        if Event.type == pygame.MOUSEBUTTONDOWN :
                # Check if Mouse is over
                for Key in MenuLabels.keys() :
                    MSurf = MenuFont.render(Key, 1, (255, 0, 0))
                    MSurfRect = MSurf.get_rect(center=(MenuLabels[Key]))
                    if MSurfRect.collidepoint(pygame.mouse.get_pos()) :
                        if Key == 'Quit.' :
                            Globals.HasToQuit = True
                        if Key == 'Start Game.' :
                            print("Starting up")
                            #Make sure we bind socket to IpAddress:Port
                            NetInterface.Socket.close()
                            NetInterface.Init(True)
                            StartNewGame()
                        if Key == 'Join Game.' :
                            # Open Input dialog in order to connect
                            print("Connecting.")
                        # blit txtbx on the sceen
                            InputTextBox = Inputbox.TextInput()
                            InputTextBox.set_text_color((255, 0, 0))
                            while(not(InputTextBox.update(pygame.event.get()))) :
                                Screen.fill((75, 111, 77))
                                InputText = InputTextBox.get_font().render("Ip address: ", 1, (255, 0, 0))
                                Screen.blit(InputText, (500, 300 - InputTextBox.get_font().get_height()))
                                Screen.blit(InputTextBox.get_surface(), (500, 300))
                                MExitSurf = InputTextBox.get_font().render("Back", 1, (255, 0, 0))
                                MExitRect = MSurf.get_rect(topleft=((500,370 + InputTextBox.get_font().get_height())))
                                Screen.blit(MExitSurf,MExitRect)
                                if( pygame.mouse.get_pressed()[0] and MExitRect.collidepoint(pygame.mouse.get_pos()) ) :
                                  return
                                pygame.display.flip()
                            if( InputTextBox.get_text() == '127.0.0.1' ) :
                                NetInterface.Socket.close()
                                NetInterface.Init(False)
                            NetInterface.Challenging = True
                            NetInterface.WriteOp(Globals.NetworkOP.OP_CHALLENGE, 0,
                                                 (InputTextBox.get_text(), NetInterface.Port))
        if Event.type == pygame.KEYDOWN :
           if Event.key == pygame.K_RETURN :
               if pygame.key.get_mods() & pygame.KMOD_ALT :
                   pygame.display.toggle_fullscreen()

# def MapFindPlayerSpawn():
    # for Position in PSpawn :
        
def SendPlayerPos():
    global Players
    player = GetMainPlayer()
    for client in Players:
        if client.ID == player.ID :
            continue
        if not(client.Used) :
            continue
        NetInterface.PackAndWriteOp(Globals.NetworkOP.OP_UPDATEPLAYERPOS,
                                    pickle.dumps((player.x, player.y)), client.Address)
def GetConnectedPlayers() :
  global Players
  NumPlayers = 0
  for player in Players :
    if not(player.Used) :
      continue
    NumPlayers += 1
  return NumPlayers

def DrawMap(Map, Screen):
    for Tile in Map :
        if Tile.Remove == True :
            Map.remove(Tile)
            continue
        Tile.Draw(Screen);
    for Bomb in BombList :
        if Bomb.Time <= 0 :
            # Explode!
            Bomb.Explode()
            ExplosionList.append(Explosion(Bomb.x,Bomb.y))
            BombList.remove(Bomb)
            continue
        Bomb.Draw(Screen)
    for explosion in ExplosionList :
      explosion.Draw(Screen)

def DrawMenu(Screen, MenuFont):
    if Globals.GameIsRunning :
        return
    # Draw our entries
    for Entry in MenuLabels.keys() :
        MSurf = MenuFont.render(Entry, 1, (255, 0, 0))
        MSurfRect = MSurf.get_rect(center=(MenuLabels[Entry]))
        Screen.blit(MSurf, MSurfRect)
        

def LoadMap(Path):
    player = None
    IsPlayer = False
    MRoot = xml.etree.ElementTree.parse("Maps/TestMap.xml").getroot()
    i = 0
    for Tile in MRoot.find('TileInfo'):
        #print(Tile.tag)
        MObject = MapObject()
        for DInfo in Tile:
            if DInfo.tag == 'Type':
                if DInfo.text == 'TILE_PLAYER' :
                    IsPlayer = True
                    player = Player()
            if IsPlayer :
                if DInfo.tag == 'X' :
                    player.x = int(DInfo.text)
                if DInfo.tag == 'Y' :
                    player.y = int(DInfo.text)
            else :
                if DInfo.tag == 'Breakable' :
                    if DInfo.text == 'true' :
                        MObject.Breakable = True
                    else :
                        MObject.Breakable = False
                if DInfo.tag == 'X' :
                    MObject.x = int(DInfo.text)
                if DInfo.tag == 'Y' :
                    MObject.y = int(DInfo.text)
        if IsPlayer == False:
            # Loop didn't brake so we need to add a new tile!
            Map.append(MObject)
            i += 1
        else :
            Players.append(player)
            IsPlayer = False
    return Map
def InitMenu(MFont):
    # ,'Join Game''
    MenuLabels['Start Game.'] = (Globals.SCREENWIDTH / 2, Globals.SCREENHEIGHT / 2)
    MenuLabels['Join Game.'] = (Globals.SCREENWIDTH / 2, (Globals.SCREENHEIGHT / 2) + MFont.get_height() * len(MenuLabels))
    MenuLabels['Quit.'] = (Globals.SCREENWIDTH / 2, (Globals.SCREENHEIGHT / 2) + MFont.get_height() * len(MenuLabels))

def CheckExitCondition(gameDisplay,ExitDictionary):
    global NumFrames
    NumAlive = 0
    global Players
    if GetMainPlayer().Used == False :
      gameDisplay.blit(ExitDictionary["GameOver"][0], ExitDictionary["GameOver"][1])
      #Wait 5 seconds before going back to main menu.
      if NumFrames >= 300 :
        NumFrames = 0
        Globals.GameIsRunning = False
      NumFrames += 1
      return True;
    for player in Players :
        if player.ID == GetMainPlayer().ID :
            continue
        if not(player.Used) :
            continue
        NumAlive += 1
    if NumAlive == 0 and GetMainPlayer().NumKills > 0 :
      gameDisplay.blit(ExitDictionary["Win"][0], ExitDictionary["Win"][1])
      #Wait 5 seconds before going back to main menu.
      if NumFrames >= 300 :
        NumFrames = 0
        Globals.GameIsRunning = False
      NumFrames += 1
      return True
    return False
def CacheTextures() :
    LoadImage("PlayerFront", "Textures/PlayerFront.png")
    LoadImage("PlayerBack", "Textures/PlayerBack.png")
    LoadImage("PlayerSideLeft", "Textures/PlayerSideLeft.png")
    LoadImage("PlayerSideRight", "Textures/PlayerSideRight.png")
    LoadImage("FixedTile", "Textures/Brick.png")
    LoadImage("DestructibleTile", "Textures/Player.png")
    LoadImage("Bomb", "Textures/Bomb32.png")
    LoadImage("BombAnim", "Textures/Explosion.png")
    LoadImage("PW_BOMB", "Textures/BombPowerUp.png")
    LoadImage("PW_SPEED", "Textures/SpeedPowerUp.png")
    LoadImage("PW_RANGE", "Textures/RangePowerUp.png")

def main():
    pygame.init()
    pygame.key.set_repeat(1, 100)
    GameFont = pygame.font.SysFont("monospace", 24)
    MenuFont = pygame.font.SysFont("monospace", 32)
    gameDisplay = pygame.display.set_mode((Globals.SCREENWIDTH, Globals.SCREENHEIGHT))
    Background = pygame.Surface(gameDisplay.get_size()).convert()
    Background.fill((75, 111, 77))
    pygame.display.set_caption('PyBomberman')
    clock = pygame.time.Clock()
    CacheTextures()
    InitMenu(MenuFont)
    ExitDictionary = {};
    WinLabel = GameFont.render("YOU WIN!", 1, (255, 0, 0))
    WinRect = WinLabel.get_rect(center=(Globals.SCREENWIDTH/2,Globals.SCREENHEIGHT/2))
    GameOverLabel = GameFont.render("YOU LOSE!", 1, (255, 0, 0))
    GameOverRect = GameOverLabel.get_rect(center=(Globals.SCREENWIDTH/2,Globals.SCREENHEIGHT/2))
    WaitPlayersLabel = GameFont.render("Waiting for more players to join", 1, (255, 0, 0))
    WaitPlayersRect = WaitPlayersLabel.get_rect(center=(Globals.SCREENWIDTH/2,Globals.SCREENHEIGHT/2))
    ExitDictionary['Win'] = [WinLabel,WinRect]
    ExitDictionary['GameOver'] = [GameOverLabel,GameOverRect]
    StartTime = pygame.time.get_ticks()
    while(Globals.HasToQuit != True) :
        #Delta computation.
        Optimal_Time_Seconds = 1000 / 60.0;
        UpdateLength = pygame.time.get_ticks() - StartTime
        Delta = UpdateLength / Optimal_Time_Seconds
        if( ( pygame.time.get_ticks() - StartTime ) >= 1000 ) :
            StartTime = pygame.time.get_ticks()
        # Clear the bg.
        gameDisplay.blit(Background, (0, 0))
        NetInterface.GetPackets()
        if Globals.GameIsRunning == False :
            # Draw Menu
            CheckMenuEvent(gameDisplay, MenuFont)
            DrawMenu(gameDisplay, MenuFont)
        else :
            CheckGameEvent()
            if( not(CheckExitCondition(gameDisplay,ExitDictionary)) ) :
                #if( GetConnectedPlayers() > 1 ) :
                if 1 :
                 DrawMap(Map, gameDisplay)
                 for player in Players :
                     player.Draw(Delta,gameDisplay)
                 SendPlayerPos()
                else :
                  gameDisplay.blit(WaitPlayersLabel,WaitPlayersRect)

        clock.tick(60)
        LocalSpeed = 0 if GetMainPlayer() == None  else GetMainPlayer().Speed
        label = GameFont.render("FPS:{f:.2f} || Bomb:{d} || Speed:{s}"
                                .format(f=clock.get_fps(), d=len(BombList),s=LocalSpeed), 1, (255, 0, 0))
        gameDisplay.blit(label, (0, 0))
        pygame.display.flip()
    pygame.quit()
    quit()
    
if __name__ == '__main__':
    main()
  
  
    
