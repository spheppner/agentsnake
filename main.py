"""
SimonSnake
author: Simon HEPPNER
email: simon@heppner.at
license: gpl, see http://www.gnu.org/licenses/gpl-3.0.de.html
github: https://www.github.com/spheppner
"""

import pygame

# import pygame.locals
import pygame.freetype  # not automatically loaded when importing pygame!
import random

# import os
# import sys


class VectorSprite(pygame.sprite.Sprite):
    """base class for sprites. this class inherits from pygames sprite class"""

    number = 0  # unique number for each sprite

    # numbers = {} # { number, Sprite }

    def __init__(self, **kwargs):
        self._default_parameters(**kwargs)
        self._overwrite_parameters()
        pygame.sprite.Sprite.__init__(
            self, self.groups
        )  # call parent class. NEVER FORGET !
        self.number = VectorSprite.number  # unique number for each sprite
        VectorSprite.number += 1
        # VectorSprite.numbers[self.number] = self
        # self.visible = False
        self.create_image()
        self.distance_traveled = 0  # in pixel
        # self.rect.center = (-300,-300) # avoid blinking image in topleft corner
        if self.angle != 0:
            self.set_angle(self.angle)

    def _overwrite_parameters(self):
        """change parameters before create_image is called"""
        pass

    def _default_parameters(self, **kwargs):
        """get unlimited named arguments and turn them into attributes
        default values for missing keywords"""

        for key, arg in kwargs.items():
            setattr(self, key, arg)
        if "layer" not in kwargs:
            self.layer = 0
        # else:
        #    self.layer = self.layer
        if "pos" not in kwargs:
            self.pos = pygame.math.Vector2(200, 200)
        if "move" not in kwargs:
            self.move = pygame.math.Vector2(0, 0)
        if "angle" not in kwargs:
            self.angle = 0  # facing right?
        if "radius" not in kwargs:
            self.radius = 5
        if "width" not in kwargs:
            self.width = self.radius * 2
        if "height" not in kwargs:
            self.height = self.radius * 2
        if "color" not in kwargs:
            # self.color = None
            self.color = (
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255),
            )
        if "hitpoints" not in kwargs:
            self.hitpoints = 100
        self.hitpointsfull = self.hitpoints  # makes a copy

        if "stop_on_edge" not in kwargs:
            self.stop_on_edge = False
        if "bounce_on_edge" not in kwargs:
            self.bounce_on_edge = False
        if "kill_on_edge" not in kwargs:
            self.kill_on_edge = False
        if "warp_on_edge" not in kwargs:
            self.warp_on_edge = False
        if "age" not in kwargs:
            self.age = 0  # age in seconds. A negative age means waiting time until sprite appears
        if "max_age" not in kwargs:
            self.max_age = None

        if "max_distance" not in kwargs:
            self.max_distance = None
        if "picture" not in kwargs:
            self.picture = None
        if "boss" not in kwargs:
            self.boss = None
        if "kill_with_boss" not in kwargs:
            self.kill_with_boss = False
        if "move_with_boss" not in kwargs:
            self.move_with_boss = False

    def kill(self):
        # check if this is a boss and kill all his underlings as well
        tokill = []
        for s in Viewer.allgroup:
            if "boss" in s.__dict__ and s.boss == self:
                tokill.append(s)
        for s in tokill:
            s.kill()
        # if self.number in self.numbers:
        #   del VectorSprite.numbers[self.number] # remove Sprite from numbers dict
        pygame.sprite.Sprite.kill(self)

    def create_image(self):
        if self.picture is not None:
            self.image = self.picture.copy()
        else:
            self.image = pygame.Surface((self.width, self.height))
            self.image.fill(self.color)
        self.image = self.image.convert_alpha()
        self.image0 = self.image.copy()
        self.rect = self.image.get_rect()
        self.rect.center = (round(self.pos[0], 0), round(self.pos[1], 0))
        self.width = self.rect.width
        self.height = self.rect.height

    def rotate(self, by_degree):
        """rotates a sprite and changes it's angle by by_degree"""
        self.angle += by_degree
        self.angle = self.angle % 360
        oldcenter = self.rect.center
        self.image = pygame.transform.rotate(self.image0, -self.angle)
        self.image.convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = oldcenter

    def set_angle(self, degree):
        """rotates a sprite and changes it's angle to degree"""
        self.angle = degree
        self.angle = self.angle % 360
        oldcenter = self.rect.center
        self.image = pygame.transform.rotate(self.image0, -self.angle)
        self.image.convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = oldcenter

    def update(self, seconds):
        """calculate movement, position and bouncing on edge"""
        self.age += seconds
        if self.age < 0:
            return
        # self.visible = True
        self.distance_traveled += self.move.length() * seconds
        # ----- kill because... ------
        if self.hitpoints <= 0:
            self.kill()
        if self.max_age is not None and self.age > self.max_age:
            self.kill()
        if self.max_distance is not None and self.distance_traveled > self.max_distance:
            self.kill()
        # ---- movement with/without boss ----
        if self.boss and self.move_with_boss:
            self.pos = self.boss.pos
            self.move = self.boss.move
        else:
            # move independent of boss
            self.pos += self.move * seconds
            self.wallcheck()
        # print("rect:", self.pos.x, self.pos.y)
        self.rect.center = (int(round(self.pos.x, 0)), int(round(self.pos.y, 0)))

    def wallcheck(self):
        # ---- bounce / kill on screen edge ----
        # ------- left edge ----
        if self.pos.x < 0:
            if self.stop_on_edge:
                self.pos.x = 0
            if self.kill_on_edge:
                self.kill()
            if self.bounce_on_edge:
                self.pos.x = 0
                self.move.x *= -1
            if self.warp_on_edge:
                self.pos.x = Viewer.width
        # -------- upper edge -----
        if self.pos.y < 0:
            if self.stop_on_edge:
                self.pos.y = 0
            if self.kill_on_edge:
                self.kill()
            if self.bounce_on_edge:
                self.pos.y = 0
                self.move.y *= -1
            if self.warp_on_edge:
                self.pos.y = 0
        # -------- right edge -----
        if self.pos.x > Viewer.width:
            if self.stop_on_edge:
                self.pos.x = Viewer.width
            if self.kill_on_edge:
                self.kill()
            if self.bounce_on_edge:
                self.pos.x = Viewer.width
                self.move.x *= -1
            if self.warp_on_edge:
                self.pos.x = 0
        # --------- lower edge ------------
        if self.pos.y > Viewer.height:
            if self.stop_on_edge:
                self.pos.y = Viewer.height
            if self.kill_on_edge:
                self.hitpoints = 0
                self.kill()
            if self.bounce_on_edge:
                self.pos.y = Viewer.height
                self.move.y *= -1
            if self.warp_on_edge:
                self.pos.y = 0


