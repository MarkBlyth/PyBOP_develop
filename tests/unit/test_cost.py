import pytest
import pybop
import numpy as np

class TestCosts:
    """
    Class for tests cost functions
    """

    @pytest.mark.unit
    def test_RMSE(self):
        # Tests cost function
        vector1 = np.array([1, 2, 3])
        vector2 = np.array([2, 3, 4])

        cost = pybop.RMSE()
        cost.compute(vector1, vector2)

    @pytest.mark.unit
    def test_RMSE_mismatch_dims(self):
        # Tests cost function
        vector1 = np.array([1, 2, 3])
        vector2 = np.array([2, 3, 4, 5])

        cost = pybop.RMSE()
        with pytest.raises(
                ValueError
        ):
            cost.compute(vector1, vector2)

    @pytest.mark.unit
    def test_RMSE_incorrect_type(self):
        # Tests cost function
        vector1 = np.array([1, 2, 3])
        vector2 = "string"

        cost = pybop.RMSE()
        with pytest.raises(
            ValueError
        ):
            cost.compute(vector1, vector2)

    @pytest.mark.unit
    def test_MLE(self):
        # Tests cost function
        vector1 = np.array([1, 2, 3])
        vector2 = np.array([2, 3, 4])

        cost = pybop.MLE()
        cost.compute(vector1, vector2)

    @pytest.mark.unit
    def test_PEM(self):
        # Tests cost function
        vector1 = np.array([1, 2, 3])
        vector2 = np.array([2, 3, 4])

        cost = pybop.PEM()
        cost.compute(vector1, vector2)

    @pytest.mark.unit
    def test_MAP(self):
        # Tests cost function
        vector1 = np.array([1, 2, 3])
        vector2 = np.array([2, 3, 4])

        cost = pybop.MAP()
        cost.compute(vector1, vector2)
