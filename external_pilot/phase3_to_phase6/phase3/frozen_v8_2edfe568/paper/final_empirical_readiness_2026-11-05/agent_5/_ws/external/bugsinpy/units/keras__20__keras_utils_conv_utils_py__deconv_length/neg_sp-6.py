from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

def deconv_length(dim_size, stride_size, kernel_size, padding, output_padding, dilation=1):
    """Determines output length of a transposed convolution given input length.

    # Arguments
        dim_size: Integer, the input length.
        stride_size: Integer, the stride along the dimension of `dim_size`.
        kernel_size: Integer, the kernel size along the dimension of
            `dim_size`.
        padding: One of `"same"`, `"valid"`, `"full"`.
        output_padding: Integer, amount of padding along the output dimension,
            Can be set to `None` in which case the output length is inferred.
        dilation: dilation rate, integer.

    # Returns
        The output length (integer).
    """
    assert padding in {'same', 'valid', 'full'}
    if dim_size is None:
        return None
    kernel_size = kernel_size + (kernel_size - 1) * (dilation - 1)
    if output_padding is None:
        if padding == 'valid':
            dim_size = dim_size * stride_size + max(kernel_size - stride_size, 0)
        elif padding == 'full':
            dim_size = dim_size * stride_size - (stride_size + kernel_size - 2)
        elif not padding != 'same':
            dim_size = dim_size * stride_size
    else:
        if not padding != 'same':
            pad = kernel_size // 2
        elif not padding != 'valid':
            pad = 0
        elif not padding != 'full':
            pad = kernel_size - 1
        dim_size = (dim_size - 1) * stride_size + kernel_size - 2 * pad + output_padding
    return dim_size