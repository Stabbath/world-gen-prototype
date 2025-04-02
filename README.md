# The Basics
The surface of the world is made up of contiguous rigid plates that move against each other - the lithosphere -, pushed by convection currents in the underlying fluid asthenosphere, as well as slab-pull (if part of the plate is being pushed down, the rest gets dragged along) and ridge-push (wherever 2 plates move apart, there is material coming to the top and cooling down and becoming part of the slabs, and it pushes the rest of the slab away) forces.

We want to model this in a hyper-realistic but comfortably-abstracted way. Our goal isn't to create a complex soft-body simulation of a planet's entire mass. It's to get pretty realistic planets with realistic geological information. I actually considered the former for a moment, thinking about writing a custom soft-body physics engine, but then I remembered I'm not actually a geophysicist and I'm not getting paid to do this.

**Abstraction 1:** We ignore everything below the lithosphere. We can just simulate the effects the asthenosphere has on it abstractly, and we don't even need to think about anything lower than that.

# Pre-Modelling: Surface Representation
There are a few different ways to represent the surface, which is a key requirement of any model we develop here. I initially considered having multiple possible planet geometries, namely at least Flat, Cyllindrical, and Spherical, and I stand by it. Each one applies certain constraints to any model we use, but I believe this should not be an issue given a well-designed architecture. So we should consider those possibilities.

We can look at the surface as a grid of some sort, or discretize it into points. Height-map-based methods (where we calculate heights directly onto a static location on the surface) would tend to work better with a grid; truer tectonic simulations with movement of surfaces would tend to work better with surface points.

For Spheres, there is an easily-found (or LLM-able) method to distribute points evenly across a sphere: look-up **Fibonacci Spheres**. There are other solutions, that one is pretty popular and looks pretty good.
For flat and cyllindrical worlds, we don't need to worry about that. For a flat world it's pretty obvious, and for a cyllindrical world, consider that it's just a flat world that was curved inwards until 2 of its opposing edges connected to each other.

# Modelling 1: Plate and Boundary Geometries
## 1.1: Initial Generation
There are 2 options: 
1. You define plates and then the boundaries are the edges of those plates; or
2. You define boundaries, and then the plates are the space between those boundaries.

- **Option 1** is normally done through Voronoi partition or some flood-fill or expansion algorithm (with a discretized grid or set of points or shapes representing small sections of the crust).
- **Option 2...** isn't done? I don't remember finding anything in my research where they generated boundaries first. Which I think is a big reason why their continents so often look blocky. 

In our first prototype, we attempted something along the lines of 1, with an over-generation of plates which get merged down to the goal number, which was already an improvement over the "state-of-the-art" voronoi method which looks like crap. In that same prototype we also experimented with boundary-first generation, and it yielded better results still, at a slightly lower theoretical computational cost.

**Decision 1:** We generate boundaries first, using some random-walk or similar method, and calculate plates from the boundaries.

**Refinements:** 
- We must define each boundary as being between 2 and only 2 plates. Wherever there is a triple junction, we will see it as 3 boundaries meeting, and not as 1 boundary meeting another which ends at the junction.
	- This has basically no cost, and makes a lot of possible calculations later a lot easier.
- We should perhaps take care that no junctions above degree 3 exist, as only 4 is still possible and those collapse very quickly back down into a 3. Although if plates and boundaries move correctly, this will just solve itself.

## 1.2: Plate & Boundary Dynamics
### Rifting
As we will see later, the moving plates can get subducted, pushed back into the earth and destroyed, which would mean that over time plates would continuously be destroyed with some "stronger plate" or perfectly balanced set of plates eventually taking up the entire world. This is obviously not what happens on geologically-active planets. For example, on Earth, we can see something interesting happening currently: there is a rift forming between the Horn of Africa and the rest of the mainland, which in the future will eventually break it off into its own separate plate and begin pushing the African continent and the Horn of Africa away from each other, as a new divergent boundary and future rift. This is also what happened to push South America away from Africa, which has turned into what now is the mid-atlantic ridge.

So, we need to periodically and dynamically create new rifts to break apart large plates, creating a new triple junction at some location. Each time we do so, we will have to recalculate Euler poles and/or rotational velocity, probably in a way that preserves momentum for the 2 new sub-plates breaking apart from the original. That might be what explains the "instant" and drastic change in direction that one can observe in the volcanic chains of pacific islands, like Hawaii. **TODO Question** - I haven't seen that explained that way anywhere, but it seems like a likely physical grounding for that sort of event.

