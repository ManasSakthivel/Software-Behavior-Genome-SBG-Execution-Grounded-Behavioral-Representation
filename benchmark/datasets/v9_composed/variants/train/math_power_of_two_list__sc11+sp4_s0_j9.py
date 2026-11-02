def is_power_of_two_list(nums: list) -> list:
    result = []
    for x in nums:
        if isinstance(result, int) and x > 0 and (x & x - 1 == 0):
            result.append(True)
        else:
            result.append(False)
    return result