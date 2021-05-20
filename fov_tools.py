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


def make_fov_map(agent, sim_tiles):
    """makes field_of_view (fov) map for an agent
       the agent has self.x and self.y attribute
    """
    fov_map = []
    # self.checked = set() # clear the set of checked coordinates
    px, py, = agent.x, agent.y
    # set all tiles to False
    ##? [[False for tile in line] for line in sim_tiles]
    for line in sim_tiles:
        row = []
        for tile in line:
            row.append(False)
        fov_map.append(row)
    # set player's tile to visible
    fov_map[py][px] = True
    # get coordinates form player to point at end of torchradius / torchsquare
    endpoints = set()
    for y in range(py - agent.torch_radius, py + agent.torch_radius + 1):
        if y == py - agent.torch_radius or y == py + agent.torch_radius:
            for x in range(px - agent.torch_radius, px + agent.torch_radius + 1):
                endpoints.add((x, y))
        else:
            endpoints.add((px - agent.torch_radius, y))
            endpoints.add((px + agent.torch_radius, y))
    for coordinate in endpoints:
        # a line of points from the player position to the outer edge of the torchsquare
        points = get_line((px, py), (coordinate[0], coordinate[1]))
        fov_map = calculate_fov_points(points, agent, sim_tiles, fov_map)
    # print(Game.fov_map)
    # ---------- the fov map is now ready to use, but has some ugly artifacts ------------
    # ---------- start post-processing fov map to clean up the artifacts ---
    # -- basic idea: divide the torch-square into 4 equal sub-squares.
    # -- look of a invisible wall is behind (from the player perspective) a visible
    # -- ground floor. if yes, make this wall visible as well.
    # -- see https://sites.google.com/site/jicenospam/visibilitydetermination
    # ------ north-west of player
    for xstart, ystart, xstep, ystep, neighbors in [
        (-agent.torch_radius, -agent.torch_radius, 1, 1, [(0, 1), (1, 0), (1, 1)]),
        (-agent.torch_radius, agent.torch_radius, 1, -1, [(0, -1), (1, 0), (1, -1)]),
        (agent.torch_radius, -agent.torch_radius, -1, 1, [(0, -1), (-1, 0), (-1, -1)]),
        (agent.torch_radius, agent.torch_radius, -1, -1, [(0, 1), (-1, 0), (-1, 1)])]:

        for x in range(px + xstart, px, xstep):
            for y in range(py + ystart, py, ystep):
                # not even in fov?
                try:
                    visible = fov_map[y][x]
                except:
                    continue
                if visible:
                    continue  # next, i search invisible tiles!
                # oh, we found an invisble tile! now let's check:
                # is it a wall?
                # if Game.dungeon[pz][y][x].char != "#":
                if not sim_tiles[y][x].block_sight:
                    continue  # next, i search walls!
                # --ok, found an invisible wall.
                # check south-east neighbors

                for dx, dy in neighbors:
                    # does neigbor even exist?
                    try:
                        v = fov_map[y + dy][x + dx]
                        t = sim_tiles[y + dy][x + dx]
                    except IndexError:
                        continue
                    # is neighbor a tile AND visible?
                    # if isinstance(t, Floor) and v == True:
                    if v and not t.block_sight:
                        # ok, found a visible floor tile neighbor. now let's make this wall
                        # visible as well
                        fov_map[y][x] = True
                        break  # other neighbors are irrelevant now
    return fov_map


def calculate_fov_points(pointlist, agent, sim_tiles, fov_map):
    """needs a points-list from Bresham's get_line method
    agent must have self.fov_map
    """

    for point in pointlist:
        x, y = point[0], point[1]
        # player tile always visible
        if x == agent.x and y == agent.y:
            fov_map[y][x] = True  # make this tile visible and move to next point
            continue
        # outside of dungeon level ?
        try:
            tile = sim_tiles[agent.y][agent.x]
        except IndexError:
            continue  # outside of dungeon error
        # outside of torch radius ?
        distance = ((agent.x - x) ** 2 + (agent.y - y) ** 2) ** 0.5
        if distance > agent.torch_radius:
            continue
        try:
            fov_map[y][x] = True  # make this tile visible
        except IndexError:
            pass
        if tile.block_sight:
            break  # forget the rest

    return fov_map


if __name__ == "__main__":
    print("this module is supposed to be imported from the main program")
    # points1 = get_line((0, 0), (3, 4))
    # print(points1)

