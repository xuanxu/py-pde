'''
.. codeauthor:: David Zwicker <david.zwicker@ds.mpg.de>
'''

import pytest
import numpy as np

from .. import polar as ops
from ... import PolarGrid, CartesianGrid
from ....fields import ScalarField, VectorField, Tensor2Field


    
def test_findiff():
    """ test operator for a simple polar grid """
    grid = PolarGrid(1.5, 3)
    _, _, r2 = grid.axes_coords[0]
    assert grid.discretization == (0.5,)
    s = ScalarField(grid, [1, 2, 4]) 
    v = VectorField(grid, [[1, 2, 4], [0]*3]) 

    # test gradient
    grad = s.gradient(bc='value')
    np.testing.assert_allclose(grad.data[0, :], [1, 3, -6])
    grad = s.gradient(bc='derivative')
    np.testing.assert_allclose(grad.data[0, :], [1, 3, 2])

    # test divergence        
    div = v.divergence(bc='value')
    np.testing.assert_allclose(div.data, [5, 17 / 3, -6 + 4/r2])
    div = v.divergence(bc='derivative')
    np.testing.assert_allclose(div.data, [5, 17 / 3, 2 + 4/r2])
    
    
    
def test_conservative_laplace():
    """ test and compare the two implementation of the laplace operator """
    grid = PolarGrid(1.5, 8)
    f = ScalarField.random_uniform(grid)
    
    bcs = grid.get_boundary_conditions('natural')
    lap = ops.make_laplace(bcs)
    np.testing.assert_allclose(f.apply(lap).integral, 0, atol=1e-12)
    
    
    
@pytest.mark.parametrize('make_op,field', [(ops.make_laplace, ScalarField),
                                           (ops.make_divergence, VectorField),
                                           (ops.make_gradient, ScalarField),
                                           (ops.make_tensor_divergence,
                                            Tensor2Field)])
def test_small_annulus(make_op, field):
    """ test whether a small annulus gives the same result as a sphere """
    grids = [PolarGrid((0, 1), 8),
             PolarGrid((1e-8, 1), 8),
             PolarGrid((0.1, 1), 8)]
    
    f = field.random_uniform(grids[0])
    
    res = [make_op(g.get_boundary_conditions())(f.data) for g in grids]
    
    np.testing.assert_almost_equal(res[0], res[1], decimal=5)
    assert np.linalg.norm(res[0] - res[2]) > 1e-3    



def test_grid_laplace():
    """ test the polar implementation of the laplace operator """
    grid_sph = PolarGrid(10, 11)
    grid_cart = CartesianGrid([[-5, 5], [-5, 5]], [12, 11]) 
     
    a_1d = np.cos(grid_sph.axes_coords[0])
    a_2d = grid_sph.interpolate_to_cartesian(a_1d, grid=grid_cart)

    b_2d = grid_cart.get_operator('laplace', 'no-flux')(a_2d)
    b_1d = grid_sph.get_operator('laplace', 'no-flux')(a_1d)
    b_1d_2 = grid_sph.interpolate_to_cartesian(b_1d, grid=grid_cart)
     
    i = slice(1, -1)  # do not compare boundary points
    np.testing.assert_allclose(b_1d_2[i, i], b_2d[i, i], rtol=0.2, atol=0.2)
     
     
     
def test_grid_div_grad():
    """ compare div grad to laplacian for polar grids """
    grid = PolarGrid(2*np.pi, 16)
    r = grid.axes_coords[0]
    arr = np.cos(r)

    laplace = grid.get_operator('laplace', 'no-flux')
    grad = grid.get_operator('gradient', 'no-flux')
    div = grid.get_operator('divergence', 'value')
    a = laplace(arr)
    b = div(grad(arr))
    res = -np.sin(r) / r - np.cos(r) 
     
    # do not test the radial boundary points
    np.testing.assert_allclose(a[1:-1], res[1:-1], rtol=0.1, atol=0.1)
    np.testing.assert_allclose(b[1:-1], res[1:-1], rtol=0.1, atol=0.1)

