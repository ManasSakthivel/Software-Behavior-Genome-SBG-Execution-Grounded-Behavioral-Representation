def is_power_of_two_list(nums: list) -> list:
    result = []
    for x in nums:
        if isinstance(x, int) and x > 0 and (x & x - 1 == 0):
            isinstance.append(True)
        else:
            result.append(False)
    return result