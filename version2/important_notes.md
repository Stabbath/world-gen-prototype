# Realistic Elevation Generation

For Realistic worlds, we always need to determine tectonic faults/plates one way or another. Even if we don't simulate tectonic movement, and instead follow an alternative method like I did in version1.

## Challenge 1: Generating INITIAL Faults and Plates

Generating them meaning simply drawing lines / shapes on a map.

Two options here.

### Option 1: Plates First

This will normally mean selecting N random starting points, and expanding the plate from there. Different algorithms exist for that, none of them yield truly natural-looking results, although it improves if you have an exaggerated number of initial plates M > N and then merge plates down to N.

### Option 2: Faults First

With some random walk algorithms and forking faults from already existing faults, we get much better results. Especially given that plate boundaries are very irregular: lots of right angle shifts, so that e.g. at divergent boundaries, there's actually a lot of small sections of divergent boundaries, connected by small perpendicular transform faults.

- However, read on to see why right angle shifts this early on might not be desired.

**This is likely the best option.**

## Challenge 2: Generating an Initial Elevation Map from Faults/Plates

### Option 1: Heuristics / Statistics

Perform a statistical modelling of elevation OR come up with abstract non-physically-based laws that generate an elevation map (as we do in version1) and which yield good-looking results.

### Option 2: Tectonic Simulation

So many ways to tackle this...

- Soft-Body Simulation: abstract crustal points as compressible spheres with appropriate physical properties, push them against each other, see what happens. Computationally and design-wise very expensive, even with a simplified model.
- Euler Poles: assign an euler pole and rotational velocity to each plate, define plates as points. Move points around accordingly. Create new points at places where plates move away from each other. Where points collide, handle subduction.
  - An issue with this is that if we generated faults that are realistic (meaning, with lots of right-angle turns), the directions might not be consistent with this. A work-around for that is we could have an initial base fault which isn't so big with the right-angle turns, and then after finding the rotational frame for the plates we can split the fault apart into segments and get that right-angley look.
- Fault-Based Euler Poles: assign an initial pair of angular vectors to each fault determining where it's pushing the adjoining plates. For each plate, add up the vectors being imposed on it, and their origins, and I think we can acquire an euler pole and rotational velocity from that somehow.
  - Seems pretty complex, and the only benefit is that we could generate right-angle faults from the start; which is likely not even preferred? It feels more natural to get those breaks as the plates pull apart.

I've had some more random ideas which weren't fully-formed enough to really be able to express them... But I do believe there's a lot more that could be proposed here.

**So let's say we go with Euler Poles, having used a faults-first approach without right angle turns.**

That means that we now have a world with:
- A surface defined by crustal points.
- Relatively stable straight lines designating faults, also represented by a series of points.
- Plates in between those faults, whose movement we have defined, which are really just a set of surface points.

Next step is to determine the type of each fault.
- Look at rotational vector of both plates touching it.

Next step is to adjust the faults for realistic-looking break-apart:
- Randomly shift the line in segments, parallel to rotational vector, to yield the right-angle turns and in-between transform faults, in a geologically-sound way.


**THINGS I NEED TO UNDERSTAND STILL:**

- Hot spots are absolute, unmoving. But they can die out eventually, probably, after 100 million years or something. Which means they can also spawn in. Why, where, when, how?
- Faults also move, I think all of them always, practically speaking. They move in absolute terms; of course in their referential, they're stationary, and the 2 plates they split are pushed away at equal speeds; but in reality, the fault itself is moving in absolute terms.
  - We can use hot spots as a reference for absolute movement, as hot spots don't move in absolute terms. I guess there's also some rotating frame of reference based on the earth's axis which would yield the same absolute reference, but that's more complicated. So we can spawn in at least one hot spot, use it as a reference, if it dies out, change to another one (or just have that one hot spot be immortal). I guess realy, it is in relation to this neutral referential that hot spots remain stationary.
  - **So then the question:** how can we determine the movement of the fault itself?
- New faults appear, creating new plates. For example, the one that's slowly detaching the Horn of Africa from the rest of the African plate. When, how, where?
- Plates can be completely subducted, destroying them. They can also be partially subducted in a way that breaks them apart into 2 separate plates. Do they both preserve the same velocity? Do plates just always have the same velocity for their entire life? Surely that's not quite it.