class Flytext(VectorSprite):
    def __init__(
        self,
        pos=pygame.math.Vector2(50, 50),
        move=pygame.math.Vector2(0, -50),
        text="hallo",
        color=(255, 0, 0),
        bgcolor=None,
        max_age=0.5,
        age=0,
        acceleration_factor=1.0,
        fontsize=48,
        textrotation=0,
        style=pygame.freetype.STYLE_STRONG,
        alpha_start=255,
        alpha_end=255,
        width_start=None,
        width_end=None,
        height_start=None,
        height_end=None,
        rotate_start=0,
        rotate_end=0,
        picture=None,
    ):
        """Create a flying VectorSprite with text or picture that disappears after a while

        :param pygame.math.Vector2 pos:     startposition in Pixel. To attach the text to another Sprite, use an existing Vector.
        :param pygame.math.Vector2 move:    movevector in Pixel per second
        :param text:                        the text to render. accept unicode chars. Will be overwritten when picture is given
        :param (int,int,int) color:         foregroundcolor for text
        :param (int,int,int) bgcolor:       backgroundcolor for text. If set to None, black is the transparent color
        :param float max_age:               lifetime of Flytext in seconds. Delete itself when age > max_age
        :param float age:                   start age in seconds. If negative, Flytext stay invisible until age >= 0
        :param float acceleration_factor:   1.0 for no acceleration. > 1 for acceleration of move Vector, < 1 for negative acceleration
        :param int fontsize:                fontsize for text
        :param float textrotation:          static textrotation in degree for rendering text.
        :param int style:                   effect for text rendering, see pygame.freetype constants
        :param int alpha_start:             alpha value for age =0. 255 is no transparency, 0 is full transparent
        :param int alpha_end:               alpha value for age = max_age.
        :param int width_start:             start value for dynamic zooming of width in pixel
        :param int width_end:               end value for dynamic zooming of width in pixel
        :param int height_start:            start value for dynamic zooming of height in pixel
        :param int height_end:              end value for dynamic zooming of height in pixel
        :param float rotate_start:          start angle for dynamic rotation of the whole Flytext Sprite
        :param float rotate_end:            end angle for dynamic rotation
        :param picture:                     a picture object. If not None, it overwrites any given text
        :return: None
        """

        self.recalc_each_frame = False
        self.text = text
        self.alpha_start = alpha_start
        self.alpha_end = alpha_end
        self.alpha_diff_per_second = (alpha_start - alpha_end) / max_age
        if alpha_end != alpha_start:
            self.recalc_each_frame = True
        self.style = style
        self.acceleration_factor = acceleration_factor
        self.fontsize = fontsize
        self.textrotation = textrotation
        self.color = color
        self.bgcolor = bgcolor
        self.width_start = width_start
        self.width_end = width_end
        self.height_start = height_start
        self.height_end = height_end
        self.picture = picture
        # print( "my picture is:", self.picture)
        if width_start is not None:
            self.width_diff_per_second = (width_end - width_start) / max_age
            self.recalc_each_frame = True
        else:
            self.width_diff_per_second = 0
        if height_start is not None:
            self.height_diff_per_second = (height_end - height_start) / max_age
            self.recalc_each_frame = True
        else:
            self.height_diff_per_second = 0
        self.rotate_start = rotate_start
        self.rotate_end = rotate_end
        if (rotate_start != 0 or rotate_end != 0) and rotate_start != rotate_end:
            self.rotate_diff_per_second = (rotate_end - rotate_start) / max_age
            self.recalc_each_frame = True
        else:
            self.rotate_diff_per_second = 0
        # self.visible = False
        VectorSprite.__init__(
            self,
            color=color,
            pos=pos,
            move=move,
            max_age=max_age,
            age=age,
            picture=picture,
        )
        self._layer = 7  # order of sprite layers (before / behind other sprites)
        # acceleration_factor  # if < 1, Text moves slower. if > 1, text moves faster.

    def create_image(self):
        if self.picture is not None:
            # print("picture", self)
            self.image = self.picture
        else:
            # print("no picture", self)
            myfont = Viewer.font
            # text, textrect = myfont.render(
            # fgcolor=self.color,
            # bgcolor=self.bgcolor,
            # get_rect(text, style=STYLE_DEFAULT, rotation=0, size=0) -> rect
            textrect = myfont.get_rect(
                text=self.text,
                size=self.fontsize,
                rotation=self.textrotation,
                style=self.style,
            )  # font 22
            self.image = pygame.Surface((textrect.width, textrect.height))
            # render_to(surf, dest, text, fgcolor=None, bgcolor=None, style=STYLE_DEFAULT, rotation=0, size=0) -> Rect
            textrect = myfont.render_to(
                surf=self.image,
                dest=(0, 0),
                text=self.text,
                fgcolor=self.color,
                bgcolor=self.bgcolor,
                style=self.style,
                rotation=self.textrotation,
                size=self.fontsize,
            )
            if self.bgcolor is None:
                self.image.set_colorkey((0, 0, 0))

            self.rect = textrect
            # picture ? overwrites text

        # transparent ?
        if self.alpha_start == self.alpha_end == 255:
            pass
        elif self.alpha_start == self.alpha_end:
            self.image.set_alpha(self.alpha_start)
            # print("fix alpha", self.alpha_start)
        else:
            self.image.set_alpha(
                self.alpha_start - self.age * self.alpha_diff_per_second
            )
            # print("alpha:", self.alpha_start - self.age * self.alpha_diff_per_second)
        self.image.convert_alpha()
        # save the rect center for zooming and rotating
        oldcenter = self.image.get_rect().center
        # dynamic zooming ?
        if self.width_start is not None or self.height_start is not None:
            if self.width_start is None:
                self.width_start = textrect.width
            if self.height_start is None:
                self.height_start = textrect.height
            w = self.width_start + self.age * self.width_diff_per_second
            h = self.height_start + self.age * self.height_diff_per_second
            self.image = pygame.transform.scale(self.image, (int(w), int(h)))
        # rotation?
        if self.rotate_start != 0 or self.rotate_end != 0:
            if self.rotate_diff_per_second == 0:
                self.image = pygame.transform.rotate(self.image, self.rotate_start)
            else:
                self.image = pygame.transform.rotate(
                    self.image,
                    self.rotate_start + self.age * self.rotate_diff_per_second,
                )
        # restore the old center after zooming and rotating
        self.rect = self.image.get_rect()
        self.rect.center = oldcenter
        self.rect.center = (int(round(self.pos.x, 0)), int(round(self.pos.y, 0)))

    def update(self, seconds):
        VectorSprite.update(self, seconds)
        if self.age < 0:
            return
        self.move *= self.acceleration_factor
        if self.recalc_each_frame:
            self.create_image()


