import numpy as np

from random_walk import random_walk, geometric_random_walk

assert_func = np.testing.assert_allclose
relative_tolerance = 0
absolute_tolerance = 1e-8

def test_random_walk():
    np.random.seed(123)
    actual = random_walk(5, 2, mu=0, std=0.01)
    desired = np.array([[ 0.        ,  0.        ],
        [ 0.00282978, -0.01506295],
        [-0.00295622,  0.00145142],
        [-0.02722301, -0.00283771],
        [-0.01456365, -0.01150511]])
    assert_func(actual, desired, rtol=relative_tolerance, atol=absolute_tolerance)


def test_random_walk_default_args():
    np.random.seed(123)
    actual = random_walk(5, 2)
    desired = np.array([[ 0.        ,  0.        ],
        [ 0.00282978, -0.01506295],
        [-0.00295622,  0.00145142],
        [-0.02722301, -0.00283771],
        [-0.01456365, -0.01150511]])
    assert_func(actual, desired, rtol=relative_tolerance, atol=absolute_tolerance)

def test_geometric_walk():
    np.random.seed(123)
    actual = geometric_random_walk(5, 2, mu=1, alpha=0.01)
    desired = np.array([[1.        , 1.        ],
        [0.99453703, 1.0010263 ],
        [0.99890243, 0.99948685],
        [1.00850716, 1.00318154],
        [1.00812255, 1.00101703]])
    assert_func(actual, desired, rtol=relative_tolerance, atol=absolute_tolerance)

def test_geometric_walk_default_args():
    np.random.seed(123)
    actual = geometric_random_walk(5, 2)
    desired = np.array([[1.        , 1.        ],
        [0.99453703, 1.0010263 ],
        [0.99890243, 0.99948685],
        [1.00850716, 1.00318154],
        [1.00812255, 1.00101703]])
    assert_func(actual, desired, rtol=relative_tolerance, atol=absolute_tolerance)
