from neighbor_functions import get_neighbors_wraparound

class HexTile:
    def __init__(self, col, row, grid):
        self.col = col
        self.row = row
        self.grid = grid
        self.plate_index = None

    def get_coords(self):
        return self.col, self.row
        
    def set_plate_index(self, plate_index):
        self.plate_index = plate_index

    def get_plate_index(self):
        return self.plate_index

    def get_neighbors(self):
        neighbors = []
        coord_tuples = get_neighbors_wraparound(self.col, self.row, self.grid.width, self.grid.height)
        for x, y in coord_tuples:
            neighbors.append(self.grid.get_tile(x, y))
        return neighbors

class HexGrid:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tiles = [None] * (width * height)
        for row in range(height):
            for col in range(width):
                self.tiles[col + row * self.width] = HexTile(col, row, self)
                
    def get_tiles(self):
        return self.tiles
    
    def get_tile(self, col, row):
        return self.tiles[col + row * self.width]
    
    def set_tile(self, col, row, tile):
        self.tiles[col + row * self.width] = tile