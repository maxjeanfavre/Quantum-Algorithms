"""
plotting.py

Plotting utilities for Latin-square result analysis.
"""
from typing import Dict, Tuple
import matplotlib.pyplot as plt


def plot_grid_counts_histogram(
    grid_counts: Dict[Tuple[int, ...], int],
    n: int,
    m: int
) -> None:
    """
    Display a bar chart of grid configuration counts.

    Each bar is labeled with a single-line representation of the grid:
      rows are comma-separated and joined by '|'.

    Parameters:
        grid_counts: Mapping from flat grid tuples to occurrence counts.
        n:           Number of rows.
        m:           Number of columns.
    """
    # Prepare labels and values
    labels = []
    values = []
    for grid, count in grid_counts.items():
        # Build one-line label: 'r0; r1; ...'
        row_strs = [','.join(str(grid[i*m + j]) for j in range(m)) for i in range(n)]
        label = '|'.join(row_strs)
        labels.append(label)
        values.append(count)

    # Plot histogram
    plt.figure()
    indices = range(len(values))
    plt.bar(indices, values)
    plt.xticks(indices, labels, rotation='vertical')
    plt.xlabel('Grid configurations')
    plt.ylabel('Counts')
    plt.title('Distribution of Final Grid Outcomes')
    plt.tight_layout()
    plt.show()
