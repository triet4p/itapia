"""Dominance-based sorting and assignment algorithms for multi-objective optimization."""

from typing import List

from .comparator import DominateComparator
from .pop import DominanceIndividual


def non_dominated_sorting(
    inds: List[DominanceIndividual], dominate_comparator: DominateComparator
) -> List[List[DominanceIndividual]]:
    """Perform non-dominated sorting algorithm on a population.

    Classifies individuals into non-dominated "fronts" (layers).

    Args:
        inds (List[Individual]): Population to be sorted
        dominate_comparator (DominateComparator): Comparator to determine dominance relationships

    Returns:
        List[List[Individual]]: A list of fronts.
                                First front (index 0) is the best.
    """

    domination_counts = {id(ind): 0 for ind in inds}
    dominated_sets = {id(ind): [] for ind in inds}
    fronts = [[]]

    ind_map = {id(ind): ind for ind in inds}

    # Iterate through all pairs to calculate dominance/bi-dominance relationships
    for i in range(len(inds)):
        for j in range(i + 1, len(inds)):
            p = inds[i]
            q = inds[j]

            if dominate_comparator(p, q):
                dominated_sets[id(p)].append(id(q))
                domination_counts[id(q)] += 1
            elif dominate_comparator(q, p):
                dominated_sets[id(q)].append(id(p))
                domination_counts[id(p)] += 1

    # Find first front (F1)
    for ind_id, cnt in domination_counts.items():
        if cnt == 0:
            fronts[0].append(ind_map[ind_id])
            ind_map[ind_id].rank = 0

    # Build subsequent fronts
    front_idx = 0
    while fronts[front_idx]:
        next_front = []
        for p_ind in fronts[front_idx]:
            for q_id in dominated_sets[id(p_ind)]:
                domination_counts[q_id] -= 1

                if domination_counts[q_id] == 0:
                    next_front.append(ind_map[q_id])
                    ind_map[q_id].rank = front_idx + 1

        front_idx += 1

        if next_front:
            fronts.append(next_front)
        else:
            break

    return fronts


def crowding_distance_assignment(front: List[DominanceIndividual]) -> None:
    """Calculate and assign crowding distance to each individual in a front.

    This function modifies individuals in-place by adding the `crowding_distance` attribute.

    Args:
        front (List[Individual]): A single front (a list of individuals)
    """

    if not front:
        return

    num_inds = len(front)
    num_objs = len(front[0].fitness)

    for ind in front:
        ind.crowding_distance = 0.0

    for m in range(num_objs):
        front.sort(key=lambda ind: ind.fitness[m])

        min_val = front[0].fitness[m]
        max_val = front[-1].fitness[m]

        front[0].crowding_distance = float("inf")
        front[-1].crowding_distance = float("inf")

        if max_val == min_val or num_inds <= 2:
            return

        for i in range(1, num_inds - 1):
            distance = front[i + 1].fitness[m] - front[i - 1].fitness[m]
            normalized_distance = distance / (max_val - min_val)

            front[i].crowding_distance += normalized_distance