**TODO Question:** We may want to consider some kind of non-boundary boundary, a transitional boundary of sorts, to represent e.g. the current situation in East Africa. It's still one plate, but there is already a very visible topological rift.

**TODO citation needed & Question:** Rifts may sometimes form through highly active hot spots. Could that be what caused the east african one? As there are some hot spots in that area. Which one came first?

### Suture
**TODO Citation Needed:** Also when an oceanic plate is getting subducted, it may drag along continental crust (or sufficiently light or stacked-up crust in any case that may resist being pulled down) and crash it onto a continental plate. This may cause subduction to stop (I guess if there's too much resistance, or once the entire oceanic plate has been subducted) and lead to what's left of the previously-subducted plate to merge onto the other, becoming one plate.

We'll need to adjust movement, probably as a weighted average of the 2 plates?



# Modelling 2: Tectonic Motion

## 2.1: Isolated Motion
The simplest and most accurate method I managed to find after a lot of research and reflection: we ignore the specific forces at play, and instead focus on the movement itself. 

**Method:**
1. Each plate has what's called an Euler pole (see Euler's rotation theorem), and a rotational velocity around that pole.
2. We assign to each boundary a "boundary type", based on the movement of the 2 plates it borders:
	- If the 2 plates move away from each other, it is divergent.
	-  If the 2 plates move in the same direction, then if the plate moving away from the boundary is faster, it is divergent; else it is convergent.
		-  If they move at the *exact* same speed, we should maybe merge the 2 plates? I'm not sure how that would work; I guess the *exact* same speed is probably something that never actually really happens.
	- If the 2 plates move towards each other, the boundary is convergent.

**Possible Pitfalls:**
- Poles being too close to the center of a plate can cause it to move extremely slowly, which may not be desirable.
- There might be issues if we attribute directions to plates completely randomly, e.g. if they all move in the same direction and/or very slowly. I think a robust system where new rifts appear etc could probably solve this on its own, but it may make it take very long for the generation to yield a visually interesting world.

