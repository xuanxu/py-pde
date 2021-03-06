r"""
This module implements differential operators on cylindrical grids 

.. autosummary::
   :nosignatures:

   make_laplace
   make_gradient
   make_divergence
   make_vector_gradient
   make_vector_laplace
   make_tensor_divergence
   make_operator
   
   
.. codeauthor:: David Zwicker <david.zwicker@ds.mpg.de>


.. The following contains text parts that are used multiple times below:

.. |Description_cylindrical| replace:: 
  This function assumes polar symmetry of the cylindrical grid, so that fields
  only depend on the radial coordinate `r` and the axial coordinate `z`. Here,
  the first axis is along the radius, while the second axis is along the axis of
  the cylinder. The radial discretization is defined as
  :math:`r_i = (i + \frac12) \Delta r` for :math:`i=0, \ldots, N_r-1`.
"""

from typing import Callable

from . import PARALLELIZATION_THRESHOLD_2D
from .. import CylindricalGrid
from ..boundaries import Boundaries
from ...tools.numba import nb, jit_allocate_out

        
        
def make_laplace(bcs: Boundaries) -> Callable:
    """ make a discretized laplace operator for a cylindrical grid
    
    |Description_cylindrical|

    Args:
        bcs (:class:`~pde.grids.boundaries.axes.Boundaries`):
            |Arg_boundary_conditions|
        
    Returns:
        A function that can be applied to an array of values
    """
    assert isinstance(bcs.grid, CylindricalGrid)
    bcs.check_value_rank(0)
    boundary_r, boundary_z = bcs

    # calculate preliminary quantities
    dim_r, dim_z = bcs.grid.shape
    dr_2, dz_2 = 1 / bcs.grid.discretization**2
    
    value_outer = boundary_r.high.get_virtual_point_evaluator()
    region_z = boundary_z.get_region_evaluator()
    
    # use processing for large enough arrays 
    parallel = (dim_r * dim_z >= PARALLELIZATION_THRESHOLD_2D**2)

    @jit_allocate_out(parallel=parallel, out_shape=(dim_r, dim_z))
    def laplace(arr, out=None):
        """ apply laplace operator to array `arr` """
        for j in nb.prange(0, dim_z):  # iterate axial points
            # inner radial boundary condition
            i = 0
            arr_z_l, arr_c, arr_z_h = region_z(arr, (i, j))
            out[i, j] = (
                2 * (arr[i + 1, j] - arr_c) * dr_2 +
                (arr_z_l - 2 * arr_c + arr_z_h) * dz_2
            )
            
            if dim_r == 1:
                continue  # deal with singular radial dimension
            
            for i in range(1, dim_r - 1):  # iterate radial points
                arr_z_l, arr_c, arr_z_h = region_z(arr, (i, j))
                arr_r_l, arr_r_h = arr[i - 1, j], arr[i + 1, j]
                out[i, j] = (
                    (arr_r_h - 2 * arr_c + arr_r_l) * dr_2 +
                    (arr_r_h - arr_r_l) / (2 * i + 1) * dr_2 +
                    (arr_z_l - 2 * arr_c + arr_z_h) * dz_2
                )
                
            # outer radial boundary condition
            i = dim_r - 1
            arr_z_l, arr_c, arr_z_h = region_z(arr, (i, j))
            arr_r_l, arr_r_h = arr[i - 1, j], value_outer(arr, (i, j))
            out[i, j] = (
                (arr_r_h - 2 * arr_c + arr_r_l) * dr_2 +
                (arr_r_h - arr_r_l) / (2 * i + 1) * dr_2 +
                (arr_z_l - 2 * arr_c + arr_z_h) * dz_2
            )
        return out
        
    return laplace  # type: ignore



