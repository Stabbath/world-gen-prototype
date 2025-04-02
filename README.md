# The Basics
The surface of the world is made up of contiguous rigid plates that move against each other - the lithosphere -, pushed by convection currents in the underlying fluid asthenosphere, as well as slab-pull (if part of the plate is being pushed down, the rest gets dragged along) and ridge-push (wherever 2 plates move apart, there is material coming to the top and cooling down and becoming part of the slabs, and it pushes the rest of the slab away) forces.

We want to model this in a hyper-realistic but comfortably-abstracted way. Our goal isn't to create a complex soft-body simulation of a planet's entire mass. It's to get pretty realistic planets with realistic geological information.

**Abstraction 1:** We ignore everything below the lithosphere. We can just simulate the effects the asthenosphere has on it abstractly, and we don't even need to think about anything lower than that.

At some point I considered modeling the crust as discretized spheres and writing a custom soft-body physics engine to simulate it fully. Then I remembered I'm not actually a geophysicist and I'm not getting paid to do this.

# Modeling 1: Plate and Boudary Geometries
There are 2 options: 
1. You define plates and then the boundaries are the edges of those plates; or
2. You define boundaries, and then the plates are the space between those boundaries.

- **Option 1** is normally done through Voronoi partition or some flood-fill or expansion algorithm (with a discretized grid or set of points or shapes representing small sections of the crust).
- **Option 2...** isn't done? I don't remember finding anything in my research where they generated boundaries first. Which I think is a big reason why their continents so often look blocky. 

In our first prototype, we attempted something along the lines of 1, with an over-generation of plates which get merged down to the goal number, which was already an improvement.

But in that same prototype we also experimented with boundary-first generation, and it yielded even better results at a slightly lower computational cost.

**Decision 1:** We generate boundaries first, using some random-walk or similar method, and calculate plates from the boundaries.

**Refinements:** 
- We must define each boundary as being between 2 and only 2 plates. Wherever there is a triple junction, we will see it as 3 boundaries meeting, and not as 1 boundary meeting another which ends at the junction.
	- This has basically no cost, and makes a lot of possible calculations later a lot easier.
- We should perhaps take care that no junctions above degree 3 exist, as only 4 is possible and those collapse very quickly down into a 3.

# Modeling 2: Tectonic Motion

## 2.1: Isolated Motion
The simplest and most accurate method I managed to find after a lot of research and reflection: we ignore the specific forces at play, and instead focus on the movement itself. 

**Method:**
1. Each plate has what's called an Euler pole (see Euler's rotation theorem), and a rotational velocity around that pole.
2. We assign to each boundary a "boundary type", based on the movement of the 2 plates it borders:
	- If the 2 plates move away from each other, it is divergent.
	-  If the 2 plates move in the same direction, then if the plate moving away from the boundary is faster, it is divergent; else it is convergent.
		-  If they move at the *exact* same speed, we should maybe merge the 2 plates? I'm not sure how that would work; I guess the *exact* same speed is probably something that never actually really happens.
	- If the 2 plates move towards each other, the boundary is convergent.

