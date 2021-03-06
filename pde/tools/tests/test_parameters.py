'''
.. codeauthor:: David Zwicker <david.zwicker@ds.mpg.de>
'''

import itertools

import pytest

from ..parameters import (Parameter, DeprecatedParameter, ObsoleteParameter,
                          Parameterized, get_all_parameters)



def test_parameters():
    """ test mixing Parameterized """
    
    class Test1(Parameterized):
        parameters_default = [Parameter('a', 1, int, "help")]
        
        
    t = Test1()
    assert t.parameters['a'] == 1
    assert t.get_parameter_default('a') == 1

    t = Test1(parameters={'a': 2})
    assert t.parameters['a'] == 2
    assert t.get_parameter_default('a') == 1
    
    with pytest.raises(ValueError):
        t = Test1(parameters={'b': 1})
    t = Test1(parameters={'b': 1}, check_validity=False)
    assert t.parameters['a'] == 1
    assert t.parameters['b'] == 1
    
    
    class Test2(Test1):
        # also test conversion of default parameters
        parameters_default = [Parameter('b', '2', int, "help")]
        
    t = Test2()
    assert t.parameters['a'] == 1
    assert t.parameters['b'] == 2
    
    t = Test2(parameters={'a': 10, 'b': 20})
    assert t.parameters['a'] == 10
    assert t.parameters['b'] == 20
    assert t.get_parameter_default('a') == 1
    assert t.get_parameter_default('b') == '2'
    with pytest.raises(KeyError):
        t.get_parameter_default('c')
        
    class Test3(Test2):
        # test overwriting defaults
        parameters_default = [Parameter('a', 3), Parameter('c', 4)]
        
    t = Test3()
    assert t.parameters['a'] == 3
    assert t.get_parameter_default('a') == 3
    assert set(t.parameters.keys()) == {'a', 'b', 'c'}
        
        
        
def test_parameter_help(capsys):
    """ test how parameters are shown """
    class Test1(Parameterized):
        parameters_default = [DeprecatedParameter('a', 1, int, "random string")]
        
    class Test2(Test1):
        parameters_default = [Parameter('b', 2, int, "another word")]
        
    t = Test2()
    for flags in itertools.combinations_with_replacement([True, False], 3):
        Test2.show_parameters(*flags)
        o1, e1 = capsys.readouterr()
        t.show_parameters(*flags)
        o2, e2 = capsys.readouterr()
        assert o1 == o2
        assert e1 == e2 == ''
    
    
    
def test_obsolete_parameter():
    """ test how parameters are shown """
    class Test1(Parameterized):
        parameters_default = [Parameter('a', 1), Parameter('b', 2)]
         
    class Test2(Test1):
        parameters_default = [ObsoleteParameter('b')]
        
    class Test3(Test1):
        parameters_default = [Parameter('b', 3)]
        
    assert Test1().parameters == {'a': 1, 'b': 2}
    assert Test2().parameters == {'a': 1}
    assert Test3().parameters == {'a': 1, 'b': 3}
    
    
    
def test_get_all_parameters():
    """ test the get_all_parameters function """
    p1 = get_all_parameters()
    for key in ['value', 'description']:
        p2 = get_all_parameters(key)
        assert set(p1) == p2.keys()
    
    