class Bubble(VectorSprite):
    """a round fragment or bubble particle, fading out"""

    def _overwrite_parameters(self):
        self.speed = random.randint(10, 50)
        if self.max_age is None:
            self.max_age = 0.2 + random.random() * 0.5
        self.kill_on_edge = True
        self.kill_with_boss = False  # VERY IMPORTANT!!!
        if self.move == pygame.math.Vector2(0, 0):
            self.move = pygame.math.Vector2(1, 0)
            self.move *= self.speed
            a, b = 0, 360
            self.move.rotate_ip(random.randint(a, b))
        self.alpha_start = 255
        self.alpha_end = 0
        self.alpha_diff_per_second = (self.alpha_start - self.alpha_end) / self.max_age

    def create_image(self):
        self.radius = random.randint(3, 8)
        self.image = pygame.Surface((2 * self.radius, 2 * self.radius))
        r, g, b = self.color
        r += random.randint(-30, 30)
        g += random.randint(-30, 30)
        b += random.randint(-30, 30)
        r = between(r)  # 0<-->255
        g = between(g)
        b = between(b)
        self.color = (r, g, b)
        pygame.draw.circle(
            self.image, self.color, (self.radius, self.radius), self.radius
        )
        self.image.set_colorkey((0, 0, 0))
        self.image.set_alpha(self.alpha_start - self.age * self.alpha_diff_per_second)
        self.image.convert_alpha()
        self.rect = self.image.get_rect()
        # self.rect.center=(int(round(self.pos[0],0)), int(round(self.pos[1],0)))

    def update(self, seconds):
        # self.create_image()
        super().update(seconds)
        self.image.set_alpha(self.alpha_start - self.age * self.alpha_diff_per_second)
        self.image.convert_alpha()


