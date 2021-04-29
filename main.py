import pygame
import pygame.freetype
import random


maze1 = """
#######################
#.....................#
#.....................#
#.....................#
#.....................#
#.....................#
#######################"""



class Tile:
    pass

class Wall(Tile):
    color = (50,50,50)

class Floor(Tile):
    color = None

class Box:
    def __init__(self, x=None, y=None):
        if x is None and y is None:
            while True:
                x = random.randint(1, Viewer.width // Viewer.grid_size-2)
                y = random.randint(1, Viewer.height // Viewer.grid_size-2)
                for box in Simulation.boxes:
                    if box.x == x and box.y == y:
                        continue
                ok = True
                for ty, row in enumerate(Simulation.tiles):
                    for tx, element in enumerate(row):
                        if ty == y and tx == x and type(element) == Wall:
                            ok = False
                if not ok:
                    continue
                break
        self.x = x
        self.y = y

        self.dx = 0
        self.dy = 0

        self.d = 0
        self.friction = random.choice([32, 64, 96, 128, 160, 192, 224, 255])
        self.color = (self.friction, self.friction, 0)
        self.locked = False

        Simulation.boxes.append(self)

    def move(self):
        if self.locked:
            self.dx, self.dy = 0,0
        if type(Simulation.tiles[self.y+self.dy][self.x+self.dx]) == Wall:
            self.dx, self.dy = 0,0
        for box in Simulation.boxes:
            if box.x == self.x+self.dx and box.y == self.y+self.dy:
                box.dx = self.dx
                box.dy = self.dy
                self.dx, self.dy = 0,0
        for agent in Simulation.agents.values():
            if agent.x == self.x+self.dx and agent.y == self.y+self.dy:
                self.dx, self.dy = 0,0
        self.x += self.dx
        self.y += self.dy
        if self.dx != 0 or self.dy != 0:
            self.d += Viewer.grid_size
            if self.d > self.friction:
                self.dx, self.dy = 0,0
                self.d = 0


class Simulation:
    agents = {}
    tiles = []
    boxes = []
    num_seekers = 2
    num_hiders = 2

class Agent:
    number = 0

    def __init__(self, seeker=False, x=None, y=None, color=None):
        self.number = Agent.number
        Agent.number += 1

        self.seeker = seeker

        if x is None and y is None:
            while True:
                x = random.randint(1, Viewer.width // Viewer.grid_size-2)
                y = random.randint(1, Viewer.height // Viewer.grid_size-2)
                for agent in Simulation.agents.values():
                    if agent.number == self.number:
                        continue
                    if agent.x == x and agent.y == y:
                        continue
                ok = True
                for ty, row in enumerate(Simulation.tiles):
                    for tx, element in enumerate(row):
                        if ty == y and tx == x and type(element) == Wall:
                            ok = False
                if not ok:
                    continue
                break
        self.x = x
        self.y = y

        if color is None:
            while True:
                color = (random.randint(0,150),random.randint(0,150),random.randint(0,150))
                if color == Viewer.background_color:
                    continue
                if color in [a.color for a in Simulation.agents.values()]:
                    continue
                break
        self.color = color
        if self.seeker is True:
            self.color = (255,0,0)
        else:
            self.color = (0,0,255)

        self.viewdirection = 0
        self.viewrange = 5

        Simulation.agents[self.number] = self

    def move_random(self):
        while True:
            dx, dy = random.randint(-1,1), random.randint(-1,1)
            if type(Simulation.tiles[self.y+dy][self.x+dx]) == Wall:
                continue
            ok = True
            for box in Simulation.boxes:
                if box.x == self.x+dx and box.y == self.y+dy:
                    ok = False
            if not ok:
                continue
            break
        self.x += dx
        self.y += dy

        nosw = ((0,1),(1,0),(0,-1),(-1,0))
        boxnosw = [False, False, False, False]
        for n in nosw:
            for b in Simulation.boxes:
                if b.x == self.x+n[0] and b.y == self.y+n[1]:
                    boxnosw[nosw.index(n)] = True
                    b.dx, b.dy = n

class Viewer:
    width = 0
    height = 0
    grid_size = 20
    grid_color = (200,200,200)
    background_color = (255,255,255)
    min_boxes = 60
    max_boxes = 70
    font = None

    def __init__(self,width=800,height=600):

        Viewer.width = width
        Viewer.height = height

        # ---- pygame init
        pygame.init()
        pygame.mixer.init(11025)  # raises exception on fail
        # Viewer.font = pygame.font.Font(os.path.join("data", "FreeMonoBold.otf"),26)
        # fontfile = os.path.join("data", "fonts", "DejaVuSans.ttf")
        # --- font ----
        # if you have your own font:
        # Viewer.font = pygame.freetype.Font(os.path.join("data","fonts","INSERT_YOUR_FONTFILENAME.ttf"))
        # otherwise:
        fontname = pygame.freetype.get_default_font()
        Viewer.font = pygame.freetype.SysFont(fontname, 64)

        # ------ joysticks init ----
        #pygame.joystick.init()
        #self.joysticks = [
        #    pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())
        #]
        #for j in self.joysticks:
        #    j.init()
        self.screen = pygame.display.set_mode(
            (self.width, self.height), pygame.DOUBLEBUF
        )
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.playtime = 0.0

        # ------ background images ------
        # self.backgroundfilenames = []  # every .jpg or .jpeg file in the folder 'data'
        # self.make_background()
        # self.load_images()

        #self.prepare_sprites()
        self.setup()
        self.run()

    def setup(self):
        """call this to restart a game"""
        self.background = pygame.Surface((Viewer.width, Viewer.height))
        self.background.fill(Viewer.background_color)

        self.draw_grid()

        # create fence
        for y in range(Viewer.height // Viewer.grid_size):
            if y == 0 or y == Viewer.height // Viewer.grid_size - 1:
                row = []
                for _ in range(Viewer.width // Viewer.grid_size):
                    row.append(Wall())
                Simulation.tiles.append(row)
                continue
            row = [Wall()]
            for x in range(Viewer.width // Viewer.grid_size - 2):
                row.append(Floor())
            row.append(Wall())
            Simulation.tiles.append(row)

        # create maze (walls/floors)
        for y, line in enumerate(maze1.strip().split("\n")):
            for x, char in enumerate(line):
                if char == "#":
                    Simulation.tiles[y][x] = Wall()
                elif char == ".":
                    Simulation.tiles[y][x] = Floor()

        for b in range(random.randint(Viewer.min_boxes,Viewer.max_boxes)):
            Box()
        self.draw_maze()

        for _ in range(Simulation.num_seekers):
            Agent(seeker=True)
        for _ in range(Simulation.num_hiders):
            Agent(seeker=False)

        #self.player1 = Snake(
        #    pos=pygame.math.Vector2(100, 100),
        #    speed=Snake.speed,
        #    color=(255, 0, 0),
        #    move=pygame.math.Vector2(Snake.speed, 0),
        #)
        #self.player2 = Snake(
        #    pos=pygame.math.Vector2(300, 200),
        #    speed=Snake.speed,
        #    color=(128, 255, 0),
        #    move=pygame.math.Vector2(-Snake.speed, 0),
        #)
        #self.food1 = Food(pos=pygame.math.Vector2(400, 50), color=(255, 255, 0))

    def draw_grid(self):
        # draw grid x
        for x in range(0, Viewer.width, Viewer.grid_size):
            pygame.draw.line(self.background, self.grid_color, (x, 0), (x, Viewer.height), 1)

        # draw grid y
        for y in range(0, Viewer.height, Viewer.grid_size):
            pygame.draw.line(self.background, self.grid_color, (0, y), (Viewer.width, y), 1)

    def draw_maze(self):
        for y, line in enumerate(Simulation.tiles):
            for x, char in enumerate(line):
                if char.color is not None:
                    pygame.draw.rect(self.background, char.color, (x*Viewer.grid_size,y*Viewer.grid_size,Viewer.grid_size, Viewer.grid_size))

    def run(self):
        """The mainloop"""
        running = True

        # --------------------------- main loop --------------------------
        while running:
            for a in Simulation.agents.values():
                a.move_random()
            for b in Simulation.boxes:
                b.move()
            milliseconds = self.clock.tick(self.fps)  #
            seconds = milliseconds / 1000
            self.playtime += seconds
            # -------- events ------
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                # ------- pressed and released key ------
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                        running = False

            # ------------ pressed keys ------
            pressed_keys = pygame.key.get_pressed()

            # ------ mouse handler ------
            left, middle, right = pygame.mouse.get_pressed()

            oldleft, oldmiddle, oldright = left, middle, right
            # ----------- collision detection ------------


            # ---------- clear all --------------
            # pygame.display.set_caption(f"player 1: {self.player1.deaths}   vs. player 2: {self.player2.deaths}")     #str(nesw))
            self.screen.blit(self.background, (0, 0))

            # --------- update all sprites ----------------
            for agent in Simulation.agents.values():
                pygame.draw.rect(self.screen, agent.color, (agent.x*Viewer.grid_size, agent.y*Viewer.grid_size, Viewer.grid_size, Viewer.grid_size))
            for box in Simulation.boxes:
                pygame.draw.rect(self.screen, box.color, (box.x*Viewer.grid_size, box.y*Viewer.grid_size, Viewer.grid_size, Viewer.grid_size))
            #self.allgroup.update(seconds)

            # ---------- blit all sprites --------------
            #self.allgroup.draw(self.screen)
            pygame.display.flip()
            # -----------------------------------------------------
        pygame.mouse.set_visible(True)
        pygame.quit()
        # try:
        #    sys.exit()
        # finally:
        #    pygame.quit()

if __name__ == "__main__":
    viewer = Viewer()
    viewer.run()
