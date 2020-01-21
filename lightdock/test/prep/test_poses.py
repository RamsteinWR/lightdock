"""Tests for poses related module"""

import os
import shutil
import filecmp
import numpy as np
from nose.tools import assert_almost_equal
from lightdock.prep.poses import normalize_vector, quaternion_from_vectors, get_quaternion_for_restraint, \
        get_random_point_within_sphere, estimate_membrane, upper_layer
from lightdock.mathutil.cython.quaternion import Quaternion
from lightdock.structure.residue import Residue
from lightdock.mathutil.lrandom import MTGenerator


class TestPoses:

    def setUp(self):
        self.path = os.path.dirname(os.path.realpath(__file__))
        self.test_path = self.path + '/scratch_poses/'
        try:
            shutil.rmtree(self.test_path)
        except:
            pass
        os.mkdir(self.test_path)
        self.golden_data_path = os.path.normpath(os.path.dirname(os.path.realpath(__file__))) + '/golden_data/'

    def tearDown(self):
        try:
            shutil.rmtree(self.test_path)
        except:
            pass
    
    def test_normalize_vector1(self):
        v = np.array([1., 0., 0.])
        e = np.array([1., 0., 0.])
        n = normalize_vector(v)
        assert np.allclose(n, e)

    def test_normalize_vector2(self):
        v = np.array([4., 0., 0.])
        e = np.array([1., 0., 0.])
        n = normalize_vector(v)
        assert np.allclose(n, e)

    def test_normalize_vector3(self):
        v = np.array([0., 0., 0.])
        e = np.array([0., 0., 0.])
        n = normalize_vector(v)
        assert np.allclose(n, e)

    def test_normalize_vector4(self):
        v = np.array([2., -2., 0.])
        e = np.array([0.70710678, -0.70710678, 0.])
        n = normalize_vector(v)
        assert np.allclose(n, e)

    def test_quaternion_from_vectors1(self):
        a = np.array([1., 0., 0.])
        b = np.array([1., 0., 0.])
        q = quaternion_from_vectors(a, b)
        e = Quaternion()
        assert e == q

    def test_quaternion_from_vectors2(self):
        a = np.array([1., 0., 0.])
        b = np.array([2., 0., 0.])
        q = quaternion_from_vectors(a, b)
        e = Quaternion()
        assert e == q

    def test_quaternion_from_vectors3(self):
        a = np.array([1., 0., 0.])
        b = np.array([0., 2., 0.])
        q = quaternion_from_vectors(a, b)
        # 90 degrees in Z axis
        e = Quaternion(w=0.70710678, x=0., y=0., z=0.70710678)
        assert e == q

    def test_quaternion_from_vectors4(self):
        a = np.array([1., 0., 0.])
        b = np.array([-1., 0., 0.])
        q = quaternion_from_vectors(a, b)
        # Orthogonal rotation, two possibilities:
        e1 = Quaternion(w=0., x=0., y=1.0, z=0.)
        e2 = Quaternion(w=0., x=0., y=-1.0, z=0.)
        assert e1 == q or e2 == q

    def test_get_quaternion_for_restraint1(self):
        # Origin is 0,0,0
        # Ligand center
        l_center = [-5., 5., -5.]
        # Ligand residue
        l_res = [-7., 7., -7.]
        # Receptor residue
        r_res = [3., 1., 0.]
        # Calculate quaternion for rotation from l_res to point to r_res
        rec_residue = Residue.dummy(r_res[0], r_res[1], r_res[2])
        lig_residue = Residue.dummy(l_res[0], l_res[1], l_res[2])

        q = get_quaternion_for_restraint(rec_residue, lig_residue,
                                         l_center[0], l_center[1], l_center[2], # translation
                                         [0., 0., 0.], # receptor translation 
                                         [5., -5., 5.] # ligand translation
                                         )

        e = Quaternion(w=0.14518697, x=0.19403814, y=-0.58211441, z=-0.77615254)

        assert e == q

    def test_get_quaternion_for_restraint2(self):
        # Origin is 0,0,0
        # Ligand center
        l_center = [-5., 5., -5.]
        # Ligand residue
        l_res = [-7., 6., -7.]
        # Receptor residue
        r_res = [3., 1., 0.]
        # Calculate quaternion for rotation from l_res to point to r_res
        rec_residue = Residue.dummy(r_res[0], r_res[1], r_res[2])
        lig_residue = Residue.dummy(l_res[0], l_res[1], l_res[2])

        q = get_quaternion_for_restraint(rec_residue, lig_residue,
                                         l_center[0], l_center[1], l_center[2], # translation
                                         [0., 0., 0.], # receptor translation 
                                         [5., -5., 5.] # ligand translation
                                         )

        e = Quaternion(0.10977233, -0.44451098, -0.88902195, 0.)

        assert e == q

    def test_get_quaternion_for_restraint2d(self):
        # Origin is 0,0,0
        # Ligand center
        l_center = [5., 5., 0.]
        # Ligand residue
        l_res = [7., 7., 0.]
        # Receptor residue
        r_res = [3., 1., 0.]
        # Calculate quaternion for rotation from l_res to point to r_res
        rec_residue = Residue.dummy(r_res[0], r_res[1], r_res[2])
        lig_residue = Residue.dummy(l_res[0], l_res[1], l_res[2])

        q = get_quaternion_for_restraint(rec_residue, lig_residue,
                                         l_center[0], l_center[1], l_center[2], # translation
                                         [0., 0., 0.], # receptor translation 
                                         [5., 5., 0.] # ligand translation
                                         )

        e = Quaternion(0.16018224, 0., 0., -0.98708746)

        assert e == q

    def test_get_quaternion_for_restraint2d_different_quadrant(self):
        # Origin is 0,0,0
        # Ligand center
        l_center = [5., -5., 0.]
        # Ligand residue
        l_res = [7., -7., 0.]
        # Receptor residue
        r_res = [-3., 1., 0.]
        # Calculate quaternion for rotation from l_res to point to r_res
        rec_residue = Residue.dummy(r_res[0], r_res[1], r_res[2])
        lig_residue = Residue.dummy(l_res[0], l_res[1], l_res[2])

        q = get_quaternion_for_restraint(rec_residue, lig_residue,
                                         l_center[0], l_center[1], l_center[2], # translation
                                         [0., 0., 0.], # receptor translation 
                                         [5., -5., 0.] # ligand translation
                                         )

        e = Quaternion(0.07088902, 0., 0., -0.99748421)

        assert e == q

    def test_get_random_point_within_sphere(self):
        seed = 1984
        rng = MTGenerator(seed)
        to_generate = 10
        radius = 10.0

        points = [get_random_point_within_sphere(rng, radius) for _ in range(to_generate)]

        # Check all generated points are within a sphere of a given radius and
        # centered at the origin
        for p in points:
            assert p[0] <= radius and p[0] >= -radius
            assert p[1] <= radius and p[1] >= -radius
            assert p[2] <= radius and p[2] >= -radius

    def test_estimate_membrane(self):
        seed = 1984
        np.random.seed(seed)
        z_coordinates_two_layers = np.random.rand(10, 3) * 30
        z_coordinates_two_layers[::2][:,2] *= -1

        layers = estimate_membrane(z_coordinates_two_layers[:,2], 15.)

        assert len(layers) == 2

        z_coordinates_one_layer = np.random.rand(10, 3) * 30

        layers = estimate_membrane(z_coordinates_one_layer[:,2])

        assert len(layers) == 1

    def test_upper_layer(self):
        seed = 1984
        np.random.seed(seed)
        z_coordinates_two_layers = np.random.rand(10, 3) * 30
        z_coordinates_two_layers[::2][:,2] *= -1
        expected = np.array([14.865534412778462, 19.42594208380253, 21.84073297851065, 23.828220097290853, 23.927022857098866])
        
        layers = estimate_membrane(z_coordinates_two_layers[:,2], 15.)

        upper = upper_layer(layers)
        
        assert np.allclose(upper, expected)
