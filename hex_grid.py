from functools import total_ordering

# TODO Plate and Fault should be moved to a separate file, as the HexGrid should be independent from the Tectonic Method.
class Plate:
    def __init__(self, plate_index, tiles):
        self.id = plate_index
        self.tiles = tiles
        
    def set_tiles(self, tiles):
        self.tiles = tiles
        
    def borders_pole(self):
        for tile in self.tiles:
            if tile.is_polar():
                return True
        return False
    
class Fault:
    def __init__(self, fault_index, tiles):
        self.id = fault_index
        self.fault_index = fault_index
        self.tiles = tiles
    
    def set_tiles(self, tiles):
        self.tiles = tiles

    def get_tiles(self):
        return self.tiles

    def refresh_neighbor_groups(self):
        faults = {}
        plates = {}
        for tile in self.tiles:
            tile_neighbors = tile.get_neighbors()
            
            for tn in tile_neighbors:
                tnFaultIdx = tn.get_fault_index()
                if tnFaultIdx != self.fault_index:
                    if tnFaultIdx is None:
                        plates[tn.get_plate_index()] = True
                    else:
                        faults[tnFaultIdx] = True
        self.fault_neighbor_indices = list(faults)
        self.plate_neighbor_indices = list(plates)

    def get_fault_neighbor_indices(self):
        return self.fault_neighbor_indices
        
    def get_plate_neighbor_indices(self):
        return self.plate_neighbor_indices

@total_ordering
class HexTile:
    def __init__(self, col, row, grid):
        self.id = '$col.$row'
        self.col = col
        self.row = row
        self.grid = grid
        self.is_line = False
        self.plate_index = None
        self.fault_index = None
        self.continent_label = None
        self.is_selected = False
        self.altitude = 0
        # TODO - review continent label and is_line; also is_selected. Things that are just used during gen should probably be kept in an external dictionary/array rather than on the tile
        # TODO - same goes for plate index and fault index

    def is_polar(self):
        neighbors = self.get_neighbors()
        print('polar tile')
        return len(neighbors) < 6

    def get_altitude(self):
        return self.altitude

    def set_altitude(self, altitude):
        self.altitude = altitude        

    def get_coords(self):
        return self.col, self.row
        
    def set_plate_index(self, plate_index):
        self.plate_index = plate_index
        if plate_index is not None:
            self.set_fault_index(None) # ensure it's not a fault

    def get_plate_index(self):
        return self.plate_index

    def set_fault_index(self, fault_index):
        self.fault_index = fault_index
        if fault_index is not None:
            self.set_plate_index(None) # ensure it's not a plate

    def get_fault_index(self):
        return self.fault_index

    def get_neighbors(self):
        neighbors = []
        coord_tuples = self.grid.func_neighbors(self.col, self.row, self.grid.width, self.grid.height)
        for x, y in coord_tuples:
            neighbors.append(self.grid.get_tile(x, y))
        return neighbors
    
    def __eq__(self, other):
        if not isinstance(other, HexTile):
            return NotImplemented
        return (self.col, self.row) == (other.col, other.row)

    def __lt__(self, other):
        if not isinstance(other, HexTile):
            return NotImplemented
        return (self.col, self.row) < (other.col, other.row)

    def __hash__(self):
        return hash((self.col, self.row))

class HexGrid:
    def __init__(self, width, height, func_neighbors):
        self.width = width
        self.height = height
        self.tiles = [None] * (width * height)
        self.func_neighbors = func_neighbors
        for row in range(height):
            for col in range(width):
                self.tiles[col + row * self.width] = HexTile(col, row, self)
                
    def get_tiles(self):
        return self.tiles
    
    def get_tile(self, col, row):
        if 0 <= col < self.width and 0 <= row < self.height:
            return self.tiles[col + row * self.width]
        else:
            return None
    
    def set_tile(self, col, row, tile):
        self.tiles[col + row * self.width] = tile

    def set_plates_from_lists(self, plates):
        self.plates = []
        for plate in plates:
            self.plates.append(Plate(plate[0].get_plate_index(), plate));

    def set_faults_from_lists(self, faults):
        self.faults = []
        for fault in faults:
            self.faults.append(Fault(fault[0].get_fault_index(), fault)); # TODO - kind of hacky, clean it up later
