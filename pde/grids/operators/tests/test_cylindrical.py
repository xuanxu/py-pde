'''
.. codeauthor:: David Zwicker <david.zwicker@ds.mpg.de>
'''

import numpy as np

from .. import cylindrical as ops
from ... import CylindricalGrid, CartesianGrid
from ....fields import ScalarField, VectorField



def test_laplace_cyl():
    """ test the implementation of the laplace operator """
    for boundary_z in ['periodic', 'no-flux']:
        grid = CylindricalGrid(4, (0, 5), (8, 16),
                               periodic_z=(boundary_z == 'periodic'))
        a_2d = np.random.uniform(0, 1, grid.shape)

        bcs = grid.get_boundary_conditions(['no-flux', boundary_z])
        lap_2d = ops.make_laplace(bcs)
        b_2d = lap_2d(a_2d)
        assert b_2d.shape == grid.shape
        
        
        
def test_laplacian_field_cyl():
    """ test the gradient operator """
    grid = CylindricalGrid(2 * np.pi, [0, 2 * np.pi], [8, 16],
                           periodic_z=True)
    r, z = grid.cell_coords[..., 0], grid.cell_coords[..., 1]
    s = ScalarField(grid, data=np.cos(r) + np.sin(z))
    s_lap = s.laplace(bc='natural')
    assert s_lap.data.shape == (8, 16)
    res = -np.cos(r) - np.sin(r) / r - np.sin(z)
    np.testing.assert_allclose(s_lap.data, res, rtol=0.1, atol=0.1)



def test_gradient_field_cyl():
    """ test the gradient operator"""
    grid = CylindricalGrid(2 * np.pi, [0, 2 * np.pi], [8, 16],
                           periodic_z=True)
    r, z = grid.cell_coords[..., 0], grid.cell_coords[..., 1]
    s = ScalarField(grid, data=np.cos(r) + np.sin(z))
    v = s.gradient(bc='natural')
    assert v.data.shape == (3, 8, 16)
    np.testing.assert_allclose(v.data[0], -np.sin(r), rtol=0.1, atol=0.1)
    np.testing.assert_allclose(v.data[1], np.cos(z), rtol=0.1, atol=0.1)
    np.testing.assert_allclose(v.data[2], 0, rtol=0.1, atol=0.1)
     
     
     
def test_divergence_field_cyl():
    """ test the divergence operator """
    grid = CylindricalGrid(2 * np.pi, [0, 2 * np.pi], [8, 16],
                           periodic_z=True)
    r, z = grid.cell_coords[..., 0], grid.cell_coords[..., 1]
    data = [np.cos(r) + np.sin(z)**2,
            np.cos(r)**2 + np.sin(z),
            np.zeros_like(r)]
    v = VectorField(grid, data=data)
    s = v.divergence(bc='natural')
    assert s.data.shape == (8, 16)
    res = np.cos(z) - np.sin(r) + (np.cos(r) + np.sin(z)**2) / r
    np.testing.assert_allclose(s.data, res, rtol=0.1, atol=0.1)
     
     
    
def test_vector_gradient_divergence_field_cyl():
    """ test the divergence operator """
    grid = CylindricalGrid(2 * np.pi, [0, 2 * np.pi], [8, 16],
                           periodic_z=True)
    r, z = grid.cell_coords[..., 0], grid.cell_coords[..., 1]
    data = [np.cos(r) + np.sin(z)**2,
            np.cos(r)**2 + np.sin(z),
            np.zeros_like(r)]
    v = VectorField(grid, data=data)
    t = v.gradient(bc='natural')
    assert t.data.shape == (3, 3, 8, 16)
    v = t.divergence(bc='natural')
    assert v.data.shape == (3, 8, 16)
    
    

def test_findiff_cyl():
    """ test operator for a simple cylindrical grid. Note that we only
    really test the polar symmetry """
    grid = CylindricalGrid(1.5, [0, 1], (3, 2), periodic_z=True)
    _, r1, r2 = grid.axes_coords[0]
    np.testing.assert_array_equal(grid.discretization, np.full(2, 0.5))
    s = ScalarField(grid, [[1, 1], [2, 2], [4, 4]]) 
    v = VectorField(grid, [[[1, 1], [2, 2], [4, 4]],
                           [[0, 0]]*3, [[0, 0]]*3]) 

    # test gradient        
    grad = s.gradient(bc=['value', 'periodic'])
    np.testing.assert_allclose(grad.data[0], [[1, 1], [3, 3], [-6, -6]])
    grad = s.gradient(bc=['derivative', 'periodic'])
    np.testing.assert_allclose(grad.data[0], [[1, 1], [3, 3], [2, 2]])

    # test divergence        
    div = v.divergence(bc=['value', 'periodic'])
    y1 = 3 + 2/r1
    y2 = -6 + 4/r2
    np.testing.assert_allclose(div.data, [[5, 5], [y1, y1], [y2, y2]])
    div = v.divergence(bc=['derivative', 'periodic'])
    y2 = 2 + 4/r2
    np.testing.assert_allclose(div.data, [[5, 5], [y1, y1], [y2, y2]])
    
    # test laplace
    lap = s.laplace(bc=[{'type': 'value', 'value': 3}, 'periodic'])
    y1 = 4 + 3/r1
    y2 = -16
    np.testing.assert_allclose(lap.data, [[8, 8], [y1, y1], [y2, y2]])
    lap = s.laplace(bc=[{'type': 'derivative', 'value': 3}, 'periodic'])
    y2 = -2 + 3.5/r2
    np.testing.assert_allclose(lap.data, [[8, 8], [y1, y1], [y2, y2]])
    
    
    
def test_grid_laplace():
    """ test the cylindrical implementation of the laplace operator """
    grid_cyl = CylindricalGrid(5, (0, 4), (6, 4))
    grid_cart = CartesianGrid([[-5, 5], [-5, 5], [0, 4]], [10, 10, 4]) 
     
    rs, zs = np.meshgrid(*grid_cyl.axes_coords, indexing='ij')
    a_2d = np.exp(-5 * rs) * np.cos(zs / 3)
    a_3d = grid_cyl.interpolate_to_cartesian(a_2d, grid=grid_cart)

    b_3d = grid_cart.get_operator('laplace', 'natural')(a_3d)
    b_2d = grid_cyl.get_operator('laplace', 'natural')(a_2d)
    b_2d_3 = grid_cyl.interpolate_to_cartesian(b_2d, grid=grid_cart)
     
    np.testing.assert_allclose(b_2d_3, b_3d, rtol=0.2, atol=0.2)
     
     
     
def test_grid_div_grad():
    """ compare div grad to laplacian """
    grid = CylindricalGrid(2*np.pi, (0, 2*np.pi), (16, 16), periodic_z=True)
    r, z = grid.cell_coords[..., 0], grid.cell_coords[..., 1]
    arr = np.cos(r) + np.sin(z)

    bcs = grid.get_boundary_conditions()
    laplace = grid.get_operator('laplace', bcs)
    grad = grid.get_operator('gradient', bcs)
    div = grid.get_operator('divergence', bcs.differentiated)
    a = laplace(arr)
    b = div(grad(arr))
    res = (-np.sin(r) / r - np.cos(r)) - np.sin(z) 
    # do not test the radial boundary points
    np.testing.assert_allclose(a[1:-1], res[1:-1], rtol=0.1, atol=0.05)
    np.testing.assert_allclose(b[1:-1], res[1:-1], rtol=0.1, atol=0.05)