class Food(VectorSprite):
    """Yellow Food rectange that the player snakes must eat to grow."""

    def create_image(self):
        self.image = pygame.Surface((10, 10))
        self.image.fill(self.color)
        self.rect = self.image.get_rect()
        self.rect.center = int(self.pos.x), int(self.pos.y)

    def teleport(self):
        self.pos = pygame.math.Vector2(
            random.randint(0, Viewer.width), random.randint(0, Viewer.height)
        )


class Snake(VectorSprite):
    """Snake Controlled by player. Snake head shall never not touch walls or snake body"""

    width = 10
    speed = 50

    def reset(self):
        for _ in range(140):
            Bubble(
                color=self.color,
                pos=pygame.math.Vector2(self.pos.x, self.pos.y),
                max_age=1.5,
            )
        self.parts = []
        self.old_pos = pygame.math.Vector2(self.start_pos.x, self.start_pos.y)
        self.pos = pygame.math.Vector2(self.start_pos.x, self.start_pos.y)
        self.move = pygame.math.Vector2(self.start_move.x, self.start_move.y)
        self.deaths += 1
        self.length = 5

    def _overwrite_parameters(self):
        self.parts = []
        self.old_pos = pygame.math.Vector2(self.pos.x, self.pos.y)
        self.length = 5

        self.start_pos = pygame.math.Vector2(self.pos.x, self.pos.y)
        self.start_move = pygame.math.Vector2(self.move.x, self.move.y)
        self.deaths = 0

    def create_image(self):
        self.image = pygame.Surface((self.width, self.width))
        self.image.fill((0, 200, 0))
        self.image.convert_alpha()
        self.rect = self.image.get_rect()
        self.image0 = self.image.copy()
        self.rect.center = int(self.pos.x), int(self.pos.y)

    def go_north(self):
        if self.move.y == 0:
            self.move = pygame.math.Vector2(0, -self.speed)
            return True
        return False

    def go_south(self):
        if self.move.y == 0:
            self.move = pygame.math.Vector2(0, self.speed)
            return True
        return False

    def go_west(self):
        if self.move.x == 0:
            self.move = pygame.math.Vector2(-self.speed, 0)
            return True
        return False

    def go_east(self):
        if self.move.x == 0:
            self.move = pygame.math.Vector2(self.speed, 0)
            return True
        return False

    def grow(self):
        self.parts.insert(0, pygame.math.Vector2(self.old_pos.x, self.old_pos.y))

    def update(self, seconds):
        # print("parts:", len(self.parts))
        self.old_pos = pygame.math.Vector2(self.pos.x, self.pos.y)
        super().update(seconds)
        if len(self.parts) > 0:
            self.parts.insert(0, self.old_pos)  # insert at beginning
            del self.parts[-1]  # remove last
        if len(self.parts) < self.length:
            self.grow()
        # reset on wall
        if self.pos.x >= Viewer.width or self.pos.x <= 0:
            self.reset()
        if self.pos.y >= Viewer.height or self.pos.y <= 0:
            self.reset()


