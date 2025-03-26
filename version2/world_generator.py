from enum import Enum

# TODO - RESEARCH:
# - https://github.com/Sean-Hastings/Terrain-Generation
# - https://github.com/FreezeDriedMangos/realistic-planet-generation-and-simulation
# - https://github.com/seanth/PyTectonics
# - https://github.com/marchamann/Tectonic-Map-Generator/blob/master/technical.md
# - ChatGPT's deep research output on this topic

class WorldSurfacePoint:
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
    def _neighbors_flat_square(world: World, point: WorldSurfacePoint):
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
        self.tiles = [[WorldSurfacePoint(x, y) for x in range(init_params.width)] for y in range(init_params.height)]

        # Create function for neighbors
        self.neighbors_of = init_params.grid_topology.create_neighbors_function()

    def neighbors_of(self, point: WorldSurfacePoint):
        raise Exception("Not implemented")

    def point_at(self, x: int, y: int) -> WorldSurfacePoint:
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
    #
    # RESEARCH:
    # https://github.com/JavierCenteno/TectonicTiles.js - this guy assigns "start" and "end" tiles for each plate to define their movement, and then applies a crease function to every tile which takes into account all of the plate movements, I guess based on its distance to the start and end tiles. Or something like that.
    # https://github.com/jordanstudioroot/RootGen-UnityCSharp - this guy doesnt have real tectonics, just regions which are randomly assigned elevations
    # https://github.com/davidson16807/tectonics.js - bullshit name, actually nothing even remotely resembling tectonics
    #                                                 CORRECTION: check climate research to see how they infer tectonics from the height map and other data
    # https://github.com/Mindwerks/plate-tectonics - looks really good.
    #   - has a "lithosphere" object
    #     - stores params like num of iterations, "folding ratio", sea level, dimensions, erosion period, ...
    #     - also stores the "plates" objects and transforms them, handles their collisions, etc
    #   - lithosphere.createPlates or something
    #     - selects random points as plate centers
    #     - creates a plateArea which includes the plate's borders, top bottom left and right boundaries, and dimensions
    #     - grows plates out from their center
    #   - lithosphere tracks the height of each point and which plate each point belongs to
    #   - lithosphere resolves collisions by adjusting the crust. Handles both continental and oceanic collisions
    #     - simulates geological folding
    #       - takes the folding ratio to see how much of the top crust will be folded on top, adds that much elevation. I guess based on crust thickness too
    #     - simulates subduction of oceanic crust under continental
    #       - reduces crust thickness at that point (they just reference the height map, but I guess that's the concept)
    #     - generates new crust at divergent boundaries
    #   - periodically applies erosion every N iterations, smoothing
    #   - cleans up plates if they become empty

class ElevationStrategy:
    pass
    # options:
    # - version1 generators
    # - should probably be based on tectonics to some extent
    # - keep in mind that planets have a normal distribution of elevation (although it may be multimodal, e.g. the Earth has a bimodal distribution)
    #   - we could use such distributions to determine elevation for N randomly-selected points (probably with a large N), and then interpolate the rest of the map
    #     plus add random noise.
    #     - also, I still want to represent elevation itself as a statistical distribution, so we would need to determine not just the average elevation but also the standard deviation
    #
    # RESEARCH:
    # https://github.com/jordanstudioroot/RootGen-UnityCSharp - this guy does it randomly based on regions, with no real tectonics
    #   - He also includes erosion right from the get-go; he considers that any tile that is significantly larger than its neighbors is eligible for erosion. Just flat erosion too. Kinda dumb.
    # https://github.com/davidson16807/tectonics.js - a few different steps, with no tectonics
    #   - init - seems kinda dumb
    #     - repeatedly divides the world in random halves and adds elevation to one half
    #   - terrain gen on a sphere
    #     - selects random 3d points on the sphere as continent centers
    #     - *does the same thing as in the init again*
    #        - uses a smoothed function so there's not a hard drop-off between the two halves
    #     - tracks a "height rank" for each point based on its relative position compared to other points
    #     - normalizes height ranks to ensure they fit within a specific range
    #   - uses a hypsographic curve to map the initial elevation data to the final elevation map!! specifically, the earth's
    #     - this is one of the options for what I've talked about before with using the statistical distribution of elevations
    # https://github.com/ftomassetti/procedurality-lands - mostly just random noise, but one of the many random noise sides of it intends to simulate an ice age...
    #     - nothing of value to take from it, but the word 'ice age' is interesting, in that we should maybe look into actually simulating ice ages (although that would ideally already be a natural part of an ideal world simulation)

