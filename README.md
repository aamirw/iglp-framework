# IG-LP Framework

This project is the open‑source implementation of the **IG‑LP framework** presented in the research paper *Enhancing Value Chain Resilience through Redundancy and Flexibility in Production Networks of Micro and Small Enterprises*. The project was developed using Python 3.12. The repository contains:

* **Source code (src)** – the core framework that reproduces the experiments in the paper.
* **Experiment data (experiments_data)** – the data used for data analysis and results published in the paper.

## Getting Started

```bash
# Clone the repo
git clone https://github.com/aamirw/iglp-framework.git
cd iglp-framework

# Install dependencies
pip install -r requirements.txt
```

## Running the Experiments

The framework provides a command‑line interface to run the experiments.

```bash
# Run all experiments
python -m src.resilience_evaluator
```

## Data

The input to IG-LP, i.e., test configurations is configured in `src/test_configs/experiments.py`. 

Results along with other data such as production network scenarios data (generated_vc_scenarios), planner inputs-outputs, analysis output will be written to the auto-generated `data/` directory.

## License

This project is licensed under the European Union Public Licence (EUPL), Version 1.2.