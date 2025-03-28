# Key References

- GPlates: https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2018gc007584 and https://www.earthbyte.org/Resources/GPlates_tutorials/GPlates_Data_Manual/GPlates_Data_Manual.html 
- DGGV video lectures: e.g. 
  - https://www.dggv.de/en/portfolio/3-5-convection-currents-in-the-earths-mantle/ / https://www.youtube.com/watch?v=E_27itP8gZ4&list=PL_MQ_zbwvfYAQ9gmqas62EVFFH9PyJVFf&index=10
- (Hawaii University) https://laulima.hawaii.edu/access/content/group/dbd544e4-dcdd-4631-b8ad-3304985e1be2/book/toc/toc.htm 

Check this out for climate later:
- https://nickmcd.me/2018/07/10/procedural-weather-patterns/


# Realistic Elevation Generation

For Realistic worlds, we always need to determine tectonic boundaries/plates one way or another. Even if we don't simulate tectonic movement, and instead follow an alternative method like I did in version1.

## Challenge 1: Generating INITIAL Boundaries and Plates

Generating them meaning simply drawing lines / shapes on a map.

Two options here.

### Option 1: Plates First

This will normally mean selecting N random starting points, and expanding the plate from there. Different algorithms exist for that, none of them yield truly natural-looking results, although it improves if you have an exaggerated number of initial plates M > N and then merge plates down to N.

### Option 2: Boundaries First

With some random walk algorithms and forking boundaries from already existing boundaries, we get much better results. Especially given that plate boundaries are very irregular: lots of right angle shifts, so that e.g. at divergent boundaries, there's actually a lot of small sections of divergent boundaries, connected by small perpendicular transform boundaries.

- However, read on to see why right angle shifts this early on might not be desired, and it might be better to start with relatively straight lines.

**This is likely the best option.**

## Challenge 2: Generating an Initial Elevation Map from Boundaries/Plates

### Option 1: Heuristics / Statistics

Perform a statistical modelling of elevation OR come up with abstract non-physically-based laws that generate an elevation map (as we do in version1) and which yield good-looking results.

### Option 2: Tectonic Simulation

So many ways to tackle this...

- Soft-Body Simulation: abstract crustal points as compressible spheres with appropriate physical properties, push them against each other, see what happens. Computationally and design-wise very expensive, even with a simplified model.
- Euler Poles: assign an euler pole and rotational velocity to each plate, define plates as points. Move points around accordingly. Create new points at places where plates move away from each other. Where points collide, handle subduction.
  - An issue with this is that if we generated boundaries that are realistic (meaning, with lots of right-angle turns), the directions might not be consistent with this. A work-around for that is we could have an initial base boundary which isn't so big with the right-angle turns, and then after finding the rotational frame for the plates we can split the boundary apart into segments and get that right-angley look.
- Boundary-Based Euler Poles: assign an initial pair of angular vectors to each boundary determining where it's pushing the adjoining plates. For each plate, add up the vectors being imposed on it, and their origins, and I think we can acquire an euler pole and rotational velocity from that somehow.
  - Seems pretty complex, and the only benefit is that we could generate right-angle boundaries from the start; which is likely not even preferred? It feels more natural to get those breaks as the plates pull apart.

I've had some more random ideas which weren't fully-formed enough to really be able to express them... But I do believe there's a lot more that could be proposed here.

**So let's say we go with Euler Poles, having used a boundaries-first approach without right angle turns.**

That means that we now have a world with:
- A surface defined by crustal points.
- Relatively stable straight lines designating boundaries, also represented by a series of points.
- Plates in between those boundaries, whose movement we have defined, which are really just a set of surface points.

Next step is to determine the type of each boundary.
- Look at rotational vector of both plates touching it.

Next step is to adjust the boundaries for realistic-looking break-apart:
- Randomly shift the line in segments, parallel to rotational vector, to yield the right-angle turns and in-between transform boundaries, in a geologically-sound way.
  - Could also consider representing "fracture zones" somehow here (the lines that extend further beyond these micro transform boundaries, but which are not boundaries as they are the same plate)

