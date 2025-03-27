# Educational Resources:
# - https://www.youtube.com/watch?v=E_27itP8gZ4 (German Geological Society)
# - https://laulima.hawaii.edu/access/content/group/dbd544e4-dcdd-4631-b8ad-3304985e1be2/book/toc/toc.htm (Hawaii University)

# Personal Notes:
# - On Boundaries:
#   Divergence:
#     plates are pushed away from each other (equally); as new crust is created
#     e.g. Mid-Atlantic Ridge
#   Oceanic-Continental Convergence
#     oceanic plate is subducted under the continental plate, creating a trench along the boundary and pushing up the continental plate as it moves underneath it
#     e.g. West coast of the Americas
#   Continental-Continental Convergence
#     as both plates are light, they both resist being pushed downward, leading to massive deformation and uplift
#     e.g. Everest
#   Oceanic-Oceanic Convergence
#     the older of the two plates, being denser, will subduct. Causes a trench as well
#     e.g. Mariana Trench
#   Transform Plate Boundary:
#     plates slide past each other horizontally
#     e.g. San Andreas Fault

# - On Plate Movement:
#   Current prevailing theory is that of mantle convection
#   - basically 2 massive convection cells, splitting the world into 2 hemispheres (no relation with rotational axis or anything like that)
#   - at the center of each cell is a rising plume of hot mantle material, which pushes the plates apart
#      plus some random hot spots nearby, which also create crust, always remaining at the same place relative to the earth's center, so that with plate movement they overtime create a chain of islands
#        realistically, the hot spots can also move (very little, comparatively), or disappear, but we should simplify them as being permanent, or lasting X steps, and never moving 
#   - at the border between cells, the plates are pushed together in subduction zones
#   When a plate is pushed up, it starts with significant variation in elevation (mountains, valleys, etc), but over time it erodes and becomes smoother and more flat

# - On Crust Types:
#   Continental:
#   - thicker, less dense, older, because it's so light it doesn't really go down, just gets moved around, pushed into other continental crust, and eroded
#       - should read more into https://en.wikipedia.org/wiki/Shield_(geology)
#   - new crust does occasionally form, in areas called "terranes"
#       my understanding of this so far is that it's basically crust that was formed through hot spots which gets pushed around and eventually pushed onto a continent, becoming thereafter a part of it
#   Oceanic:
#   - just moves around, subducted, recycled. Doesn't get to age much

# - On Erosion:
#   Fluvial erosion is the main thing, of course, and there's something important I hadn't thought about:
#   - the sediment that gets eroded gets deposited somewhere else, which flattens out the landscape and builds ew low-lying land along the coast
#       - this flattening is what causes floodplains
#       - also deltas
#   Wave erosion is also important: tears down cliffs and builds beaches
#   Wind ... also exists. Wind erosion is probably not a priority
#   Glaciers. Ice ages. Etc. Not a priority either, but more important than wind

# OPEN QUESTIONS:
# - How to select realistic hot spots? Looking at the Earth, it's hard to say. There's a lot in the middle of the pacific plate, a lot along the mid-atlantic ridge, random ones in the middle of Africa...
#     they seem a bit more common at or close to certain faults, but it's not super clear
# - Plate collisions leading to faults - horsts and grabens / basin and range; rift valleys; ?
# - Earthquakes and eruptions happen at plate boundaries (and hot spots), but why is e.g. pacific ring of fire more active than the mid-atlantic ridge?
#     should probably simulate eruptions when handling crust formation in hot spots
# - One day may need to take into account coral reefs as well


# The parent class for all tectonic strategies
import numpy as np


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
    # https://github.com/seanth/PyTectonics - pretty elaborate. Partly based on PlaTec and some other projects
    #   - uses a spherical world
    #   - creates points on the spherical surface, equidistant to each other
    #     - but they're not locked down; the points themselves are moved around
    #   - randomly creates plates by selecting random center points and growing it outwards
    #   - plates are randomly assigned a velocity and an "euler pole" (which is an axis around which the plate rotates)
    #   - from that point, iterates in steps moving the points around
    #     - when 2 points overlap, subduction happens
    #       - they don't delete the subducted plate, but hide it. They will use it for mountain building later
    #       - after subduction, the subducted point keeps moving for a predefined distance until it is considered to be detached from the lithoshere
    #         - THEN it's removed from memory
    #         - this predefined distance effectively determines the width of the world's mountain ranges
    #           - the author comments that they wanted to set this distance mechanistically, but their research led them to believe they required way too many parameters and complexity
    #     - when points move away from each other, creating a divergent boundary, new points are created which represent oceanic crust
    #        - each plate stores the original positions of its points, so that it can create new points at the divergent boundary at tidy-looking locations
    #     - futher steps which require code analysis, as they don't explain it in their wiki:
    #        Other submodels play a lesser role in controlling elevation. Isostasy is perhaps the most important, since its responsible for most mountains. Each point tracks thickness and density, and when points overlap their thicknesses/densities are considered together to determine elevation. There is also a submodel controlling crust added to volcanic arcs. Basically, when subducted points are destroyed, a certain amount of crust is added to the points that overlap them. 

# Generate a sphere of points representing points on the crust; then move them around following tectonic logic
# - radius: float, the radius of the planet, in arbitrary units
# - point_density: float, the number of points per surface unit of the planet's surface (in the same unit as radius, but squared)
class CrustPoints(TectonicStrategy):
  def __init__(self, radius: float, point_density: float, iterations: int):
    self.radius = radius
    self.point_density = point_density
    self.points = self.generate_points()
    self.init_tectonics()
    for i in range(iterations):
      self.iterate()

  def init_tectonics(self):
    # we need to define the plates, their velocities, and their boundaries
    # I guess we should focus on generating boundaries first,
    pass

  def iterate(self):
    pass

  # Generate a fibonacci sphere, with a number of points proportional to the surface area of the planet
  def generate_points(self):
    num_points = int(4 * np.pi * self.radius**2 * self.point_density)
    points = np.zeros((num_points, 3))
    offset = 2.0 / num_points
    increment = np.pi * (3.0 - np.sqrt(5.0))
    for i in range(num_points):
      y = ((i * offset) - 1) + (offset / 2)
      r = np.sqrt(1 - y * y)
      phi = i * increment
      x = np.cos(phi) * r
      z = np.sin(phi) * r
      points[i] = np.array([x, y, z]) * self.radius
    return points
