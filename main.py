import pygame
import pygame.freetype
import random
#import fov_tools

maze1 = """
#######################
#.....................#
#.....................#
#......aaa.bbb.ccc....#
#......aaa.bbb.ccc....#
#.....................#
##########AAA#BBB#CCC##
#.....................#
#........aaa.bbb.ccc..#
#.....................#"""


def choose_random_place():
    """ choose a place in the playfield that is not occupied
        bye other boxes, agents, walls or closed doors

        returns: x,y [int]
    """
    ok = False
    while not ok:
        x = random.randint(1, Viewer.width // Viewer.grid_size - 2)
        y = random.randint(1, Viewer.height // Viewer.grid_size - 2)
        for box in Simulation.boxes:
            if box.x == x and box.y == y:
                continue
        ok = True
        for ty, row in enumerate(Simulation.tiles):
            for tx, element in enumerate(row):
                if (ty == y and tx == x):
                    if type(element) in [Wall, PressurePlate, Door, TransparentWall]:
                        ok = False
                        break
    return x, y

class Tile:
    """parent class of a basic tile like floor, wall etc."""
    block_sight = False
    block_movement = False

class Wall(Tile):
    """outer border of playfield must be made out of walls"""
    color = (50, 50, 50)
    block_sight = True
    block_movement = True

class TransparentWall(Tile):
    """a wall out of transparent material"""
    color = (0, 255, 255) # light blue
    block_sight = False

class Floor(Tile):
    """allows unrestricted movement of boxes, agents etc"""
    color = None

class PressurePlate(Tile):
    def __init__(self, x, y, key=1):
        self.x = x
        self.y = y
        self.key = key
        self.color = (0, 255, 0)

        Simulation.pressureplates.append(self)


class Door:
    def __init__(self, x, y, key=1):
        self.x = x
        self.y = y
        self.key = key
        self.closed = True
        self.coloropen = (255, 255, 255)
        self.colorclosed = (0, 0, 0)
        #self.color = self.colorclosed
        Simulation.doors.append(self)

    @property
    def color(self):
        if self.closed:
            return self.colorclosed
        return self.coloropen

    @property
    def block_sight(self):
        # the door blocks the field of view (fov) only when closed
        if self.closed:
            return True
        return False

    @property
    def block_movement(self):
        if self.closed:
            return True
        return False

class Box:
    block_sight = True
    block_movement = True

    def __init__(self, x=None, y=None):
        if x is None and y is None:
            x,y = choose_random_place()
        elif not all((x,y)):  # anything other than None/False/0 is considered True for all
            raise ValueError(f"x {x} and y {y} must be both None or must both be an integer vale! ")
        self.x = x
        self.y = y

        self.dx = 0
        self.dy = 0

        self.d = 0
        self.friction = random.choice([32, 64, 96, 128, 160, 192, 224, 255]) # TODO: need physic for friction
        self.color = (self.friction, self.friction, 0)
        self.locked = False

        Simulation.boxes.append(self)

    def move(self):
        if self.locked:
            self.dx, self.dy = 0, 0
            return
        block_in_path = Simulation.tiles[self.y + self.dy][self.x + self.dx]
        if block_in_path.block_movement:
            self.dx, self.dy = 0,0
            return
        for box in Simulation.boxes:
            if box.x == self.x + self.dx and box.y == self.y + self.dy:
                box.dx = self.dx # TODO: impulse to other boxes need physic !
                box.dy = self.dy # TODO: impulse to other boxes need physic !
                self.dx, self.dy = 0, 0
                return
        for agent in Simulation.agents.values():
            if agent.x == self.x + self.dx and agent.y == self.y + self.dy:
                self.dx, self.dy = 0, 0
                return
        self.x += self.dx
        self.y += self.dy
        if self.dx != 0 or self.dy != 0:
            self.d += Viewer.grid_size
            if self.d > self.friction:
                self.dx, self.dy = 0, 0
                self.d = 0


class Simulation:
    agents = {}  # {agent_number: agent instance}
    tiles = []
    boxes = []
    pressureplates = []
    doors = []
    num_seekers = 2
    num_hiders = 2
    fov_map = []


class Agent:
    number = 0

    def __init__(self, seeker=False, x=None, y=None, hp=1):
        self.number = Agent.number
        Agent.number += 1
        self.torch_radius = 5
        self.hp = hp
        # field of view: a list of list, matching the tiles of the simulation. each item can be True or False
        self.fov = []
        self.seeker = seeker


        self.grabbing_state = 0  # 0 (or False) ..... No State (can move, grab, push)
                                 # 1 (or True) ..... Grabbed Box (can move, drop)

        self.grabbed_box = None # reference to the grabbed box instance, can also be a corpse

        self.turns_alive = 0 # counter, how many turns agent was alive

        if x is None and y is None:
            x, y = choose_random_place()
        elif not all((x,y)):  # anything other than None/False/0 is considered True for all
            raise ValueError(f"x {x} and y {y} must be both None or must both be an integer vale! ")

        self.x = x
        self.y = y

        red_min, green_min, blue_min = 0, 0 ,0
        red_max, green_max, blue_max = 255,255,255
        if self.seeker is True:
            red_min = 255
            green_max = 50
            blue_max = 50
        else:
            red_max = 50
            green_max = 50
            blue_min=255
        self.color = self.choose_random_color(red_min, red_max, green_min, green_max, blue_min, blue_max)

        self.viewdirection = 0
        self.viewrange = 5

        Simulation.agents[self.number] = self

    def get_objects_near_me(self):
        """returns a list of boxes or corpses around my position"""
        near_me = []
        #for (dx,dy) in ((-1,-1),(0,-1),(1,-1),(-1,0),(1,0),(-1,1),(0,1),(1,1) ):
        for (dx, dy) in ( (0, -1), (-1, 0), (1, 0),  (0, 1) ):
            for item in (Simulation.boxes + [body for body in Simulation.agents.values() if body.hp <= 0]):
                if (item.x == self.x + dx) and (item.y == self.y +dy):
                    near_me.append(item)
        return near_me

    def choose_random_color(self, red_min=0, red_max=255, green_min=0, green_max=255, blue_min=0, blue_max=255):
        """returns a color not used by another agent or by Simulation_background_color"""
        while True:
            color = (random.randint(red_min, red_max), random.randint(green_min, green_max), random.randint(blue_min, blue_max))
            if color == Viewer.background_color:
                continue
            if color in [a.color for a in Simulation.agents.values()]:
                continue
            return color

    def random_action(self):
        possible_actions = [self.wait, self.move_random ]
        
        near_me = self.get_objects_near_me()
        if near_me: # same as : if len(get_objects_near_me()) > 0:
            possible_actions.append(self.kick) # grabbed box is excluded from kicking in later code
            if not self.grabbing_state:
                possible_actions.append(self.grab)
        if self.grabbing_state:
            possible_actions.append(self.drop)
        
        action = random.choice(possible_actions)
        action()


    def wait(self):
        pass
    
    def drop(self):
        self.grabbing_state = 0 
        self.grabbed_box = None

    def move_random(self):
        #directions =  ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1))
        directions = ( (0, -1), (-1, 0), (1, 0),  (0, 1), )
        dx, dy = random.choice(directions)
        self.move(dx,dy)
        

    def move(self, dx, dy):
        ok = True
        tile_in_my_path = Simulation.tiles[self.y + dy][self.x + dx]
        if tile_in_my_path.block_movement:
            return # no movement
        # run into other agents? corpses are blocking the way, like boxes
        for other in Simulation.agents.values():
            if other.number == self.number:
                continue
            if other.x == self.x + dx and other.y == self.y + dy:
                if self.seeker and not other.seeker and other.hp > 0:
                    other.hp = 0 # kill hider if self.seeker
                if other.seeker and not self.seeker:
                    self.hp = 0 # kill myself
                return  # no movement

        # box blocks movement?
        for box in [b for b in list(Simulation.agents.values()) + Simulation.boxes if b != self.grabbed_box]:
            if box.x == self.x + dx and box.y == self.y + dy:
                return # no movement

        oldx, oldy = self.x, self.y
        self.x += dx
        self.y += dy
        #print("moving...")
        #print("state:", self.grabbing_state)
        if self.grabbing_state:
            # Box is grabbed -> Move with us
            self.grabbed_box.x = oldx
            self.grabbed_box.y = oldy
            print("moved grabbing box", self.grabbed_box)

    def grab(self):
        #if self.grabbing_state == 1 or not self.get_objects_near_me:
        #    # already busy grabbing box or no object to grab
        #    return
        self.grabbed_box = random.choice(self.get_objects_near_me())
        self.grabbing_state = 1
        print("GRABBING", self.grabbed_box, self.grabbed_box.x, self.grabbed_box.y)


    def drop(self):
        #if self.grabbing_state != 1:
        #    # no box grabbed
        #    return
        print("dropping")
        self.grabbing_state = 0
        self.grabbed_box = None

    def kick(self):
        #if self.grabbing_state == 1:
        #    # cant kick when grabbing box
        #    return
        #directions = ((0, 1), (1, 0), (0, -1), (-1, 0))
        near_me = [item for item in self.get_objects_near_me() if item != self.grabbed_box]
        if near_me:
            kicked_object = random.choice(near_me)
            kicked_object.dx, kicked_object.dy =  kicked_object.x - self.x, kicked_object.y - self.y

    def make_fov_map(self, remove_artifacts = False):
        # clear fov_map
        self.fov_map = [[False for tile in line] for line in Simulation.tiles]
        # self.checked = set() # clear the set of checked coordinates
        px, py, = self.x, self.y
        # set all tiles to False
        # set player's tile to visible
        self.fov_map[py][px] = True
        # get coordinates form player to point at end of torchradius / torchsquare
        endpoints = set()
        for y in range(py - self.torch_radius, py + self.torch_radius + 1):
            if y == py - self.torch_radius or y == py + self.torch_radius:
                for x in range(px - self.torch_radius, px + self.torch_radius + 1):
                    endpoints.add((x, y))
            else:
                endpoints.add((px - self.torch_radius, y))
                endpoints.add((px + self.torch_radius, y))
        for coordinate in endpoints:
            # a line of points from the player position to the outer edge of the torchsquare
            points = get_line((px, py), (coordinate[0], coordinate[1]))
            self.calculate_fov_points(points)
        # print(Game.fov_map)
        # ---------- the fov map is now ready to use, but has some ugly artifacts ------------
        # ---------- start post-processing fov map to clean up the artifacts ---
        if not remove_artifacts:
            return
        # -- basic idea: divide the torch-square into 4 equal sub-squares.
        # -- look of a invisible wall is behind (from the player perspective) a visible
        # -- ground floor. if yes, make this wall visible as well.
        # -- see https://sites.google.com/site/jicenospam/visibilitydetermination
        # ------ north-west of player
        for xstart, ystart, xstep, ystep, neighbors in [
            (-self.torch_radius, -self.torch_radius, 1, 1, [(0, 1), (1, 0), (1, 1)]),
            (-self.torch_radius, self.torch_radius, 1, -1, [(0, -1), (1, 0), (1, -1)]),
            (self.torch_radius, -self.torch_radius, -1, 1, [(0, -1), (-1, 0), (-1, -1)]),
            (self.torch_radius, self.torch_radius, -1, -1, [(0, 1), (-1, 0), (-1, 1)])]:

            for x in range(px + xstart, px, xstep):
                for y in range(py + ystart, py, ystep):
                    # not even in fov?
                    try:
                        visible = self.fov_map[y][x]
                    except IndexError:
                        continue
                    if visible:
                        continue  # next, i search invisible tiles!
                    # oh, we found an invisble tile! now let's check:
                    # is it a wall?
                    if not Simulation.tiles[y][x].block_sight:
                        continue  # next, i search walls!
                    # --ok, found an invisible wall.
                    # check south-east neighbors

                    for dx, dy in neighbors:
                        # does neigbor even exist?
                        try:
                            v = self.fov_map[y + dy][x + dx]
                            t = Simulation.tiles[y + dy][x + dx]
                        except IndexError:
                            continue
                        # is neighbor a tile AND visible?
                        if not t.block_sight and v == True:
                            # ok, found a visible floor tile neighbor. now let's make this wall
                            # visible as well
                            self.fov_map[y][x] = True
                            break  # other neighbors are irrelevant now

    def calculate_fov_points(self, points):
        """needs a points-list from Bresham's get_line method"""
        for point in points:
            x, y = point[0], point[1]
            # player tile always visible
            if x == self.x and y == self.y:
                self.fov_map[y][x] = True  # make this tile visible and move to next point
                continue
            # outside of dungeon level ?
            try:
                tile = Simulation.tiles[y][x]
            except:
                continue  # outside of dungeon error
            # outside of torch radius ?
            distance = ((self.x - x) ** 2 + (self.y - y) ** 2) ** 0.5
            if distance > self.torch_radius:
                continue
            self.fov_map[y][x] = True  # make this tile visible
            if tile.block_sight:
                break  # forget the rest
            # outcomment the next lines if boxes shall NOT break line of sight
            if len([b for b in Simulation.boxes if b.x == x and
                                                   b.y == y]) > 0:
                break  # forget the rest


class Viewer:
    width = 0
    height = 0
    grid_size = 20
    grid_color = (200, 200, 200)
    background_color = (255, 255, 255)
    min_boxes = 60
    max_boxes = 70
    font = None

    def __init__(self, width=800, height=600):

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
        # pygame.joystick.init()
        # self.joysticks = [
        #    pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())
        # ]
        # for j in self.joysticks:
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

        # self.prepare_sprites()
        self.setup()
        self.run()

    def setup(self):
        """call this to restart a game"""
        self.background = pygame.Surface((Viewer.width, Viewer.height))
        self.background.fill(Viewer.background_color)

        self.draw_grid()
        self.darkblock = pygame.Surface((Viewer.grid_size, Viewer.grid_size))
        self.darkblock.fill((0, 0, 0))  # fill black
        self.darkblock.set_alpha(128)
        self.darkblock.convert_alpha()
        self.lightblock = pygame.Surface((Viewer.grid_size, Viewer.grid_size))
        self.lightblock.fill((0, 0, 0))  # fill black
        self.lightblock.set_alpha(32)
        self.lightblock.convert_alpha()

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
                elif char == "a":
                    Simulation.tiles[y][x] = PressurePlate(key=1, x=x, y=y)
                elif char == "b":
                    Simulation.tiles[y][x] = PressurePlate(key=2, x=x, y=y)
                elif char == "c":
                    Simulation.tiles[y][x] = PressurePlate(key=3, x=x, y=y)
                elif char == "d":
                    Simulation.tiles[y][x] = PressurePlate(key=4, x=x, y=y)
                elif char == "A":
                    Simulation.tiles[y][x] = Door(key=1, x=x, y=y)
                elif char == "B":
                    Simulation.tiles[y][x] = Door(key=2, x=x, y=y)
                elif char == "C":
                    Simulation.tiles[y][x] = Door(key=3, x=x, y=y)
                elif char == "D":
                    Simulation.tiles[y][x] = Door(key=4, x=x, y=y)

        # initialize Field of View for all agents
        # for agent in Simulation.agents.values():
        #    agent.fov = [[False for tile in line] for line in Simulation.tiles]

        for b in range(random.randint(Viewer.min_boxes, Viewer.max_boxes)):
            Box()
        self.draw_maze()

        for _ in range(Simulation.num_seekers):
            Agent(seeker=True)
        for _ in range(Simulation.num_hiders):
            Agent(seeker=False)


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
                    pygame.draw.rect(self.background, char.color,
                        (x * Viewer.grid_size, y * Viewer.grid_size, Viewer.grid_size, Viewer.grid_size))

    def run(self):
        """The mainloop"""
        running = True

        # --------------------------- main loop --------------------------
        while running:
            for a in Simulation.agents.values():
                if a.hp > 0:
                    a.random_action()
                    a.turns_alive += 1
            for b in Simulation.boxes:
                b.move()
            #---pressureplates---
            # --- generally, all doors are closed ---
            for door in Simulation.doors:
                door.closed = True
                # but, when one of it's connected pressure_plates is triggered (by box or agent), the door is open
                for pressure_plate in  [pp for pp in Simulation.pressureplates if pp.key == door.key]:
                    for item in list(Simulation.agents.values()) + Simulation.boxes:
                        if item.x == pressure_plate.x and item.y == pressure_plate.y:
                            door.closed = False
                            break
                    if not door.closed:
                        break
            # update field of view for each agent
            for a in Simulation.agents.values():
                if a.hp > 0:
                    a.make_fov_map()

            # update global fov map, make everything dark
            Simulation.fov_map = [[False for tile in line] for line in Simulation.tiles]
            # update indivdiual fov map for each agent, make global map light
            for agent in [a for a in Simulation.agents.values() if a.hp >0]:
                for y, line in enumerate(agent.fov_map):
                    for x, tile in enumerate(line):
                        if agent.fov_map[y][x]:
                            Simulation.fov_map[y][x] = True

            # ------- update viewer ---------

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
            turns_alive = [h.turns_alive for h in Simulation.agents.values() if not h.seeker]
            pygame.display.set_caption(f"FPS: {self.clock.get_fps():.2f} | Turns-Alive: {str(turns_alive)}")     #str(nesw))
            if not any([h.hp for h in Simulation.agents.values() if not h.seeker]):
                print("Gameover!")
                print(turns_alive)
                break
            self.screen.blit(self.background, (0, 0))

            # --------- update all sprites ----------------
            for agent in Simulation.agents.values():
                pygame.draw.rect(self.screen, agent.color, (
                agent.x * Viewer.grid_size, agent.y * Viewer.grid_size, Viewer.grid_size, Viewer.grid_size))
            for box in Simulation.boxes:
                pygame.draw.rect(self.screen, box.color, (
                box.x * Viewer.grid_size, box.y * Viewer.grid_size, Viewer.grid_size, Viewer.grid_size))
            for door in Simulation.doors:
                pygame.draw.rect(self.screen, door.color, (
                door.x * Viewer.grid_size, door.y * Viewer.grid_size, Viewer.grid_size, Viewer.grid_size))

            # ----------- half-transparent FOV overlay ------------------
            for y, line in enumerate(Simulation.tiles):
                for x, tile in enumerate(line):
                    if Simulation.fov_map[y][x]:
                        self.screen.blit(self.lightblock, (x * Viewer.grid_size, y * Viewer.grid_size))
                    else:
                        self.screen.blit(self.darkblock, (x * Viewer.grid_size, y * Viewer.grid_size))

            # self.allgroup.update(seconds)
            # print([door.closed for door in Simulation.doors])
            # print([(pp.x,pp.y) for pp in Simulation.pressureplates])
            # ---------- blit all sprites --------------
            # self.allgroup.draw(self.screen)
            pygame.display.flip()
            # -----------------------------------------------------
        pygame.mouse.set_visible(True)
        pygame.quit()
        # try:
        #    sys.exit()
        # finally:
        #    pygame.quit()


def get_line(start, end):
    """Bresenham's Line Algorithm
       Produces a list of tuples from start and end
       source: http://www.roguebasin.com/index.php?title=Bresenham%27s_Line_Algorithm#Python
       see also: https://en.wikipedia.org/wiki/Bresenham%27s_line_algorithm

       :param: start_point (x,y)
       :param: end_point (x,y)
       :returns: list_of_points
       #>>> points1 = get_line((0, 0), (3, 4))
       # >>> points2 = get_line((3, 4), (0, 0))
       #>>> assert(set(points1) == set(points2))
       #>>> print points1
       #[(0, 0), (1, 1), (1, 2), (2, 3), (3, 4)]
       #>>> print points2
       #[(3, 4), (2, 3), (1, 2), (1, 1), (0, 0)]
    """
    # Setup initial conditions
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1

    # Determine how steep the line is
    is_steep = abs(dy) > abs(dx)

    # Rotate line
    if is_steep:
        x1, y1 = y1, x1
        x2, y2 = y2, x2

    # Swap start and end points if necessary and store swap state
    swapped = False
    if x1 > x2:
        x1, x2 = x2, x1
        y1, y2 = y2, y1
        swapped = True

    # Recalculate differentials
    dx = x2 - x1
    dy = y2 - y1

    # Calculate error
    error = int(dx / 2.0)
    ystep = 1 if y1 < y2 else -1

    # Iterate over bounding box generating points between start and end
    y = y1
    points = []
    for x in range(x1, x2 + 1):
        coord = (y, x) if is_steep else (x, y)
        points.append(coord)
        error -= abs(dy)
        if error < 0:
            y += ystep
            error += dx

    # Reverse the list if the coordinates were swapped
    if swapped:
        points.reverse()
    return points


if __name__ == "__main__":
    viewer = Viewer()
    viewer.run()