### Addendum:
**TODO:** note that boundaries themselves *also* move. I can't remember what solution I had proposed for this, but I think either we:
- Need to calculate a velocity for the fault based on its adjoining plates (maybe complicated, maybe inaccurate?); or
- We see, before filling in the crust for the divergent area, where the edge of the 2 plates is, and recenter our divergent boundary to be equidistant to both (a little complicated, but accurate); or
- We attach the boundary to one of the plates (which one?) and so it always moves with it (relatively simple, but likely inaccurate? although I think I read somewhere that this IS actually what happens, but I'm not sure.).

## 2.2: Convergence and Divergence 
As the plates move, they will diverge from or converge at their boundaries, as we appropriately categorised.
- New material must be produced where they diverge, as new crust is produced from the uprising mantle and what have you. 
- Where they converge, crust must be transformed and destroyed.

### 2.2.1 Divergence
Very simple: after every time step, we must fill all space around each divergent boundary that has become empty as space opens up between the plates. These new points get added onto to the plate on the appropriate side.


# Modeling 3: Hot Spots
Hot Spots are .... 

There are estimated to be about 40-50 active hot spots on Earth.

They are considered to have a constant position, unlike divergent boundaries which often move with the plates.

They are mostly centered on and around divergent boundaries (although it can still be quite distant), and *never* appear on top of subductive boundaries (the main type of convergence).
- **TODO Question:** How does that work with the fact that they're supposed to have constant positions? Or do divergent boundaries also have constant positions? And just convergent ones can move. Unless the thing is that if the divergent boundary moves, then the hot spots that start to become too far away die out.






# Further Refinement, Random Brainstorming, and notes that need to be organised

## Early Stages
- More or less define 2 opposite areas of the world as subduction zones, and the 2 areas at 90º with them as spread zones. I guess about half the world for each (or a bit less for subduction than for spreading). Convergence and divergence should be 
	- I'm not sure if this really makes sense... doesn't look like it THAT much on the map... although it does work out for hot zones. And it's in video 3.6 of the DGGV lehrvideos system erde

 - We can improve divergent boundaries by taking the initial line as a sketch, and then refining it with transform faults, as all divergent boundaries have a lot of such breaks.
	- The idea would be to create turns that are parallel with the relative motion of the boundary/its plates, so roughly at 90º from the initial boundary line.
  
- We can define Hot spots as geometric areas. Same for boundaries. It might be useful to consider pure geometric constructs, instead of discretizing them to a set of "crustal points".


- For each plate, you will have 2 opposite sides of the pole (which may be very different to each other); one must be subducting, the other must be divergent

- The amount of crust being destroyed should more or less equal the amount of crust being created... do we need to take this into consideration?


**Ridge elevation profile**
- If the plates are moving apart very fast, we get smoother slopes and wider profiles.
- If they're moving apart slowly, we get steep, irregular topography

**Tectonics Notes**
- in general, plates move.. so we need to move all the crustal points that make up the plate, and determine what happens to them
	- potentially... might we be able to do it all geometrically, and ignore the actual movement of points altogether? could that be more efficient? just calculating the new height of every point based on movement etc
		- I guess there might be 2 major methods here: actually moving crustal points around and simulating tectonic movements, or simply modelling elevation of points based on expectations of the results of the movements (without actually doing any movements)
- sometimes we create a new rift through a plate, or the beginning of one (might be a little tough to simulate a partial boundary)
- sometimes a hot spot might die out, or a new one appear
- sometimes (or always?) land from oceanic plates gets sutured onto a continental plate upon collision
- oceanic hot spots periodically create oceanic crust, but may create enough for it to become land.
	- If a hot spot is exactly on a boundary, it might create land onto both sides, leading to an island chain expanding in both directions from the same point
	- Other than that, see https://www.youtube.com/watch?v=Vpy-u53sOv0 @ 8:35
- continental hot spots periodically create volcanic continental crust, in the shape of volcanoes
- in oceanic-continenal convergent zones, in addition to the uplift, there is also creation of new continental crust (basically from melting of the subducted oceanic)
- in oceanic-oceanic convergent zones, the older plate sinks, causing the other one to rise, and the melting magma of the subducted plate can also rise and create oceanic crust. Or continental?
	- google "island arcs" I guess. It's very confusing, some sources say one thing, others the other, others say it's a mixture. Let's just call it continental.
		- saw one place say the rock type of island arcs is typically andesite, like in the Andes, as opposed to the basalt of oceanic crust. Andesite is basically a remixing and remelting of basalt and oceanic sediment, though.
- in continental-continental convergent zones, neither gets subducted, so the crust thickens and uplifts and forms huge mountain ranges (himalayas)


Oceanic Crust is created in divergent zones.
Oceanic Crust is also created at hot spots.
Continental Crust is created through arc volcanism at subduction zones.
Continental Crust is also pushed up at continental-oceanic subduction zones.


I have a lot of disparate notes on crust and rock types... need to bring it all together with a bit more detail.


IDEA: probably it would be best to create boundaries and plates one by one, carefully. So they always remain consistent.
	We could set-up the algorithm in such a way that the appearance of new rifts (like the east-african one) is the same mechanism as we use for the initial generation...
	So for the initial set-up, we would force a rift, find its opposing subduction zones, define plates and plate movement, and repeat, until we reach the desired number of plates (as specified in input params)
	An addendum to this though, which is also a reference to the 2-plate simulations I've seen in a few places to demonstrate euler rotation and divergent and subductive boundaries... the Earth is supposedly broken into 2 major convective cells, which create 2 major subductive zones and 2 major divergent zones. That seems incompatible. Is that just due to the lack of realism of a 2-plate system? Meaning that in a realistic system you would never have such few plates, so this would never happen.


SOME THINGS TO THINK ABOUT:
- Formally define each of the possible geological features? Might be useful. Can probably checks GPlates for their definitions
- Should we track rock types more specifically than just continental and oceanic crust? Given the thing about Andesite. Could be interesting as well if it then can help us determine where e.g. gold or diamond deposits might be more likely.