def make_gradient(bcs: Boundaries) -> Callable:
    """ make a discretized gradient operator for a cylindrical grid
    
    |Description_cylindrical|

    Args:
        bcs (:class:`~pde.grids.boundaries.axes.Boundaries`):
            |Arg_boundary_conditions|
        
    Returns:
        A function that can be applied to an array of values
    """
    assert isinstance(bcs.grid, CylindricalGrid)
    bcs.check_value_rank(0)
    boundary_r, boundary_z = bcs

    # calculate preliminary quantities
    dim_r, dim_z = bcs.grid.shape
    scale_r, scale_z = 1 / (2 * bcs.grid.discretization)
    
    value_outer = boundary_r.high.get_virtual_point_evaluator()
    region_z = boundary_z.get_region_evaluator()

    # use processing for large enough arrays 
    parallel = (dim_r * dim_z >= PARALLELIZATION_THRESHOLD_2D**2)

    @jit_allocate_out(parallel=parallel, out_shape=(3, dim_r, dim_z))
    def gradient(arr, out=None):
        """ apply gradient operator to array `arr` """
        for j in nb.prange(0, dim_z):  # iterate axial points
            # inner radial boundary condition
            i = 0
            arr_z_l, _, arr_z_h = region_z(arr, (i, j))
            out[0, i, j] = (arr[1, i] - arr[0, i]) * scale_r
            out[1, i, j] = (arr_z_h - arr_z_l) * scale_z
            out[2, i, j] = 0  # no phi dependence by definition
            
            for i in range(1, dim_r - 1):  # iterate radial points
                arr_z_l, _, arr_z_h = region_z(arr, (i, j))
                out[0, i, j] = (arr[i + 1, j] - arr[i - 1, j]) * scale_r
                out[1, i, j] = (arr_z_h - arr_z_l) * scale_z
                out[2, i, j] = 0  # no phi dependence by definition
                
            # outer radial boundary condition
            i = dim_r - 1
            arr_z_l, _, arr_z_h = region_z(arr, (i, j))
            arr_r_h = value_outer(arr, (i, j))
            out[0, i, j] = (arr_r_h - arr[i - 1, j]) * scale_r
            out[1, i, j] = (arr_z_h - arr_z_l) * scale_z
            out[2, i, j] = 0  # no phi dependence by definition
            
        return out
        
    return gradient  # type: ignore



def make_divergence(bcs: Boundaries) -> Callable:
    """ make a discretized divergence operator for a cylindrical grid
    
    |Description_cylindrical|

    Args:
        bcs (:class:`~pde.grids.boundaries.axes.Boundaries`):
            |Arg_boundary_conditions|
        
    Returns:
        A function that can be applied to an array of values
    """
    assert isinstance(bcs.grid, CylindricalGrid)
    bcs.check_value_rank(0)
    boundary_r, boundary_z = bcs

    # calculate preliminary quantities
    dim_r, dim_z = bcs.grid.shape
    dr = bcs.grid.discretization[0]
    scale_r, scale_z = 1 / (2 * bcs.grid.discretization)
    
    value_outer = boundary_r.high.get_virtual_point_evaluator()
    region_z = boundary_z.get_region_evaluator()

    # use processing for large enough arrays 
    parallel = (dim_r * dim_z >= PARALLELIZATION_THRESHOLD_2D**2)

    @jit_allocate_out(parallel=parallel, out_shape=(dim_r, dim_z))
    def divergence(arr, out=None):
        """ apply divergence operator to array `arr` """            
        for j in nb.prange(0, dim_z):  # iterate axial points
            # inner radial boundary condition
            i = 0
            arr_z_l, _, arr_z_h = region_z(arr[1], (i, j))
            d_r = (arr[0, 1, j] + 3 * arr[0, 0, j]) * scale_r
            d_z = (arr_z_h - arr_z_l) * scale_z
            out[i, j] = d_r + d_z
            
            for i in range(1, dim_r - 1):  # iterate radial points
                arr_z_l, _, arr_z_h = region_z(arr[1], (i, j))
                d_r = (arr[0, i + 1, j] - arr[0, i - 1, j]) * scale_r + \
                      (arr[0, i, j] / ((i + 0.5) * dr))
                d_z = (arr_z_h - arr_z_l) * scale_z
                out[i, j] = d_r + d_z
                
            # outer radial boundary condition
            i = dim_r - 1
            arr_z_l, _, arr_z_h = region_z(arr[1], (i, j))
            arr_r_h = value_outer(arr[0], (i, j))
            d_r = (arr_r_h - arr[0, i - 1, j]) * scale_r + \
                  (arr[0, i, j] / ((i + 0.5) * dr))
            d_z = (arr_z_h - arr_z_l) * scale_z
            out[i, j] = d_z + d_r
            
        return out
        
    return divergence  # type: ignore