**QUESTIONS THAT POPPED UP THAT I SOLVED:**
1. Boundaries also move, I think all of them always, practically speaking. They move in absolute terms; of course in their referential, they're stationary, and the 2 plates they split are pushed away at equal speeds; but in reality, the boundary itself is moving in absolute terms.
  - We can use hot spots as a reference for absolute movement, as hot spots don't move in absolute terms. I guess there's also some rotating frame of reference based on the earth's axis which would yield the same absolute reference, but that's more complicated. So we can spawn in at least one hot spot, use it as a reference, if it dies out, change to another one (or just have that one hot spot be immortal). I guess realy, it is in relation to this neutral referential that hot spots remain stationary.
  - **So then the question:** how can we determine the movement of the boundary itself?
  - **ANSWER:** Within the euler pole framework, if one plate has a greater velocity than the other away from the boundary, then the boundary moves towards it; because the boundary always produces material equally in both directions. So with each step, we can move the boundary by the difference in the euler velocity between the two plates.


**THINGS I NEED TO UNDERSTAND STILL:**

1. Hot spots are absolute, unmoving. But they can die out eventually, probably, after 100 million years or something. Which means they can also spawn in. Why, where, when, how?
3. New divergent boundaries appear, creating new plates. For example, the one that's slowly detaching the Horn of Africa from the rest of the African plate. When, how, where?
4. Plates can be completely subducted, destroying them. They can also be partially subducted in a way that breaks them apart into 2 separate plates. Do they both preserve the same velocity? Do plates just always have the same velocity for their entire life? Surely that's not quite it.
5. Boundaries can also disappear, at least divergent ones. In lecture 3.1 of the German Geological Society videos, he mentions one in Germany that started breaking apart Europe and then stopped.
6. Spontaneous subduction (3.3 GGS) can happen, creating new subduction zones.
  - As crust moves away from the source ridge, it gets thicker and less dense, especially in the lithospheric mantle. As it gets up to 3.4 g/cm^3 or so, it can happen (but doesn't always) that it begins to sink, to having a greater density than the layer immediately below it.
7. I don't think boundaries should necessarily be hardcoded as divergent, convergent, whatever. I think that's just behavior that arises from natural forces.
  - Could we simply model, as I had originally envisioned in version 1, sources of material and sinks of material?
  - How would this mix with our current modelling concept where plates have movement assigned to them, and then we refine the shape of boundaries based on the kind of boundary they are? I suppose it's not so much the kind of boundary they are as it is, really, the movement they are implied to be imposing onto the plates.
8. How do we actually calculate changes in elevation from tectonic movement? Especially if we don't consider oceanic and continental crusts as being separate. Ideally we would be able to base it on a hystographic curve or statistical distribution of elevation.

**POSSIBLE ANSWERS TO THESE QUESTIONS:**
1. Probably too complex, probably should just do it a bit random based on some arbitrary heuristic.
3. When the plate gets too stretched, a new break can surge, allowing flow upwards, thence pushing apart the 2 sides and creating a plate separation. Probably should just do it a bit random based on some arbitrary heuristic. We can probably assume at some random intervals (possibly with some conditions) that a new triple junction forms, and a new pseudo-boundary starts forming off of it (an incomplete boundary, that does not fully separate 2 plates, but instead is in the process of dividing a plate into two).
  - See Annex 1.
4. Plate velocity changes over time, since it results from the balance of ridge-push, slab-pull, and mantle drag forces, which are not constant. However, still need to look into how velocity would change over time, and also for how it would change upon plate splitting. Not only intensity changes, but also the euler pole can change (this can be observed by dramatic shifts in the direction of hotspot island chains).
5. It seems that in GPlates divergent boundaries are given a specific time when they are extinguished. And they tend to die out quickly, not gradually slow down into obscurity. So we should stick with that, and just decide for each one when it dies.
  - Should probably ensure a closed system, so we would track how much material is rising across the entire world, and how much is going down, and keep that constant.
6. We could model this through plate age alone, I guess? Have a probabilistic function which gives a certain chance, for each age, of it starting to sink. On each step, we roll the dice, and the sinking starts if it's a jackpot.
  - We would probably track, for any given plate, its oldest crustal points (or, possibly, have an age-sorted index, which would be O(1) time to maintain)
7. See Annex 2.
8. Probably have to handle it heuristically and statistically, ensuring:
  - Divergent boundary = ridge at the boundary, which gets smoothed down and shortened with distance from the ridge until it turns into an abyssal plain.
  - Convergent boundary = uplift... I guess similar to divergence? But taller?
  - Over time, values are relaxed towards a preconfigured hypsographic distribution.

**Further brainstorming...**

We should consider that each boundary is a line between 2 and only 2 plates. Wherever there's a triple junction, the boundary ends, and 2 new ones begin. This way, we can have a clear reference to what plate is on either side of it.
- We can generate boundaries as if they were continuing further, the point is just that the final data model must split it into multiple boundaries.

Boundaries (always?) move, in absolute terms. Could we just attach them to one of the plates they divide? So it moves with it. Or do we need to manually move it.

# ANNEX

## ANNEX 1: ChatGPT response to "How could you estimate the Euler rotation of the 2 new plates that emerge from breaking a plate apart?"

To estimate the Euler pole (latitude, longitude) and rotation rate (ω) for each of two new plates created when one breaks apart, you essentially solve for the rigid‑body rotation that best fits the observed motion of their shared boundary (and any other known relative motions). Here’s a step‑by‑step recipe:

1. **Define reference frame & plate IDs**  
   • Pick one plate as your “fixed” reference (e.g. Plate A).  
   • Assign the newly detached block its own plate ID (Plate B). citeturn0search25

2. **Measure boundary motion vectors**  
   • Along the nascent rift, sample velocity vectors (direction + rate) from seafloor‑spreading magnetic anomalies or GPS.  
   • Ideally you need ≥3 non‑colinear points per plate.

3. **Set up the spherical kinematic equations**  
   For any surface point (lat, lon), the velocity **v** = ω×r, where r is the position vector on the unit sphere. In spherical form:
   \[
     v = ωR\sin(angular\;distance)
   \]
   with known azimuth.

4. **Solve for each plate’s Euler parameters via least squares**  
   • For Plate A, use its boundary velocities relative to Plate B → solve for (λA, φA, ωA).  
   • For Plate B, use velocities relative to Plate A → solve for (λB, φB, ωB).  
   • Formally minimize Σ|v_obs – v_pred(λ,φ,ω)|².

5. **Check consistency at breakup instant**  
   • Ensure the relative rotation between A and B matches the opening rate along the new rift (difference of their Euler rotations).  
   • If not, iterate weights or include adjacent plate constraints.

6. **Implement in GPlates**  
   • Add two new lines in your .rot file at the breakup age:  
     ```
     A  t  poleLatA  poleLonA  rateA  000  
     B  t  poleLatB  poleLonB  rateB  000
     ```  
   • Lower‑time entries for each plate retain those poles until any subsequent change.

Because each daughter plate now has its own finite rotation (pole + rate), their velocities immediately diverge: neither “inherits” the parent’s speed wholesale, but is determined by the best‑fit Euler solution for its boundary kinematics.

## ANNEX 2: ChatGPT comments on my "inner monologue" as written in Question 7

Your “inner monologue” is exactly how GPlates actually works under the hood: boundaries aren’t hard‑wired as “divergent” or “convergent.” Instead, you store only rigid plates (each with an Euler rotation) and a continuously‑closing network of edges between them. At each timestep GPlates computes the relative velocity vector across every edge and — based purely on that kinematic field — classifies each segment as:

    Source (plates moving apart)

    Sink (plates converging)

    Neutral/Transform (plates sliding past)
    en.wikipedia.org
    ​
    agupubs.onlinelibrary.wiley.com

Put simply:

    Assign each plate a rotation (pole + rate).

    For every shared edge, calculate relative motion from plate A → plate B.

    Project that motion onto the edge’s normal: positive = divergence (material added), negative = convergence (material removed), zero = shear.

    No boundary type property needs pre‑assignment — it “emerges” from step 3.

This is exactly what GPlates’ topological network + velocity‑field framework implements.