class ClimateStrategy:
    pass
    # options:
    # - version1 generators
    #
    # RESEARCH:
    # https://github.com/jordanstudioroot/RootGen-UnityCSharp - this guy actually does something a bit more interesting-looking here, for once
    #                                                           SCRATCH THAT, after reviewing all of it, it's just a dumbed-down version of my method
    #   - Clouds - very similar to my method: 
    #     - if a tile is water, then it adds a fixed amount of clouds above itself, based on an evaporation factor
    #       - otherwise, it's based on the moisture of the tile (and an evaporation factor)
    #     - clouds turn into precipitation based on a precipitation factor
    #     - there's a maximum number of clouds which decreases with elevation
    #     - clouds are dispersed to neighbors based on wind direction and strength
    #   - Moisture - also pretty similar:
    #     - precipitation adds to moisture
    #     - moisture flows to neighboring tiles based on elevation difference (with a factor for "runoff" and one for "seepage")
    #   - Temperature - also similar:
    #     - temperature is based on latitude and elevation
    #     - then he adds some jitter to induce random variations
    #   - Wind - very dumb:
    #     - wind strength is a constant parameter
    #     - wind direction is based on latitude
    #   - Biome - very basic
    #     - he just uses temperature and moisture to determine biomes from a list of options, breaking them down into 4 categories for both temperature and biome, and mapping those 16 combinations down to 4 actual biomes (snow, mud, grassland, desert)
    # https://github.com/davidson16807/tectonics.js - looks pretty elaborate, although with some variables having overly simplified initializations (so temperature bands and moisture are too latitude-dependent, deserts and jungles and stuff are all just latitudinal bands)
    #                                                 like, for real, there's some real sciencey shit in there and then the outcome is worse than my bullshit heuristic method. lol.
    #                       NOTE also: this is where they actually handle tectonics, infering it from the height map I guess
    #   - they generate 'crust' from the elevation map, giving it properties like sedimentary etc
    #     - they track oceanic crust age (also thickness, density)
    #       - younger crust is hotter and more buoyant; older is cooler and denser
    #         - younger crust is also found near mid-ocenan ridges where it's being formed; older crust in subduction zones where it's being recycled into the mantle
    #         - this temperature difference can influence ocean currents, heat flow, and other thermal dynamics in the region
    #       - once crust reaches a certain age it's marked for subduction
    #     - they calculate "velocity lines" so that crust will be drawn towards subducting regions
    #       - the weighted average of velocity lines becomes the velocity for the whole plate
    #         - so then the plates move towards the subduction zones, colliding with each other. Colliding crust tiles are deleted from the model.
    #         - as the plates move, they leave behind holes which are filled in with new crust
    #     - somewhere in there, they perform "image segmentation" to group crust tiles into plates, based on their velocity being similar?
    #   - incoming sunlight:
    #     - they perform atmospheric scattering of light
    #       - this involves calculating the column density ratio, which represent the density of air along a path from the viewer to a light source
    #     - they perform raymarching, to trace the path of light
    #       - for each point along the view ray, the algorithm sums up the column density ratio from that point to the light source
    #   - wind: same as me, coriolis and air pressure
    #   - ocean currents: they mention it somewhere, but nope no code
    #   - precipitation: dumb model, estimates based on latitude and little else
    #   - clouds: nope
    #   - vegetation: simplified, basically dependant on precipitation, but reference interesting concepts:
    #     - net primary productivity
    #     - leaf area indices
    #   - biomes: hyper simplified

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