class Viewer:
    width = 0
    height = 0
    font = None

    # playergroup = None # pygame sprite Group only for players

    def __init__(
        self,
        width=800,
        height=600,
    ):

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
        pygame.joystick.init()
        self.joysticks = [
            pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())
        ]
        for j in self.joysticks:
            j.init()
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

        self.prepare_sprites()
        self.setup()
        self.run()

    def setup(self):
        """call this to restart a game"""
        self.background = pygame.Surface((Viewer.width, Viewer.height))
        self.background.fill((255, 255, 255))
        self.player1 = Snake(
            pos=pygame.math.Vector2(100, 100),
            speed=Snake.speed,
            color=(255, 0, 0),
            move=pygame.math.Vector2(Snake.speed, 0),
        )
        self.player2 = Snake(
            pos=pygame.math.Vector2(300, 200),
            speed=Snake.speed,
            color=(128, 255, 0),
            move=pygame.math.Vector2(-Snake.speed, 0),
        )
        self.food1 = Food(pos=pygame.math.Vector2(400, 50), color=(255, 255, 0))

    def prepare_sprites(self):
        """painting on the surface and create sprites"""
        Viewer.allgroup = pygame.sprite.LayeredUpdates()  # for drawing with layers
        Viewer.snakegroup = pygame.sprite.Group()
        Viewer.foodgroup = pygame.sprite.Group()  # GroupSingle
        # assign classes to groups
        VectorSprite.groups = self.allgroup
        Snake.groups = self.allgroup, self.snakegroup
        Food.groups = self.allgroup, self.foodgroup

        # Bubble.groups = self.allgroup, self.fxgroup  # special effects
        # Flytext.groups = self.allgroup, self.flytextgroup, self.flygroup

    def run(self):
        """The mainloop"""
        running = True

        # pygame.mouse.set_visible(False)
        oldleft, oldmiddle, oldright = False, False, False

        # for b in range(-50,50, 5):
        #    Bubble(pos=pygame.math.Vector2(200, 200), age=b/100, max_age=3)
        Flytext(
            pos=pygame.math.Vector2(200, 300),
            move=pygame.math.Vector2(0, -3),
            text="Snake Game",
            max_age=5,
            fontsize=64,
            alpha_start=255,
            alpha_end=15,
            width_start=600,
            width_end=100,
            height_start=300,
            height_end=100,
            rotate_start=-30,
            rotate_end=30,
            acceleration_factor=1.015,
        )
        Flytext(
            pos=pygame.math.Vector2(Viewer.width // 2, Viewer.height),
            move=pygame.math.Vector2(0, -10),
            text="move with WASD / Cursor Keys",
            color=(5, 5, 5),
            max_age=10,
            fontsize=25,
        )

        # --------------------------- main loop --------------------------
        while running:
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
            # news stands for North, East, South, West
            # set all directions to False to avoid unclear commands (like north and south keys both pressed)
            # ---- player1 steering ----
            nesw1 = [False, False, False, False]
            if pressed_keys[pygame.K_w]:
                nesw1[0] = True
            if pressed_keys[pygame.K_d]:
                nesw1[1] = True
            if pressed_keys[pygame.K_s]:
                nesw1[2] = True
            if pressed_keys[pygame.K_a]:
                nesw1[3] = True
            # ---- player 2 steering ---
            nesw2 = [False, False, False, False]
            if pressed_keys[pygame.K_UP]:
                nesw2[0] = True
            if pressed_keys[pygame.K_RIGHT]:
                nesw2[1] = True
            if pressed_keys[pygame.K_DOWN]:
                nesw2[2] = True
            if pressed_keys[pygame.K_LEFT]:
                nesw2[3] = True
                # self.player1.go_west() # move = pygame.math.Vector2(-self.player1.speed, 0)
            # ---- give direction command. only undisputed commands are accepted ----
            if nesw1 == [True, False, False, False]:
                self.player1.go_north()
            if nesw1 == [False, True, False, False]:
                self.player1.go_east()
            if nesw1 == [False, False, True, False]:
                self.player1.go_south()
            if nesw1 == [False, False, False, True]:
                self.player1.go_west()
            # -- player 2---
            if nesw2 == [True, False, False, False]:
                self.player2.go_north()
            if nesw2 == [False, True, False, False]:
                self.player2.go_east()
            if nesw2 == [False, False, True, False]:
                self.player2.go_south()
            if nesw2 == [False, False, False, True]:
                self.player2.go_west()
            # ------ mouse handler ------
            left, middle, right = pygame.mouse.get_pressed()

            oldleft, oldmiddle, oldright = left, middle, right
            # ----------- collision detection ------------
            # ----- food with snake ------
            for f in self.foodgroup:
                crashgroup = pygame.sprite.spritecollide(
                    f, self.snakegroup, False, pygame.sprite.collide_rect
                )
                # print("Crashgroup", crashgroup, len(crashgroup))
                for snake in crashgroup:
                    snake.length += 10
                if len(crashgroup) > 0:
                    for _ in range(15):
                        Bubble(color=f.color, pos=pygame.math.Vector2(f.pos.x, f.pos.y))
                    f.teleport()
            # ---- snake head with other snake head ------
            for s in self.snakegroup:
                crashgroup = pygame.sprite.spritecollide(
                    s, self.snakegroup, False, pygame.sprite.collide_rect
                )
                # each sprite has a unique number. avoid self-collision
                for other_snake in crashgroup:
                    if s.number != other_snake.number:
                        s.reset()
                        other_snake.reset()
            # ----- snake head with (own or other) tail ------
            for s in self.snakegroup:
                for other in self.snakegroup:
                    for part in other.parts:
                        futurepos = s.pos + s.move.normalize() * s.width
                        distance = futurepos - part
                        if distance.length() < Snake.width:
                            s.reset()
            # ---------- clear all --------------
            # pygame.display.set_caption(f"player 1: {self.player1.deaths}   vs. player 2: {self.player2.deaths}")     #str(nesw))
            self.screen.blit(self.background, (0, 0))
            # write score
            rect1 = Viewer.font.render_to(
                surf=self.screen,
                dest=(100, 30),
                text=str(self.player1.deaths),
                fgcolor=(64, 64, 64),
                size=64,
            )
            rect2 = Viewer.font.render_to(
                surf=self.screen,
                dest=(Viewer.width - 100, 30),
                text=str(self.player2.deaths),
                fgcolor=(64, 64, 64),
                size=64,
            )
            # --------- update all sprites ----------------
            self.allgroup.update(seconds)

            # blit tail for each snake
            for s in self.snakegroup:
                # part is a list of vec2d pos vectors
                for part in s.parts:
                    pygame.draw.rect(
                        self.screen,
                        s.color,
                        (
                            part.x - s.width // 2,
                            part.y - s.width // 2,
                            s.width,
                            s.width,
                        ),
                    )
            # ---------- blit all sprites --------------
            self.allgroup.draw(self.screen)
            pygame.display.flip()
            # -----------------------------------------------------
        pygame.mouse.set_visible(True)
        pygame.quit()
        # try:
        #    sys.exit()
        # finally:
        #    pygame.quit()


## -------------------- functions --------------------------------


def between(value, lower_limit=0, upper_limit=255):
    """makes sure a (color) value stays between a lower and a upper limit ( 0 and 255 )
    :param float value: the value that should stay between min and max
    :param float lower_limit:  the minimum value (lower limit)
    :param float upper_limit:  the maximum value (upper limit)
    :return: new_value"""
    return (
        lower_limit
        if value < lower_limit
        else upper_limit
        if value > upper_limit
        else value
    )


if __name__ == "__main__":
    # g = Game()
    Viewer(
        width=400,
        height=400,
    )
