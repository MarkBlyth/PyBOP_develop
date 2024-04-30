import numpy as np

from pybop.costs._likelihoods import BaseLikelihood
from pybop.costs.base_cost import BaseCost
from pybop.observers.observer import Observer


class RootMeanSquaredError(BaseCost):
    """
    Root mean square error cost function.

    Computes the root mean square error between model predictions and the target
    data, providing a measure of the differences between predicted values and
    observed values.

    Inherits all parameters and attributes from ``BaseCost``.

    """

    def __init__(self, problem, weights=None):
        super(RootMeanSquaredError, self).__init__(problem, weights=weights)

        # Default fail gradient
        self._de = 1.0

    def _evaluate(self, x, grad=None):
        """
        Calculate the root mean square error for a given set of parameters.

        Parameters
        ----------
        x : array-like
            The parameters for which to evaluate the cost.
        grad : array-like, optional
            An array to store the gradient of the cost function with respect
            to the parameters.

        Returns
        -------
        float
            The root mean square error.

        """
        predictions = self.problem.evaluate(x)
        errors = np.zeros(len(predictions))
        # For each dataset...
        for i, (prediction, target) in enumerate(zip(predictions, self._target)):
            for key in self.signal:
                if len(prediction.get(key, [])) != len(target.get(key, [])):
                    return np.float64(np.inf)  # prediction doesn't match target

            # Calculate the root mean square error
            e = np.array(
                [
                    np.sqrt(np.mean((prediction[signal] - target[signal]) ** 2))
                    for signal in self.signal
                ]
            )
            if self.n_outputs == 1:
                errors[i] = e.item()
            else:
                errors[i] = np.sum(e)

        # Weight errors and return
        if self.weights is None:
            return errors.sum()
        return np.inner(self.weights, errors)

    def _evaluateS1(self, x):
        ys, dys = self.problem.evaluateS1(x)

        errors, gradients = [], []
        for i, (prediction, dy, target) in enumerate(zip(ys, dys, self._target)):
            for key in self.signal:
                if len(prediction.get(key, [])) != len(target.get(key, [])):
                    e = np.float64(np.inf)
                    de = self._de * np.ones(self.n_parameters)
                    return e, de

            r = np.array(
                [prediction[signal] - target[signal] for signal in self.signal]
            )
            errors.append(np.sqrt(np.mean(r**2, axis=1)))
            gradients.append(
                np.mean((r * dy.T), axis=2)
                / (np.sqrt(np.mean((r * dy.T) ** 2, axis=2)) + np.finfo(float).eps)
            )

        errors = np.array(errors)
        gradients = np.array(gradients)
        if self.weights is None:
            return errors.sum(), gradients.sum(axis=1)

        # Weight and return
        weighted_gradients = np.inner(self.weights.reshape((1, 1, -1)), gradients).sum(
            axis=1
        )
        return np.inner(self.weights, errors), weighted_gradients

    def set_fail_gradient(self, de):
        """
        Set the fail gradient to a specified value.

        The fail gradient is used if an error occurs during the calculation
        of the gradient. This method allows updating the default gradient value.

        Parameters
        ----------
        de : float
            The new fail gradient value to be used.
        """
        de = float(de)
        self._de = de


class SumSquaredError(BaseCost):
    """
    Sum of squared errors cost function.

    Computes the sum of the squares of the differences between model predictions
    and target data, which serves as a measure of the total error between the
    predicted and observed values.

    Inherits all parameters and attributes from ``BaseCost``.

    Additional Attributes
    ---------------------
    _de : float
        The gradient of the cost function to use if an error occurs during
        evaluation. Defaults to 1.0.

    """

    def __init__(self, problem):
        super(SumSquaredError, self).__init__(problem)

        # Default fail gradient
        self._de = 1.0

    def _evaluate(self, x, grad=None):
        """
        Calculate the sum of squared errors for a given set of parameters.

        Parameters
        ----------
        x : array-like
            The parameters for which to evaluate the cost.
        grad : array-like, optional
            An array to store the gradient of the cost function with respect
            to the parameters.

        Returns
        -------
        float
            The sum of squared errors.
        """
        predictions = self.problem.evaluate(x)
        errors = np.zeros(len(predictions))
        # For each dataset...
        for i, (prediction, target) in enumerate(zip(predictions, self._target)):
            for key in self.signal:
                if len(prediction.get(key, [])) != len(target.get(key, [])):
                    return np.float64(np.inf)  # prediction doesn't match target

            e = np.array(
                [
                    np.sum(((prediction[signal] - target[signal]) ** 2))
                    for signal in self.signal
                ]
            )
            if self.n_outputs == 1:
                errors[i] = e.item()
            else:
                errors[i] = np.sum(e)

        # Weight errors and return
        if self.weights is None:
            return errors.sum()
        return np.inner(self.weights, errors)

    def _evaluateS1(self, x):
        """
        Compute the cost and its gradient with respect to the parameters.

        Parameters
        ----------
        x : array-like
            The parameters for which to compute the cost and gradient.

        Returns
        -------
        tuple
            A tuple containing the cost and the gradient. The cost is a float,
            and the gradient is an array-like of the same length as `x`.

        Raises
        ------
        ValueError
            If an error occurs during the calculation of the cost or gradient.
        """
        ys, dys = self.problem.evaluateS1(x)

        errors, gradients = [], []
        for i, (prediction, dy, target) in enumerate(zip(ys, dys, self._target)):
            for key in self.signal:
                if len(prediction.get(key, [])) != len(target.get(key, [])):
                    e = np.float64(np.inf)
                    de = self._de * np.ones(self.n_parameters)
                    return e, de

            r = np.array(
                [prediction[signal] - target[signal] for signal in self.signal]
            )
            errors.append(np.sum(np.sum(r**2, axis=0), axis=0))
            gradients.append(2 * np.sum(np.sum((r * dy.T), axis=2), axis=1))

        errors = np.array(errors)
        gradients = np.array(gradients)
        if self.weights is None:
            return errors, gradients
        return np.inner(self.weights, errors), np.inner(self.weights, gradients)



    def set_fail_gradient(self, de):
        """
        Set the fail gradient to a specified value.

        The fail gradient is used if an error occurs during the calculation
        of the gradient. This method allows updating the default gradient value.

        Parameters
        ----------
        de : float
            The new fail gradient value to be used.
        """
        de = float(de)
        self._de = de


