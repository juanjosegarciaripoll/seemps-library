import unittest
import numpy as np
from seemps.state import TensorArray, MPS, MPSSum
from .tools import *
from .fixture_mps_states import MPSStatesFixture


class TestTensorArray(MPSStatesFixture):
    def test_initial_data_is_copied(self):
        data = self.product_state.copy()
        A = TensorArray(data)
        A[::] = self.other_tensor
        self.assertTrue(contain_different_objects(A, data))

    def test_copy_creates_independent_object(self):
        A = TensorArray(self.product_state.copy())
        B = A.copy()
        A[::] = self.other_tensor
        self.assertTrue(contain_different_objects(A, B))

    def test_copy_references_same_tensors(self):
        A = TensorArray(self.product_state)
        self.assertTrue(contain_same_objects(A, self.product_state))


class TestMPS(MPSStatesFixture):
    def test_initial_data_is_copied(self):
        data = self.product_state.copy()
        A = MPS(data)
        A[::] = self.other_tensor
        self.assertTrue(contain_different_objects(A, data))

    def test_copy_creates_independent_object(self):
        A = MPS(self.product_state.copy())
        B = A.copy()
        A[::] = self.other_tensor
        self.assertTrue(contain_different_objects(A, B))

    def test_copy_references_same_tensors(self):
        A = MPS(self.product_state)
        self.assertTrue(contain_same_objects(A, self.product_state))

    def test_total_dimension_is_product_of_physical_dimensions(self):
        A = MPS(self.inhomogeneous_state)
        self.assertEqual(A.dimension(), self.inhomogeneous_state_dimension)

    def test_to_vector_creates_correct_wavefunction(self):
        A = MPS(self.inhomogeneous_state)
        ψ = A.to_vector()
        self.assertEqual(ψ.shape, (self.inhomogeneous_state_dimension,))
        self.assertTrue(similar(ψ, self.inhomogeneous_state_wavefunction))

    def test_from_vector_recreates_product_states(self):
        A = MPS.from_vector(
            self.inhomogeneous_state_wavefunction, [2, 3, 4], normalize=False
        )
        self.assertTrue(
            all(a.shape == b.shape for a, b in zip(A, self.inhomogeneous_state))
        )
        self.assertTrue(similar(A.to_vector(), self.inhomogeneous_state_wavefunction))


class TestMPSOperations(MPSStatesFixture):
    def test_norm2_is_deprecated(self):
        with self.assertWarns(DeprecationWarning):
            MPS(self.inhomogeneous_state).norm2()

    def test_norm_returns_real_nonnegative_values(self):
        complex_mps = MPS([-1j * x for x in self.inhomogeneous_state])
        complex_mps_norm = complex_mps.norm()
        self.assertTrue(complex_mps_norm > 0)
        self.assertTrue(isinstance(complex_mps_norm, np.double))

    def test_norm_returns_wavefunction_norm(self):
        self.assertAlmostEqual(
            MPS(self.inhomogeneous_state).norm(),
            np.linalg.norm(self.inhomogeneous_state_wavefunction),
        )

    def test_norm_squared_returns_wavefunction_norm_squared(self):
        self.assertAlmostEqual(
            MPS(self.inhomogeneous_state).norm_squared(),
            np.linalg.norm(self.inhomogeneous_state_wavefunction) ** 2,
        )

    def test_adding_mps_creates_mps_list(self):
        A = MPS(self.inhomogeneous_state)
        B = MPS(self.inhomogeneous_state)
        C = A + B
        self.assertTrue(isinstance(C, MPSSum))

    def test_adding_mps_with_non_mps_raises_error(self):
        A = MPS(self.inhomogeneous_state)
        with self.assertRaises(TypeError):
            A = A + 2.0
        with self.assertRaises(TypeError):
            A = 2.0 + A

    def test_subtracting_mps_creates_mps_list(self):
        A = MPS(self.inhomogeneous_state)
        B = MPS(self.inhomogeneous_state)
        C = A - B
        self.assertTrue(isinstance(C, MPSSum))

    def test_subtracting_mps_and_non_mps_raises_error(self):
        A = MPS(self.inhomogeneous_state)
        with self.assertRaises(TypeError):
            A = A + 2.0
        with self.assertRaises(TypeError):
            A = 2.0 + A

    def test_scaling_mps_creates_new_object(self):
        A = MPS(self.inhomogeneous_state)
        B = 3.0 * A
        self.assertTrue(B is not A)
        self.assertTrue(contain_different_objects(B, A))

    def test_multiplying_mps_by_non_scalar_raises_exception(self):
        A = MPS(self.inhomogeneous_state)
        with self.assertRaises(TypeError):
            A = A * np.array([1.0])
        with self.assertRaises(TypeError):
            A = A * A

    def test_scaled_mps_produces_scaled_wavefunction(self):
        factor = 1.0 + 3.0j
        A = MPS(self.inhomogeneous_state)
        self.assertTrue(similar(factor * A.to_vector(), (factor * A).to_vector()))
        factor = 1.0 + 3.0j
        A = MPS(self.inhomogeneous_state)
        self.assertTrue(similar(factor * A.to_vector(), (A * factor).to_vector()))

    def test_scaled_mps_produces_scaled_norm(self):
        factor = 1.0 + 3.0j
        A = MPS(self.inhomogeneous_state)
        self.assertAlmostEqual(abs(factor) * A.norm(), (factor * A).norm())


if __name__ == "__main__":
    unittest.main()
