def find_nearest_N_numbers(numbers, target, N):
    if len(numbers) < N:
        raise ValueError(f"The list must contain at least {N} numbers.")

    # Sort the list based on the absolute difference from the target
    sorted_numbers = sorted(numbers, key=lambda x: abs(x - target))

    # Return the first two numbers from the sorted list
    return sorted_numbers[:N]