class ObserverCost(BaseCost):
    """
    Observer cost function.

    Computes the cost function for an observer model, which is log likelihood
    of the data points given the model parameters.

    Inherits all parameters and attributes from ``BaseCost``.

    """

    def __init__(self, observer: Observer):
        super().__init__(problem=observer)
        self._observer = observer

    def _evaluate(self, x, grad=None):
        """
        Calculate the observer cost for a given set of parameters.

        Parameters
        ----------
        x : array-like
            The parameters for which to evaluate the cost.
        grad : array-like, optional
            An array to store the gradient of the cost function with respect
            to the parameters.

        Returns
        -------
        float
            The observer cost (negative of the log likelihood).
        """
        inputs = {key: x[i] for i, key in enumerate(self._observer._model.fit_keys)}
        log_likelihood = self._observer.log_likelihood(
            self._target, self._observer.time_data(), inputs
        )
        return -log_likelihood

    def evaluateS1(self, x):
        """
        Compute the cost and its gradient with respect to the parameters.

        Parameters
        ----------
        x : array-like
            The parameters for which to compute the cost and gradient.

        Returns
        -------
        tuple
            A tuple containing the cost and the gradient. The cost is a float,
            and the gradient is an array-like of the same length as `x`.

        Raises
        ------
        ValueError
            If an error occurs during the calculation of the cost or gradient.
        """
        raise NotImplementedError


class MAP(BaseLikelihood):
    """
    Maximum a posteriori cost function.

    Computes the maximum a posteriori cost function, which is the sum of the
    negative log likelihood and the log prior.

    Inherits all parameters and attributes from ``BaseLikelihood``.

    """

    def __init__(self, problem, likelihood, sigma=None):
        super(MAP, self).__init__(problem)
        self.sigma0 = sigma
        if self.sigma0 is None:
            self.sigma0 = []
            for param in self.problem.parameters:
                self.sigma0.append(param.prior.sigma)

        try:
            self.likelihood = likelihood(problem=self.problem, sigma=self.sigma0)
        except Exception as e:
            raise ValueError(
                f"An error occurred when constructing the Likelihood class: {e}"
            )

        if hasattr(self, "likelihood") and not isinstance(
            self.likelihood, BaseLikelihood
        ):
            raise ValueError(f"{self.likelihood} must be a subclass of BaseLikelihood")

    def _evaluate(self, x, grad=None):
        """
        Calculate the maximum a posteriori cost for a given set of parameters.

        Parameters
        ----------
        x : array-like
            The parameters for which to evaluate the cost.
        grad : array-like, optional
            An array to store the gradient of the cost function with respect
            to the parameters.

        Returns
        -------
        float
            The maximum a posteriori cost.
        """
        log_likelihood = self.likelihood.evaluate(x)
        log_prior = sum(
            param.prior.logpdf(x_i) for x_i, param in zip(x, self.problem.parameters)
        )

        posterior = log_likelihood + log_prior
        return posterior

    def _evaluateS1(self, x):
        """
        Compute the maximum a posteriori with respect to the parameters.
        The method passes the likelihood gradient to the optimiser without modification.

        Parameters
        ----------
        x : array-like
            The parameters for which to compute the cost and gradient.

        Returns
        -------
        tuple
            A tuple containing the cost and the gradient. The cost is a float,
            and the gradient is an array-like of the same length as `x`.

        Raises
        ------
        ValueError
            If an error occurs during the calculation of the cost or gradient.
        """
        log_likelihood, dl = self.likelihood.evaluateS1(x)
        log_prior = sum(
            param.prior.logpdf(x_i) for x_i, param in zip(x, self.problem.parameters)
        )

        posterior = log_likelihood + log_prior
        return posterior, dl