### Addendum:
**TODO:** note that boundaries themselves *also* move. I can't remember what solution I had proposed for this, but I think either we:
- Need to calculate a velocity for the fault based on its adjoining plates (maybe complicated, maybe inaccurate?); or
- We see, before filling in the crust for the divergent area, where the edge of the 2 plates is, and recenter our divergent boundary to be equidistant to both (a little complicated, but accurate); or
- We attach the boundary to one of the plates (which one?) and so it always moves with it (relatively simple, but likely inaccurate? although I think I read somewhere that this IS actually what happens, but I'm not sure.).

## 2.2: Convergence and Divergence 
As the plates move, they will diverge from or converge at their boundaries, as we appropriately categorised.
- New material must be produced where they diverge, as new crust is produced from the uprising mantle and what have you. 
- Where they converge, crust must be transformed and destroyed. Or in some cases also created, through volcanism.

### 2.2.1 Divergence
Very simple: after every time step, we must fill all space around each divergent boundary that has become empty as space opens up between the plates. These new points get added onto to the plate on the appropriate side.

### 2.2.2 Convergence
Typically, crust/plates are classed as either continental or oceanic. Their mineral composition is different, with a key difference being that continental is less dense. Density also changes with age: older = denser.

Where 2 plates converge, things happen. Firstly, in all but 1 case, there is subduction, which depends on which plate is less dense:
- **Oceanic-oceanic:** the older plate gets subducted underneath the younger.
  - There's a bit of a magmatic mess, leading to volcanic activity which creates new oceanic or intermediate crust. This creates a feature called an "island arc" (e.g. Caribbean chain). Not to be confused with hot spot island chains like Hawaii.
- **Continental-continental:** neither can be subducted because they are just too light, causing uplift and deformation leading to massive mountain chains (e.g. Himalayas).
- **Oceanic-continental:** the oceanic plate gets subducted underneath the continental plate. This causes uplift of the continental crust, causing mountain chains as well, but I think typically smaller than continental-continental (e.g. Andes).
  - Additionally, there's a bit of a magmatic mess going down with the melting of the subducted plate, which leads to volcanism and the creation of new continental crust, in addition to the uplift.

Another consideration is that at the subduction boundary, a deep trench always forms.



# Modelling 3: Hot Spots
Hot Spots are places on the earth's crust where magma seeps upwards, disconnected from any boundary line. They are considered to have a constant position, unlike boundaries which often move with the plates. As they periodically emit matter through volcanism, they form mountains. As the plates move through and away, this causes island chains (e.g. Hawaii). If there's enough mass to reach sea level, it's what's called a "seamount". These islands are really a series of volcanoes with varying levels of activity: as a volcano gets pushed away from the hot spot, its activity decreases until it becomes extinct.

They are mostly centered on and around divergent boundaries (although it can still be quite distant), and *never* appear on top of subductive boundaries (the main type of convergence).
- **TODO Question:** How does that work with the fact that they're supposed to have constant positions? Or do divergent boundaries also have constant positions? And just convergent ones can move. Unless the thing is that if the divergent boundary moves, then the hot spots that start to be too far away die out.

There are estimated to be about 40-50 active hot spots on Earth.

# Modelling 4: Crust Creation & Mineral Resources
As already mentioned, crust gets remixed and created at all bondaries except continental-continental convergent, as well as at hot spots.

There are a couple of open questions in this area:
1. Should we worry about keeping crust creating equal to crust destruction (at subduction areas)? Will that be relevant?
2. How do we represent different types of crust and rock? Is just a single monolithic "crust" enough? Do we just go with continental and oceanic? An arbitrary array? Or do we even go more specific and look at different types of rocks, in greater detail than just "oceanic" and "continental"?

One particular cool use of greater detail here, is that different minerals (like gold, iron ore, diamonds, etc) are more likely to form in different environments; so this could give us a blueprint for realistic resource distribution.

So below follow a number of explorations of these concerns...

## 4.1 Continental, Oceanic, or Both?
**TODO Question:** Plates can have both oceanic AND continental crust. Should we model this? And how? As a percentage, as 2 (or more) layers of a single plate, or some other way?

For reference, Earth's crust is about 30% continental.

## 4.2 Rock Types
Oceanic Crust is generally **basaltic**. It's less dense and the crust is thinner (5-10 km).
Continental Crust is generally **granitic**. It's denser and the crust is thicker (30-70km), and lives longer since it doesn't get subducted.
- Can also be **felsic**.

More specifically:
- Divergent zones create mostly *oceanic* **basaltic** material.
- **TODO - confirm:** Hotspot volcanism also creates *oceanic* **basaltic** material.
  - I think hotspot volcanism on continental mass actually creates continental or intermediate crust, not sure.
- Subduction-related volcanism creates *intermediate* **andesitic** material.
  - It "becomes" continental upon collision with a continental plate? I guess you can create continents even by just accreting andesitic materials.
  - Also through continued arc volcanism, it can directly be remixed into a more continental rock type.
  - **TODO - confirm** - is andesitic material refined into more granitic composition e.g. at continental-continental convergence? Plus through sediment recycling.

Rock types:
- Basalt is **mafic**.
- Andesite (and Dacite/Rhyolite) are **intermediate to felsic**.
- Granite is **felsic**.

**TODO - question:** I guess generally there's just still a lot to understand here, for me.

## 4.3 Mineral Resources
- **Gold and other ores:** Convergent boundaries and orogenic belts are prime zones. Areas that have undergone subduction-related magmatism or continental collision are likely to have rich mineralization.
- **Diamond:** Diamonds are linked to ancient, stable continental interiors ("cratons") with very thick lithosphere. Any continental crust that has remained intact and un-subducted for a long span can be treated as a craton. We expect diamond resources to be found in such regions.

### MAJOR TODO - Review the DeepResearch prompt I gave ChatGPT to find more info on this specific topic. Fill in the details here.


# Modelling 5: Erosion
Simplest form is just applying a bit of a smoothing function to everything at every time step. But as we want to have a climate system later, it may be better and equally realistic-looking to do no erosion until we have a climate system, and then do a lot of erosion-only steps or otherwise intensify erosion in the normal climate iterations. Conceptually I like the separation of still having just an erosion-only loop to finalize the base elevation map before we handle the rest. Or incorporating some generic heuristic-based erosion in the tectonic model itself, before we ever get around to looking at water etc.

# Modelling X: Bringing it All Together
I guess 2 options:
- Mathematical Modelling: we consider a static world, with lines for *current* boundaries, plates, and hot spots. We assign properties as normal. Instead of simulating movement and interaction, we implement mathematical formulae for the effect that each boundary has on the elevation of each point on the globe, with age being a major factor (and distance and other properties being related with age). For each point, we add up all of its effects to find its elevation. We add some random noise functions here and there as well as smoothing (also age-dependent). We hope it looks good at the end.
- Real Simulation: we simulate actual movement and interactions.

It's not clear to me which one would be easier in reality, even though the mathematical path *feels* easier. I think real simulation is the way to go.

**TODO - ponder? idk:** Oh! There's a third option: Mixed Modelling. We don't discretize the crust or whatever as points on a sphere, we stick to geometrical definitions of 1d and 2d objects (on a spherical surface); we simulate the movements of these geometries with each timestep, applying appropriate functions to each point, instead of moving the points. With each timestep, we calculate the effects on the heightmap of each geometric structure. We can dynamically destroy and create new plates etc just as we discussed, but keeping it strictly algebraic.
- Wait, does that work? For example, think about hotspot island chains. If they don't move, and we don't make plates move, that wouldn't work. Unless we add elevation at each timestep onto a specific coordinate offset from some static reference for the plate that the point is inside of... at that point, is it worth it to keep things algebraic? My brain hurts.


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


IDEA: probably it would be best to create boundaries and plates one by one, carefully. So they always remain consistent.
	We could set-up the algorithm in such a way that the appearance of new rifts (like the east-african one) is the same mechanism as we use for the initial generation...
	So for the initial set-up, we would force a rift, find its opposing subduction zones, define plates and plate movement, and repeat, until we reach the desired number of plates (as specified in input params)
	An addendum to this though, which is also a reference to the 2-plate simulations I've seen in a few places to demonstrate euler rotation and divergent and subductive boundaries... the Earth is supposedly broken into 2 major convective cells, which create 2 major subductive zones and 2 major divergent zones. That seems incompatible. Is that just due to the lack of realism of a 2-plate system? Meaning that in a realistic system you would never have such few plates, so this would never happen.


# Annex: Geological Features, A Quick Summary
- **Mid-Ocean Ridges:** Continuous submarine mountain chains at divergent boundaries. These form where plates spread apart and magma rises to create new crust.
- **Oceanic Trenches:** Deep troughs in the ocean where subduction is occurring. At convergent boundaries, the downgoing plate bends downward, forming a trench that can be several kilometers deeper than the surrounding seafloor.
- **Volcanic Island Arcs:** Curving chains of volcanic islands that arise from ocean-ocean subduction. As one oceanic plate subducts beneath another, volcanoes build up from the seafloor on the overriding plate. Over millions of years, these volcanoes grow into islands that form an arc shape roughly parallel to the trench.
- **Continental Volcanic Arcs:** Similar to island arcs, but occurring on the edge of a continent when an oceanic plate subducts beneath continental crust, just inland from the trench. These volcanoes, which are stratovolcanoes in nature, produce andesitic to rhyolitic lava and build mountains (e.g. Andes).
- **Non-volcanic Mountain Ranges (Orogenic Belts):** Where continents collide or compress, extensive mountain ranges form.
- **Plateaus and Foothills:** As a byproduct of orogeny, broad plateaus can develop (e.g. Tibet). Uplift zones can also occur away from collisions – for instance, a plume head could uplift a dome, or a region with extensive intrusions might isostatically rise.
- **Transform Fault Valleys:** While transform faults don’t create large vertical relief, the intense shear can produce a narrow depression or a series of sag ponds in continental settings​, and a noticeable geological formation (see San Andreas Fault).
  - In the ocean, we see fracture zones even beyond each transform boundary, extending its line in both directions beyond its ends, producing a similar feature.

Visually connecting them: 
- Mid-ocean ridges have the ridge effect going on, descending into abyssal plains, which later rise back up onto the continental shelf.
- Oceanic trenches cause volcanic island arcs in oceanic-oceanic convergences, or continental volcanic arcs inland in oceanic-continental.
- Continental-continental convergence causes orogenic belts closest to the boundary, followed by foothills and plateaus.
- Transform faults produce specifically transform-fault valleys.

**TODO:** I'm not sure if this is a complete list, check the GPlates api, they had good definitions for features.


# Annex: Future development
Meteor strikes - craters, atmospheric burn, exotic minerals, etc

Hypothetical complex conditions for additional types of crust/rock formation? Given:
- Different mantle compositions in distinct regions.
- Multiple crust-forming processes (e.g. extensive volcanism, plate tectonics, large impacts, or chemical layering).
- Exotic surface chemistry (e.g. ice crusts, sulfur plains, or metal-rich layers on different parts of the surface).
