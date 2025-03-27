from dataclasses import dataclass
from enum import Enum

class TectonicCrustType(Enum):
  OCEANIC = 0
  CONTINENTAL = 1

@dataclass(frozen=True)
class TectonicBoundaryPoint(Enum):
  x: float
  y: float
  z: float

@dataclass(frozen=False)
class TectonicPoint:
  x: float
  y: float
  z: float

@dataclass(frozen=True)
class TectonicBoundary:
  points: list[TectonicBoundaryPoint]

@dataclass(frozen=False)
class TectonicPlate:
  points: list[TectonicPoint]
  boundaries: list[TectonicBoundary]

@dataclass(frozen=False)
class TectonicWorldData:
  points: list[TectonicPoint]
  plates: list[TectonicPlate]
  boundaries: list[TectonicBoundary]



# Outline:
#   We generate all the points, and assign a plate to them accordingly
#   We start by generating either plates or faults, and then generate the other based on the first
#   - Faults should be represented by TectonicBoundaryPoints, never changing.
#   - Plates are a list of TectonicPoints, which can change over time.
#   - The world is: a list of TectonicPoints, TectonicPlates which
#   The preferred method is faults first. Easier to do line segments that look realistic than it is to do plates, as we saw in our version1 tests.
#   - With the flexible points (not locked to a hard grid), that's also preferrable, as boundaries are constant.

#   Plates need to be assigned:
#   - a crust type (at random: oceanic, continental)
#   - a rotational velocity based on an euler pole
#   Boundaries need to be assigned:
#   - a type (emerging from plate movements: divergence, convergence, transform)

#   During iteration, we need to:
#   - move every plate of a point based on its velocity/euler pole
#   - for every oceanic plate:
#     - for every point moving underneath a continental plate:
#       push up the continental points above it (proportionally to how aligned they are with the oceanic point), reduce the thickness of the oceanic point (eventually disappearing)
#     - for every point moving against another oceanic plate:
#       the older one gets pushed down
#   - for every continental plate:
#     - for every point moving against another continental plate:
#       they merge, going up

#   I think we should set aside this entire concept.
#     It seems like it's a lot of work and complexity, and feels like the kind of system where we can easily overlook important factors and get a bad result.
#     So we may not even get very good results.
#     In fact, looking at the results of the researched references... the best they seem able to do is generate maps that are about as good as the ones we could do with our version1.


#   Important bits of information from the invaluable German Geological Society short lectures:
#     - Movement from divergent plates is referential... plates are moving in reference to something.
#       - How to get absolute movement? In reference to hot spots. Because hot spots are relatively fixed, so the movement of the hot spot relative to the plate tells us the plate's absolute movement in that area.
#       - 
#     - Absolute movement of a plate is not uniform across the entire plate.
#       This is related to the earth's rotation
#   Can observe videos of convection in lava lakes to visualize spreading zones!!
#     https://www.youtube.com/watch?v=K_nzvHeblu8 @ 11m

#   SO, new key concept, building on our version1, with new concepts learned:
#     Define rough "convection" and "subduction" zones, which are at 90º from each other, with each pair being polarly opposite.
#     Inside each of these zones, 

class TectonicPoint:
  x: float
  y: float
  z: float
  thickness: float
  age: float
  type: TectonicCrustType

  def __init__(self, x: float, y: float, z: float, thickness: float, age: float, type: TectonicCrustType):
    self.x = x
    self.y = y
    self.z = z
    self.thickness = thickness
    self.age = age
    self.type = type

class TectonicBoundary:
  points: list[TectonicBoundaryPoint]

  def __init__(self, points: list[TectonicBoundaryPoint]):
    self.points = points

class TectonicPlate:
  points: list[TectonicPoint]
  boundaries: list[TectonicBoundary]

  def __init__(self, points: list[TectonicPoint], boundaries: list[TectonicBoundary]):
    self.points = points
    self.boundaries = boundaries

# Core class which contains TectonicPoints, TectonicPlates, and TectonicBoundaries
class TectonicBase:
  pass

# Parent class for tectonic generation
# Should have a generate method which returns a TectonicBase object
class TectonicGenerator:
  pass

