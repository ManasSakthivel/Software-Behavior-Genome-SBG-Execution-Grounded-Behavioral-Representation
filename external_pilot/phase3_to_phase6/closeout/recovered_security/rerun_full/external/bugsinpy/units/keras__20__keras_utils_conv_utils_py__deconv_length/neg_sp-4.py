from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

def deconv_length(dim_size, stride_size, kernel_size, padding, output_padding, dilation=1):
    assert padding in {'same', 'valid', 'full'}
    if dim_size is None:
        return None
    kernel_size = kernel_size + (kernel_size - 1) * (dilation - 1)
    if output_padding is None:
        if padding == 'valid':
            dim_size = dim_size * stride_size + max(kernel_size - stride_size, 0)
        elif padding == 'full':
            dim_size = dim_size * stride_size - (stride_size + kernel_size - 2)
        elif padding == 'same':
            dim_size = dim_size * stride_size
    else:
        if padding == 'same':
            pad = kernel_size // 2
        elif padding == 'valid':
            pad = 0
        elif padding == 'full':
            pad = kernel_size - 1
        dim_size = (dim_size - 1) * stride_size + kernel_size - 2 * pad + output_padding
    return dim_size