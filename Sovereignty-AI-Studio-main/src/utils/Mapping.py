Here is a corrected and refined version of your BFS pathfinding function:

from collections import deque

def solve(grid, start, end):
    queue = deque([start])  # Initialize queue with the start node
    visited = {start}
    parent = {start: None}

    while queue:
        x, y = queue.popleft()
        
        if (x, y) == end:
            # Reconstruct path
            path = []
            curr = end
            while curr is not None:
                path.append(curr)
                curr = parent[curr]
            return path[::-1]

        # Explore neighbors
        for nx, ny in [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]:
            if 0 <= nx < len(grid) and 0 <= ny < len(grid[0]) \
               and grid[nx][ny] == 1 and (nx, ny) not in visited:
                visited.add((nx, ny))
                queue.append((nx, ny))
                parent[(nx, ny)] = (x, y)
    
    return None  # No path found

This fixes the following issues:
queue was never initialized with start.
parent mapping and reconstruction were incorrect.
grid checks were missing the correct indices and conditions.
Path reconstruction now properly reverses the path using [::-1].

This function performs a BFS to find the shortest path from start to end in a 2D grid where 1 indicates a passable cell.
