import numpy as np
import plotly.graph_objects as go
import pybamm

import pybop

# Parameter set and model definition
solver = pybamm.IDAKLUSolver()
parameter_set = pybop.ParameterSet.pybamm("Chen2020")
parameter_set.update(
    {
        "Negative electrode active material volume fraction": 0.63,
        "Positive electrode active material volume fraction": 0.71,
    }
)
synth_model = pybop.lithium_ion.DFN(parameter_set=parameter_set, solver=solver)

# Fitting parameters
parameters = pybop.Parameters(
    pybop.Parameter(
        "Negative electrode active material volume fraction",
        prior=pybop.Gaussian(0.68, 0.02),
        transformation=pybop.LogTransformation(),
    ),
    pybop.Parameter(
        "Positive electrode active material volume fraction",
        prior=pybop.Gaussian(0.65, 0.02),
        transformation=pybop.LogTransformation(),
    ),
)

# Generate data
init_soc = 0.5
sigma = 0.002
experiment = pybop.Experiment(
    [
        ("Discharge at 0.5C for 6 minutes (5 second period)",),
    ]
)
values = synth_model.predict(
    initial_state={"Initial SoC": init_soc}, experiment=experiment
)


def noise(sigma):
    return np.random.normal(0, sigma, len(values["Voltage [V]"].data))


# Form dataset
dataset = pybop.Dataset(
    {
        "Time [s]": values["Time [s]"].data,
        "Current function [A]": values["Current [A]"].data,
        "Voltage [V]": values["Voltage [V]"].data + noise(sigma),
        "Bulk open-circuit voltage [V]": values["Bulk open-circuit voltage [V]"].data
        + noise(sigma),
    }
)

model = pybop.lithium_ion.SPM(parameter_set=parameter_set, solver=pybamm.IDAKLUSolver())
model.build(initial_state={"Initial SoC": init_soc})
signal = ["Voltage [V]", "Bulk open-circuit voltage [V]"]

# Generate problem, likelihood, and sampler
problem = pybop.FittingProblem(model, parameters, dataset, signal=signal)
likelihood = pybop.GaussianLogLikelihoodKnownSigma(problem, sigma0=0.002)
posterior = pybop.LogPosterior(likelihood)

optim = pybop.DifferentialEvolutionMCMC(
    posterior,
    chains=3,
    max_iterations=300,
    warm_up=100,
    verbose=True,
    # parallel=True,  # uncomment to enable parallelisation (MacOS/WSL/Linux only)
)
result = optim.run()

# Create a histogram
fig = go.Figure()
for _i, data in enumerate(result):
    fig.add_trace(go.Histogram(x=data[:, 0], name="Neg", opacity=0.75))
    fig.add_trace(go.Histogram(x=data[:, 1], name="Pos", opacity=0.75))

# Update layout for better visualization
fig.update_layout(
    title="Posterior distribution of volume fractions",
    xaxis_title="Value",
    yaxis_title="Count",
    barmode="overlay",
)

# Show the plot
fig.show()
