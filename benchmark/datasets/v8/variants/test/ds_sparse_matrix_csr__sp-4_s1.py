def csr_matrix_product(elements: list) -> list:
    if not isinstance(elements, list) or not elements:
        return []
    valid = [float(x) for x in elements if isinstance(x, (int, float)) and (not isinstance(x, bool))]
    if not valid:
        return []
    dim = 4
    csr_values = []
    csr_cols = []
    csr_row_ptr = [0]
    idx = 0
    for r in range(dim):
        for c in range(dim):
            if idx < len(valid):
                val = valid[idx]
                if abs(val) > 0.01:
                    csr_values.append(val)
                    csr_cols.append(c)
                idx += 1
        csr_row_ptr.append(len(csr_values))
    vec = [1.0] * dim
    result = [0.0] * dim
    for r in range(dim):
        s = 0.0
        for i in range(csr_row_ptr[r], csr_row_ptr[r + 1]):
            s += csr_values[i] * vec[csr_cols[i]]
        result[r] = round(s, 3)
    return result