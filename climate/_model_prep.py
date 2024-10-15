# -*- coding: utf-8 -*-
"""
Created on Mon Oct 14 14:14:57 2024

@author: Francisco
"""

import networkx as nx
import matplotlib.pyplot as plt

# Define a graph where nodes are climate variables and edges represent dependencies
G = nx.DiGraph()

# Adding nodes and their dependencies
dependencies = {
    "prev_solar_radiation": [],
    "prev_water_flow": [],
    "prev_temperature": [],
    "prev_vapor_capacity": [],
    "prev_evaporation": [],
    "prev_evapotranspiration": [],
    "prev_plant_humidity_absorption": [],
    "prev_vapor_content": [],
    "prev_air_pressure": [],
    "prev_wind_pressure": [],
    "prev_wind_cloud": [],
    "prev_wind_temp": [],
    "prev_wind_vapor": [],
    "prev_wind": [],
    "prev_cloud_density": [],
    "prev_precipitation": [],
    "prev_biomass": [],
    "solar_radiation": ["latitude", "prev_cloud_density", "solar_constant"],
    "water_flow": ["precipitation", "is_sea_tile"],
    "temperature": ["solar_radiation", "solar_constant", "geothermal_constant", "altitude", "wind_temp"],
    "vapor_capacity": ["temperature"],
    "evaporation": ["prev_water_flow", "prev_temperature", "prev_vapor_content", "prev_vapor_capacity"],
    "evapotranspiration": ["prev_biomass", "prev_temperature", "prev_vapor_content", "prev_vapor_capacity"],
    "plant_humidity_absorption": ["prev_biomass", "prev_vapor_content", "prev_vapor_capacity"],
    "vapor_content": ["evaporation", "evapotranspiration", "plant_humidity_absorption", "precipitation", "wind_vapor"],
    "air_pressure": ["altitude", "temperature", "wind_pressure"],
    "cloud_density": ["vapor_content", "vapor_capacity", "wind_cloud"],
    "biomass": ["prev_biomass", "prev_water_flow", "prev_evapotranspiration", "prev_plant_humidity_absorption", "prev_solar_radiation", "prev_temperature"],
    "wind": ["air_pressure"],
    # these wind variables dont matter, because we do them in their own phase at the end of each iteration
    "wind_pressure": [], #["wind", "air_pressure"],
    "wind_cloud": [], #["wind", "cloud_density"],
    "wind_temp": [], #["wind", "temperature"],
    "wind_vapor": [], #["wind", "vapor_content"],
    # doesnt matter because we calculate it at the end and then adjust in-state variables
    "precipitation": [], # ["vapor_content", "vapor_capacity", "cloud_density"],
}
# TODO - note that, in breaking this down manually across states to eliminate cycles,
# there's basically 2 options:
#   1 - make evaporation, evapotranspiration, and humidity absorption depend on prev state
#   2 - make vapor content depend on previous state
# Somehow, 1 felt more natural to me. And then we just turn to using the prev_state for every variable other than vapor_content too to make it feel more consistent.


# NOTE only - all of these represent the yearly average across the entire tile
units = {
    "solar_radiation": "W/m^2", # Average power per unit of surface area
    "water_flow": "m/s", # Volumetric flow averaged out over surface area
    "temperature": "C", # In Celsius
    "vapor_capacity": "kg/m^3", # Maximum density of water vapor in the air
    "vapor_content": "kg/m^3", # Density of water vapor in the air
    "evaporation": "kg/m^2/s", # Water mass evaporated per second per unit of surface area
    "evapotranspiration": "kg/m^2/s", # Water mass evapotranspirated per second per unit of surface area
    "air_pressure": "Pa",
    "wind": "m/s",
    "cloud_density": "%", # 100% means every unit of surface area is covered by the thickest cloud possible
    "precipitation": "kg/m^2", # Average rainfall volume per unit of surface area
    "biomass": "kg/m^2", # Average biomass per unit of surface area
    "plant_humidity_absorption": "kg/m^2/s" # Water taken in by plants directly from the atmosphere
}


# Add dependencies to the graph
for node, deps in dependencies.items():
    for dep in deps:
        G.add_edge(dep, node)

# Identify and remove source nodes (nodes with no incoming edges)
source_nodes = [node for node in G.nodes() if G.in_degree(node) == 0]
# G.remove_nodes_from(source_nodes)
print("Source nodes (processed at the start):", source_nodes)

# # Wind and wind factors are added in a later phase
# # Same with water flow and accumulated water
# wind_nodes = [node for node in G.nodes() if "wind" in node or "air_pressure" in node]
# G.remove_nodes_from(wind_nodes)
# water_nodes = [node for node in G.nodes() if "water" in node or "precipitation" in node]
# G.remove_nodes_from(water_nodes)
# print("Wind nodes (processed at the end):", wind_nodes)
# print("Water nodes (processed at the end):", water_nodes)

# other_nodes = [node for node in G.nodes() if "vegetation" in node or "solar" in node or "temperature" in node]
# G.remove_nodes_from(other_nodes)


# Function to find all cycles in the graph
def find_longest_cycle(graph):
    try:
        # Get all simple cycles in the graph
        cycles = list(nx.simple_cycles(graph))
        
        # Find the longest cycle
        if cycles:
            longest_cycle = max(cycles, key=len)
            return longest_cycle
        else:
            return None
    except nx.NetworkXNoCycle:
        # If no cycle is found, return None
        return None

# Find the longest cycle in the graph
longest_cycle = find_longest_cycle(G)

if longest_cycle:
    print("The longest cycle is:", longest_cycle)
else:
    print("No cycle found in the graph.")

# Visualization of the graph (optional)
plt.figure(figsize=(10, 8))
nx.draw(G, with_labels=True, node_color="lightblue", font_weight="bold", node_size=2000, font_size=10, arrows=True)
plt.show()


# Conclusions for our iterative method:
# input: prev_state, latitude, solar_constant, is_sea_tile, geothermal_constant, altitude
# 1. source calculations
#   1.1 latitude
#   1.2 solar radiation - from previous state's cloud density (its not too important to have the most accurate factor here)

# 2. our mega strongly-connected component
#   2.1 calculate vegetation density from previous state (start with this, conceptually it is easy to isolate and it comes after the watering from the previous iteration, and it's one of the less important variables to be precise with here, and it depends on itself from the previous state already)
#   2.2 calculate temperature
#       2.2.1 calculate air pressure
#   2.3 calculate evaporation from previous state (water flows should be relatively stable so this wont matter much)
#   2.4 calculate vapor capacity, evapotranspiration
#   2.5 calculate vapor content
#   2.6 calculate cloud density

# 4. distribution flows
#   4.1 wind
#       4.2.1 calculate wind map from air pressure
#       4.2.2 distribute temperature, air pressure, vapor content and clouds
#   4.2 water
#       4.2.1 calculate precipitation - important that it's AFTER wind
#       4.2.2 create map of water flow. Additive process only, flow is not destroyed, only added to children.
#           sea tiles always have maximum flow
