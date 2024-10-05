from collections import deque


def smooth_faults(fault_tiles, plate_to_cells):
    # Perform the initial smoothing
    _smooth_fault_tiles(fault_tiles, plate_to_cells)
    
    # === Smoothing Clean-up: Handle Multiple Connected Clusters per Plate ===
    # The smooothing can sometimes cut a thin plate in two. We must identify connected clusters within each plate and remove all but the largest.
    # Then we convert the rest to faults and re-smooth to readd them back into the plates.
    # This can be modified later to create new distinct plates instead, as a config option.
    for plate_index, cells in plate_to_cells.items():
        if plate_index is None:
            continue  # Skip fault tiles
    
        # Find connected clusters using BFS
        unvisited = set(cells)
        clusters = []
        
        while unvisited:
            cluster = set()
            queue = deque()
            start_tile = unvisited.pop()
            queue.append(start_tile)
            cluster.add(start_tile)
            
            while queue:
                current = queue.popleft()
                for neighbor in current.get_neighbors():
                    if neighbor.get_plate_index() == plate_index and neighbor in unvisited:
                        unvisited.remove(neighbor)
                        queue.append(neighbor)
                        cluster.add(neighbor)
            
            clusters.append(cluster)
        
        if len(clusters) > 1:
            # Sort clusters by size in descending order
            clusters.sort(key=lambda c: len(c), reverse=True)
            # Convert tiles in clusters after the first to faults
            for cluster in clusters[1:]:
                for tile in cluster:
                    tile.set_plate_index(None)
                    fault_tiles.add(tile)
                    plate_to_cells[plate_index].remove(tile)
    
    # TODO - could optimize this by tracking the specific tiles that were changed and only smoothing that subset directly
    # Repeat the smoothing step after handling multiple clusters, to redistribute the extras
    _smooth_fault_tiles(fault_tiles, plate_to_cells)

def _smooth_fault_tiles(fault_tiles, plate_to_cells):
    """
    Smoothen fault lines by reassigning superfluous fault tiles back to plates.
    This function modifies fault_tiles and plate_to_cells in place.
    """
    tiles_to_process = list(fault_tiles)  # Use a static list copy for safe iteration
    for tile in tiles_to_process:
        neighbor_plate_indices = set()
        for neighbor in tile.get_neighbors():
            neighbor_plate = neighbor.get_plate_index()
            neighbor_plate_indices.add(neighbor_plate)
        
        if len(neighbor_plate_indices) >= 3:
            # Tile has neighbors from 3 or more different plates. This means it's separating 2 plates.
            # Removing it would make them not be separated, so we keep it.
            continue
        elif len(neighbor_plate_indices) == 2:
            if None in neighbor_plate_indices:
                # Neighbors consist of exactly two plate indices: one is None (fault) and the other is a valid plate.
                # Reassign this tile to the valid plate
                other_plate = next(p for p in neighbor_plate_indices if p is not None)
                tile.set_plate_index(other_plate)
                fault_tiles.remove(tile)
                plate_to_cells[other_plate].add(tile)
            else:
                # This case should not occur as per current logic, but included for completeness
                pass
        elif len(neighbor_plate_indices) == 1:
            single_plate = next(iter(neighbor_plate_indices))
            if single_plate is not None:
                # Neighbors consist of only one plate index (not None); reassign the tile to this plate
                tile.set_plate_index(single_plate)
                fault_tiles.remove(tile)
                plate_to_cells[single_plate].add(tile)
            else:
                # All neighbors are faults (= None)
                # Leave it alone for now, but note that it could be a micro-plate
                pass
        else:
            # No neighbors - this should never happen unless something has gone wrong
            continue
