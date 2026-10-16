# HAI Multi-Agent IDS

Code for the paper "Detection of Cyber-Physical Anomalies in Industrial Control Systems Using a Process-Aware Multi-Agent System". It was developed as part of my bachelor thesis.

The system detects anomalies in the turbine loop (P2) of the HAI 23.05 dataset. Instead of one model on all 38 variables there are six small agents, each working with its own group of signals: setpoints, control output, LSTM autoencoder for time patterns, protection rules, consistency between loops P1-P4-P2 and a sentinel for P1/P4. Thresholds are calibrated on normal data only using EVT/POT. An orchestrator combines the agents and produces the final alarm intervals. For comparison there is a plain Isolation Forest trained on the same 38 variables.

## Results

Evaluated on five combined attacks on P2 (A224, A225, A228, A232, A233) with the eTaPR metric, theta_p = 0.5, theta_r = 0.1.

| | eTaF1 | eTaP | eTaR | Detected | False intervals |
|---|---|---|---|---|---|
| Isolation Forest | 0.071 | 0.038 | 0.482 | 3 of 5 | 2386 |
| Multi-agent system | 0.942 | 0.918 | 0.967 | 5 of 5 | 2 |

## How to run

Tested on Python 3.14.

```
pip install -r requirements.txt
```

Download HAI 23.05 from https://github.com/icsdataset/hai and put the csv files into the `data` folder (`hai-train1.csv` ... `hai-train4.csv`, `hai-test1.csv`, `hai-test2.csv`, `label-test1.csv`, `label-test2.csv`). The dataset itself is not included in the repo.

Then run the scripts in this order:

```
python scripts/build_p2_target_mask.py
python scripts/run_baseline.py
python scripts/run_multi_agent.py
python scripts/apply_orchestrator_final.py
```

The random seed is fixed to 42, so the numbers above should reproduce. The `results` folder already contains the metrics and predictions, so they can be checked without training anything.

## Dashboard (optional)

```
streamlit run app/dashboard.py
```

It reads everything from `results`. The button that generates a text report for an alarm uses the OpenAI API, so put your key into a `.env` file in the project root:

```
OPENAI_API_KEY=your_key
```

`python scripts/plot_thesis_figures.py` draws extra plots into `results/figures`, the dashboard shows them in the sidebar if they exist.

## Structure

- `app` - Streamlit dashboard for the operator
- `src/agents` - the six agents
- `src` - orchestrator, metrics (eTaPR), config, LLM report
- `scripts` - experiment pipeline, run in the order above
- `results` - metrics and predictions (csv)
- `figures` - plots
- `data` - HAI csv files, not in git