def make_vector_gradient(bcs: Boundaries) -> Callable:
    """ make a discretized vector gradient operator for a cylindrical grid
    
    |Description_cylindrical|

    Args:
        bcs (:class:`~pde.grids.boundaries.axes.Boundaries`):
            |Arg_boundary_conditions|
        
    Returns:
        A function that can be applied to an array of values
    """
    assert isinstance(bcs.grid, CylindricalGrid)
    bcs.check_value_rank(1)

    # calculate preliminary quantities
    gradient_r = make_gradient(bcs.extract_component(0))
    gradient_z = make_gradient(bcs.extract_component(1))
    gradient_phi = make_gradient(bcs.extract_component(2))
        
    @jit_allocate_out(out_shape=(3, 3) + bcs.grid.shape)
    def vector_gradient(arr, out=None):
        """ apply gradient operator to array `arr` """
        gradient_r(arr[0], out=out[:, 0])
        gradient_z(arr[1], out=out[:, 1])
        gradient_phi(arr[2], out=out[:, 2])
        return out    
        
    return vector_gradient  # type: ignore



def make_vector_laplace(bcs: Boundaries) -> Callable:
    """ make a discretized vector laplace operator for a cylindrical grid
    
    |Description_cylindrical|

    Args:
        bcs (:class:`~pde.grids.boundaries.axes.Boundaries`):
            |Arg_boundary_conditions|
        
    Returns:
        A function that can be applied to an array of values
    """
    assert isinstance(bcs.grid, CylindricalGrid)
    bcs.check_value_rank(1)

    laplace_r = make_laplace(bcs.extract_component(0))
    laplace_z = make_laplace(bcs.extract_component(1))
    laplace_phi = make_laplace(bcs.extract_component(2))
        
    @jit_allocate_out(out_shape=(3,) + bcs.grid.shape)
    def vector_laplace(arr, out=None):
        """ apply gradient operator to array `arr` """
        laplace_r(arr[0], out=out[0])
        laplace_z(arr[1], out=out[1])
        laplace_phi(arr[2], out=out[2])
        return out    
        
    return vector_laplace  # type: ignore



def make_tensor_divergence(bcs: Boundaries) -> Callable:
    """ make a discretized tensor divergence operator for a cylindrical grid
    
    |Description_cylindrical|

    Args:
        bcs (:class:`~pde.grids.boundaries.axes.Boundaries`):
            |Arg_boundary_conditions|
        
    Returns:
        A function that can be applied to an array of values
    """
    assert isinstance(bcs.grid, CylindricalGrid)
    bcs.check_value_rank(1)

    divergence_r = make_divergence(bcs.extract_component(0))
    divergence_z = make_divergence(bcs.extract_component(1))
    divergence_phi = make_divergence(bcs.extract_component(2))
        
    @jit_allocate_out(out_shape=(3,) + bcs.grid.shape)
    def tensor_divergence(arr, out=None):
        """ apply gradient operator to array `arr` """
        divergence_r(arr[0], out=out[0])
        divergence_z(arr[1], out=out[1])
        divergence_phi(arr[2], out=out[2])
        return out
        
    return tensor_divergence  # type: ignore



def make_operator(op: str, bcs: Boundaries) -> Callable:
    """ make a discretized operator for a cylindrical grid
    
    |Description_cylindrical|

    Args:
        op (str): Identifier for the operator. Some examples are 'laplace',
            'gradient', or 'divergence'.
        bcs (:class:`~pde.grids.boundaries.axes.Boundaries`):
            |Arg_boundary_conditions|

    Returns:
        A function that takes the discretized data as an input and returns
        the data to which the operator `op` has been applied. This function
        optionally supports a second argument, which provides allocated
        memory for the output.
    """
    if op == 'laplace' or op == 'laplacian':
        return make_laplace(bcs)
    elif op == 'gradient':
        return make_gradient(bcs)
    elif op == 'divergence':
        return make_divergence(bcs)
    elif op == 'vector_gradient':
        return make_vector_gradient(bcs)
    elif op == 'tensor_divergence':
        return make_tensor_divergence(bcs)
    else:
        raise NotImplementedError(f'Operator `{op}` is not defined for '
                                  'cylindrical grids')
    
