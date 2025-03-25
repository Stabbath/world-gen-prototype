from enum import Enum

class WorldPoint:
    x: int
    y: int

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

class WorldShape(Enum):
    FLAT = 0,
    CYLLINDRICAL_HORIZONTAL = 1,
    CYLLINDRICAL_VERTICAL = 2
    SPHERICAL = 3

class TileShape(Enum):
    SQUARE = 0,
    HEXAGONAL_FLAT = 1,
    HEXAGONAL_VERT = 2

class WorldGridTopology:
    world_shape: WorldShape
    tile_shape: TileShape

    def __init__(self, world_shape: WorldShape, tile_shape: TileShape):
        self.world_shape = world_shape
        self.tile_shape = tile_shape

    def create_neighbors_function(self):
        if self.tile_shape == TileShape.SQUARE:
            return self._neighbors_flat_square
        raise Exception("Unsupported topology")

    # in a flat square grid, the neighbors are the 8 points around the point; but we must take into account the edges of the world
    def _neighbors_flat_square(world: World, point: WorldPoint):
        x = point.x
        y = point.y
        neighbors = []
        for i in range(-1, 2):
            for j in range(-1, 2):
                if i == 0 and j == 0:
                    continue
                if x + i >= 0 and x + i < world.width and y + j >= 0 and y + j < world.height:
                    neighbors.append(world.point_at(x + i, y + j))
        return neighbors

class WorldInitParams:
    width: int
    height: int
    grid_topology: WorldGridTopology

    def __init__(self, width: int, height: int, grid_topology: WorldGridTopology):
        self.width = width
        self.height = height
        self.grid_topology = grid_topology

class World:
    def __init__(self, init_params: WorldInitParams):
        self.width = init_params.width
        self.height = init_params.height
        self.tiles = [[WorldPoint(x, y) for x in range(init_params.width)] for y in range(init_params.height)]

        # Create function for neighbors
        self.neighbors_of = init_params.grid_topology.create_neighbors_function()

    def neighbors_of(self, point: WorldPoint):
        raise Exception("Not implemented")

    def point_at(self, x: int, y: int) -> WorldPoint:
        return self.tiles[y][x]


class WorldGenerationConfig:
    world_init: WorldInitParams = WorldInitParams(100, 100)

    climate_iterations: int = 100
        

# The parent class for all tectonic strategies
class TectonicStrategy:
    pass
    # options:
    # - version1 generators
    # - fractal partitions/noise? Perlin noise or diamond-square
    # - define a random velocity on a mesh, cluster cells by similar vectors, and then iterate to refine plates
    # - one or more of the methods
    # - postprocessing: merging plates, different rules for doing so
    # - generate a "heat" value for N random points (for N plates), interpolate heat values to the rest of the map, and then use heat to determine boundaries
    #   - can interpolate for example by having each point have a "heat-effect" on every tile in the world, decreasing with distance
    #     and then averaging the "heat-effect" of all source points for each other point
    #   - once we have the full heat map, we find gradient inversions and use them as boundaries


class WorldGenerator:
    gen_config: WorldGenerationConfig
    world: World
    tectonic_strategy: TectonicStrategy

    def __init__(self, gen_config: WorldGenerationConfig):
        self.gen_config = gen_config
        self.world = World(gen_config.world_init)
    
    def generate(self):
        self.generate_tectonics()
        self.generate_height_map()
        self.generate_seas()
        self.generate_atmosphere()
        self.generate_base_climate()
        for i in range(self.gen_config.climate_iterations):
          self.iterate_climate()


    def generate_tectonics(self):
        pass

    def generate_height_map(self):
        pass
    
    def generate_seas(self):
        pass
    
    def generate_atmosphere(self):
        pass

    def generate_base_climate(self):
        pass
    
    def iterate_climate(self):
        pass
