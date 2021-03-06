"""
The Swift-Hohenberg equation

.. codeauthor:: David Zwicker <david.zwicker@ds.mpg.de> 
"""

from typing import (Callable, Dict, Any, Counter, List)  # @UnusedImport

import numpy as np


from .base import PDEBase
from ..fields import ScalarField
from ..grids.boundaries.axes import BoundariesData
from ..tools.numba import nb, jit


        
class SwiftHohenbergPDE(PDEBase):
    r""" The Swift-Hohenberg equation defined as
    
    .. math::
        \partial_t c = 
            \left[\epsilon - \left(k_c^2 + \nabla^2\right)^2\right] c
            + \delta \, c^2 - c^3
        
    where :math:`c` is a scalar field and :math:`\epsilon`, :math:`k_c^2`, and
    :math:`\delta` are parameters of the equation.
    """

    explicit_time_dependence = False


    def __init__(self,
                 rate: float = .1,
                 kc2: float = 1.,
                 delta: float = 1.,
                 bc: BoundariesData = 'natural', 
                 bc_lap: BoundariesData = None):
        r""" 
        Args:
            rate (float):
                The bifurcation parameter :math:`\epsilon`
            kc2 (float):
                Squared wave vector :math:`k_c^2` of the linear instability
            delta (float):
                Parameter :math:`\delta` of the non-linearity
            bc:
                The boundary conditions applied to the scalar field :math:`c`.
                The default value ('natural') imposes periodic boundary
                conditions for axes in which the grid is periodic and vanishing
                derivatives for all other axes. Alternatively, specific boundary
                conditions can be set for all axes individually. 
            bc_lap:
                The boundary conditions applied to the second derivative of the
                scalar field :math:`c`. If `None`, the same 
        """
        super().__init__()
        
        self.rate = rate
        self.kc2 = kc2
        self.delta = delta
        self.bc = bc
        self.bc_lap = bc if bc_lap is None else bc_lap
            
            
    def evolution_rate(self, state: ScalarField,  # type: ignore
                       t: float = 0) -> ScalarField:
        """ evaluate the right hand side of the PDE
        
        Args:
            state (:class:`~pde.fields.ScalarField`):
                The scalar field describing the concentration distribution
            t (float): The current time point
            
        Returns:
            :class:`~pde.fields.ScalarField`:
            Scalar field describing the evolution rate of the PDE 
        """
        assert isinstance(state, ScalarField)
        state_laplace = state.laplace(bc=self.bc)
        state_laplace2 = state_laplace.laplace(bc=self.bc_lap)
        
        result = ((self.rate - self.kc2**2) * state
                  - 2 * self.kc2 * state_laplace
                  - state_laplace2
                  + self.delta * state**2 - state**3)
        result.label = 'evolution rate'
        return result  # type: ignore
     
     
    def _make_pde_rhs_numba(self, state: ScalarField  # type: ignore
                            ) -> Callable:
        """ create a compiled function evaluating the right hand side of the PDE
          
        Args:
            state (:class:`~pde.fields.ScalarField`):
                An example for the state defining the grid and data types
                  
        Returns:
            A function with signature `(state_data, t)`, which can be called
            with an instance of :class:`numpy.ndarray` of the state data and
            the time to obtained an instance of :class:`numpy.ndarray` giving
            the evolution rate.  
        """
        shape = state.grid.shape
        arr_type = nb.typeof(np.empty(shape, dtype=np.double))
        signature = arr_type(arr_type, nb.double)
          
        rate = self.rate
        kc2 = self.kc2
        delta = self.delta
        
        laplace = state.grid.get_operator('laplace', bc=self.bc)
        laplace2 = state.grid.get_operator('laplace', bc=self.bc_lap)
  
        @jit(signature)
        def pde_rhs(state_data: np.ndarray, t: float):
            """ compiled helper function evaluating right hand side """ 
            state_laplace = laplace(state_data)
            state_laplace2 = laplace2(state_laplace)
              
            return ((rate - kc2**2) * state_data
                    - 2 * kc2 * state_laplace
                    - state_laplace2
                    + delta * state_data**2 - state_data**3)
              
        return pde_rhs  # type: ignore
      
