# Process-Oriented ICS Anomaly Detection Configuration — HAI 23.05

**Role of this document.** Architectural configuration of process-anomaly detectors for the HAI 23.05 industrial-control dataset, produced from process semantics, functional roles, temporal behaviour and physical relationships of the available tags. No anomaly detection is performed here and no cyberattack is classified; the output is a detector-routing configuration to be reviewed by an ICS expert before training/calibration.

---

## 1. Scope, input and method

**Inputs used**

- Dataset: `hai-23.05/` — `hai-train1..4.csv` (normal operation) and `hai-test1..2.csv` / `label-test1..2.csv` (labelled, used only for context on process behaviour).
- Technical documentation: `hai_dataset_technical_details.pdf` (v4.0, May 2023), including boiler/turbine/water-treatment control descriptions, data-point table, control logics and attack scenarios.
- Process graphs shipped in `hai.zip`: `graph/boiler/phy_boiler.json`, `graph/boiler/dcs_1001h..1020h.json`, `graph/graph_analysis.ipynb`.
- Descriptive statistics and normal-operation characterisation computed **only** on `hai-train1..4.csv` (mean, std, range, cardinality, lag-1 autocorrelation, mean/max absolute step, duty cycle, Spearman correlations).

**Method**

1. Reconstruct the functional role of every tag from the documentation and the physical graph.
2. Characterise the dominant invariant of normal behaviour for each tag (rule, statistical, multivariate, temporal, consistency).
3. Group tags into control loops, protection groups, actuator/sensor pairs and causally-connected subsystems.
4. Assign each tag/group to detector classes D1-D5, preferring the simplest class that covers the dominant invariant.
5. Specify inputs, scope, invariant, training requirement and inter-detector dependencies.

No machine-learning algorithm is selected; detector classes are specified conceptually as required by the prompt.

---

## 2. Dataset overview and normal-operation characterisation

### 2.1 Files, size and continuity

| File | Records | Time span | Role |
|---|---:|---|---|
| hai-train1.csv | 280,800 | 2022-08-04 18:00:01 → 2022-08-08 00:00:00 | normal |
| hai-train2.csv | 291,600 | 2022-08-13 07:00:01 → 2022-08-16 16:00:00 | normal |
| hai-train3.csv | 126,000 | 2022-08-19 16:00:01 → 2022-08-21 03:00:00 | normal |
| hai-train4.csv | 198,000 | 2022-08-22 17:00:01 → 2022-08-25 00:00:00 | normal |
| hai-test1.csv | 54,000 | 2022-08-12 16:00:01 → 2022-08-13 07:00:00 | labelled (14 attacks) |
| hai-test2.csv | 230,400 | 2022-08-17 00:00:01 → 2022-08-19 16:00:00 | labelled (38 attacks) |

- Sampling: **1 Hz** (uniform, 1,458,000 records total).
- Variables: **86 process tags** + timestamp. 77 of them are documented in the HAI 23.05 data-point table; 9 are not described there: the 7 internal `x100*_*_OUT` points, `P1_PP04D` and `P2_AutoGO` (the last is documented under the alias `P2_AutoGo`). Conversely, the documented operator setpoints `P1_B2004/B2016/B3004/B3005/B4002/B4005/B400B/B4022` and `P4_HT_LD` are not present as CSV columns.
- Subsystems: **P1 Boiler (Emerson Ovation)**, **P2 Turbine (GE Mark VIe)**, **P3 Water Treatment (Siemens S7)**, **P4 HIL simulation (dSPACE)**, plus internal `x100*` boiler-DCS points.

### 2.2 Normal-operation signal characterisation (from train files)

The table below summarises the characterisation that drives detector assignment. `lag1` is the lag-1 autocorrelation, `step` the maximum absolute one-second step during normal operation.

| Tag | Mean | Std | Min | Max | Uniq | lag1 | max step/s |
|---|---:|---:|---:|---:|---:|---:|---:|
| P1_FCV01D | 30.05 | 24.72 | 0 | 92.24 | 777330 | 0.9997 | 49.78 |
| P1_FCV01Z | 29.89 | 24.99 | 0.3143 | 92.2 | 10327 | 0.9997 | 47.67 |
| P1_FCV02D | 47.1 | 40.9 | 15 | 100 | 18275 | 0.9562 | 85 |
| P1_FCV02Z | 42.69 | 38.03 | 12.29 | 97.73 | 10169 | 0.9999 | 28.93 |
| P1_FCV03D | 55.07 | 3.55 | 47.69 | 68.65 | 607743 | 0.9999 | 8.582 |
| P1_FCV03Z | 55.78 | 3.635 | 48.33 | 69.71 | 2521 | 0.9996 | 8.492 |
| P1_FT01 | 62.73 | 7.821 | 0.801 | 198.8 | 862 | 0.9943 | 34.71 |
| P1_FT01Z | 326.6 | 40.5 | 4.171 | 892.2 | 861 | 0.9942 | 180.7 |
| P1_FT02 | 981.2 | 1015 | 1.183 | 2507 | 13106 | 0.9996 | 2282 |
| P1_FT02Z | 1536 | 1268 | 6.157 | 3190 | 13100 | 0.9996 | 2506 |
| P1_FT03 | 247.3 | 14.98 | 217.1 | 287.5 | 364 | 0.9993 | 15.83 |
| P1_FT03Z | 999.6 | 30.32 | 934 | 1072 | 364 | 0.9992 | 32.18 |
| P1_LCV01D | 15.34 | 2.726 | 0.5966 | 34.83 | 574190 | 0.9996 | 5.72 |
| P1_LCV01Z | 15.22 | 2.723 | 0.2991 | 35.02 | 2824 | 0.9983 | 6.18 |
| P1_LIT01 | 346.8 | 28.05 | 280.3 | 426.5 | 2774 | 1 | 57.4 |
| P1_PCV01D | 28.07 | 2.52 | 12.04 | 44.96 | 559752 | 0.9997 | 1.974 |
| P1_PCV01Z | 28.53 | 2.542 | 12.74 | 45.74 | 2735 | 0.9978 | 2.258 |
| P1_PCV02D | 12 | 0.0294 | 12 | 17.17 | 338 | 0.992 | 1.283 |
| P1_PCV02Z | 11.88 | 0.18 | 11.67 | 16.3 | 115 | 0.9994 | 1.572 |
| P1_PIT01 | 1.116 | 0.1027 | 0.4701 | 2.049 | 1460 | 0.9987 | 0.4418 |
| P1_PIT01_HH | 5.243e+05 | 0 | 5.243e+05 | 5.243e+05 | 1 | const | 0 |
| P1_PIT02 | 0.621 | 0.363 | 0.3114 | 1.543 | 1614 | 0.9981 | 0.3899 |
| P1_PP01AD | 0 | 0 | 0 | 0 | 1 | const | 0 |
| P1_PP01AR | 0 | 0 | 0 | 0 | 1 | const | 0 |
| P1_PP01BD | 1 | 0 | 1 | 1 | 1 | const | 0 |
| P1_PP01BR | 1 | 0 | 1 | 1 | 1 | const | 0 |
| P1_PP02D | 1 | 0 | 1 | 1 | 1 | const | 0 |
| P1_PP02R | 1 | 0 | 1 | 1 | 1 | const | 0 |
| P1_PP04 | 24.72 | 16.62 | 0 | 45 | 430644 | 1 | 38.79 |
| P1_PP04D | 0.6246 | 0.4842 | 0 | 1 | 2 | 0.9989 | 1 |
| P1_PP04SP | 27.7 | 0.2992 | 27.05 | 27.98 | 148 | 1 | 0.7901 |
| P1_SOL01D | 5.243e+05 | 0 | 5.243e+05 | 5.243e+05 | 1 | const | 0 |
| P1_SOL03D | 5.243e+05 | 0 | 5.243e+05 | 5.243e+05 | 1 | const | 0 |
| P1_STSP | 1 | 0 | 1 | 1 | 1 | const | 0 |
| P1_TIT01 | 30.3 | 1.326 | 27.67 | 34.12 | 424 | 0.9999 | 3.677 |
| P1_TIT02 | 36.03 | 2.03 | 32.49 | 39.62 | 468 | 1 | 3.738 |
| P1_TIT03 | 27.9 | 1.221 | 25.52 | 30.6 | 2952 | 0.9994 | 3.741 |
| P2_24Vdc | 28.03 | 0.0035 | 28.01 | 28.05 | 280 | 0.2634 | 0.0226 |
| P2_ATSW_Lamp | 0.8883 | 0.315 | 0 | 1 | 2 | 0.9999 | 1 |
| P2_AutoGO | 0.8883 | 0.315 | 0 | 1 | 2 | 0.9999 | 1 |
| P2_AutoSD | 118.1 | 7.697 | 100.7 | 129.4 | 72 | 0.9999 | 28.54 |
| P2_Emerg | 0 | 0 | 0 | 0 | 1 | const | 0 |
| P2_MASW | 0.1117 | 0.315 | 0 | 1 | 2 | 0.9999 | 1 |
| P2_MASW_Lamp | 0.1117 | 0.315 | 0 | 1 | 2 | 0.9999 | 1 |
| P2_ManualGO | 0.1117 | 0.315 | 0 | 1 | 2 | 0.9999 | 1 |
| P2_ManualSD | 11.3 | 3.789 | 0 | 12.93 | 13 | 1 | 12.45 |
| P2_OnOff | 1 | 0 | 1 | 1 | 1 | const | 0 |
| P2_RTR | 2880 | 0 | 2880 | 2880 | 1 | const | 0 |
| P2_SCO | 5.471e+04 | 163.3 | 5.415e+04 | 5.483e+04 | 209 | 0.9999 | 400 |
| P2_SCST | 720.5 | 0.2241 | 719.4 | 721.2 | 18301 | 0.9043 | 1.016 |
| P2_SIT01 | 904.7 | 32.9 | 746 | 967 | 203 | 0.9991 | 88 |
| P2_TripEx | 1 | 0 | 1 | 1 | 1 | const | 0 |
| P2_VIBTR01 | 6.717 | 0.4123 | 5.123 | 7.862 | 22563 | 0.3883 | 1.507 |
| P2_VIBTR02 | -3.131 | 0.3976 | -4.054 | -1.848 | 20151 | 0.3135 | 1.375 |
| P2_VIBTR03 | 9.652 | 0.3907 | 7.989 | 10.6 | 22590 | 0.7744 | 1.852 |
| P2_VIBTR04 | -1.081 | 0.3718 | -1.91 | 0.3069 | 20048 | 0.8321 | 1.114 |
| P2_VT01 | 11.95 | 0.047 | 11.79 | 12.07 | 22903 | 0.2752 | 0.2211 |
| P2_VTR01 | 50 | 0 | 50 | 50 | 1 | const | 0 |
| P2_VTR02 | 50 | 0 | 50 | 50 | 1 | const | 0 |
| P2_VTR03 | 50 | 0 | 50 | 50 | 1 | const | 0 |
| P2_VTR04 | 50 | 0 | 50 | 50 | 1 | const | 0 |
| P3_FIT01 | 1059 | 1674 | 20 | 5478 | 5421 | 0.9932 | 3812 |
| P3_LCP01D | 4983 | 5111 | -16 | 1.382e+04 | 1731 | 0.9992 | 5576 |
| P3_LCV01D | 7418 | 6826 | -176 | 1.941e+04 | 1140 | 0.9992 | 1.589e+04 |
| P3_LH01 | 70 | 0 | 70 | 70 | 1 | const | 0 |
| P3_LIT01 | 1.507e+04 | 3250 | 7969 | 1.976e+04 | 9004 | 0.9998 | 8715 |
| P3_LL01 | 30 | 0 | 30 | 30 | 1 | const | 0 |
| P3_PIT01 | 769 | 1302 | 16 | 4724 | 4424 | 0.9969 | 2576 |
| P4_HT_FD | -0.0002 | 0.0021 | -0.0271 | 0.0326 | 668 | 0.2473 | 0.0506 |
| P4_HT_PO | 34.76 | 31.4 | 0 | 90.57 | 3540 | 0.999 | 73.33 |
| P4_HT_PS | 4.193 | 2.317 | 0.0748 | 7.799 | 21 | 1 | 7.196 |
| P4_LD | 366.4 | 60.64 | 228.4 | 499.1 | 11265 | 0.999 | 85.74 |
| P4_ST_FD | -0 | 0.0016 | -0.0218 | 0.0101 | 263 | 0.3239 | 0.0227 |
| P4_ST_GOV | 1.812e+04 | 1805 | 1.276e+04 | 2.681e+04 | 12958 | 0.9988 | 3130 |
| P4_ST_LD | 331.5 | 36.96 | 229.7 | 497.5 | 10609 | 0.9973 | 86.26 |
| P4_ST_PO | 331.8 | 33.47 | 231.6 | 494.6 | 13314 | 0.9991 | 57 |
| P4_ST_PS | 15.38 | 8.857 | 1.133 | 29.28 | 38 | 1 | 25.38 |
| P4_ST_PT01 | 9973 | 29.11 | 9804 | 1.023e+04 | 246 | 0.9931 | 161 |
| P4_ST_TT01 | 2.71e+04 | 128.2 | 2.684e+04 | 2.747e+04 | 488 | 0.9994 | 352 |
| x1001_05_SETPOINT_OUT | 0.131 | 0.0413 | 0.0509 | 0.2 | 1049 | 1 | 0.0163 |
| x1001_15_ASSIGN_OUT | 1.116 | 0.1059 | 0.7784 | 1.598 | 59720 | 0.999 | 0.1772 |
| x1002_07_SETPOINT_OUT | 346.2 | 27.34 | 302.4 | 398.5 | 1274 | 1 | 50.58 |
| x1002_08_SETPOINT_OUT | 999.7 | 30.1 | 950.6 | 1049 | 1074 | 1 | 39.71 |
| x1003_10_SETPOINT_OUT | 1536 | 1268 | 6.157 | 3190 | 13100 | 0.9996 | 2506 |
| x1003_18_SETPOINT_OUT | 26.45 | 0.9215 | 25.14 | 28 | 280 | 1 | 1.897 |
| x1003_24_SUM_OUT | 30.23 | 0.9783 | 27.96 | 33.09 | 80164 | 0.9999 | 2.44 |

**Key behavioural findings used for detector assignment**

- **Control-loop structure is visible in the data**: command/position pairs are strongly correlated (FCV01D/Z ρ≈0.99, FCV03D/Z, LCV01D/Z, PCV01D/Z), and `P1_PIT01 ↔ x1001_15_ASSIGN_OUT` has a normal residual of only ≈0.1 bar, identifying x1001_15 as the pressure setpoint.
- **Two x-tags map to documented setpoints**: `x1002_08_SETPOINT_OUT ↔ P1_FT03Z` (ρ≈0.99) and `x1003_10_SETPOINT_OUT ↔ P1_FT02Z` (ρ≈0.996).
- **Slow-inertia variables** (lag1 ≈ 1.0, tiny mean step): tank levels, temperatures, valve positions and setpoints — candidates for temporal-dynamics monitoring.
- **Fast noise-like variables** (low lag1): vibration probes (`P2_VIBTR01/02` lag1≈0.3-0.4), key-phasor phase `P2_VT01` (0.28), frequency deviations `P4_HT_FD`/`P4_ST_FD` (0.25/0.32) — candidates for statistical/envelope monitoring.
- **20 constant tags** during normal operation (protection constants and discrete states), including `P1_PIT01_HH`, `P1_SOL01D/SOL03D`, `P2_Emerg`, `P2_RTR`, `P2_VTR01-04`, `P3_LH01/LL01`; their normal invariant is purely rule-based.
- **Binary/persistent state tags** with few transitions (24-482 transitions over 896,400 s): pump/valve commands, manual/auto switches and lamps — handled by the D1 state-machine/rule detector.
- **Undocumented placeholders**: `P1_PIT01_HH`, `P1_SOL01D`, `P1_SOL03D` hold the constant value `524320` (outside their declared physical ranges) — recorded as an unresolved data-quality issue.

---

## 3. Process architecture and functional groups

```text
P1 BOILER (Emerson Ovation DCS)
  P1-PC pressure loop : SP(x1001_15 / B2016) -> PID -> PCV01D & PCV02D -> PIT01 (PV)
  P1-LC level loop    : SP(x1002_07 / B3004) -> PID -> LCV01D -> LIT01 (PV); feed-forward from FCV03D/FT03
  P1-FC flow loop     : SP(x1002_08 / B3005) -> PID -> FCV03D -> FT03 (PV)
  P1-TC temperature   : SP(B4022/x1003_18) -> cascade PID -> FCV01D & FCV02D -> TIT01 (PV); inner flow FT02 (x1003_10)
  P1-CC cooling loop  : SP(PP04SP) -> activation+saturation -> PP04 -> TIT03 (PV)
  Auxiliaries         : PP01A/B (transfer), PP02 (heating), SOL01/SOL03 (supply/drain), PP04D
P2 TURBINE (GE Mark VIe DCS)
  P2-SC speed loop    : SP(AutoSD/ManualSD) -> PID+ramp -> SCO -> SIT01 (PV)
  P2-TRIP protection  : SIT01 vs RTR; VIBTR01-04 vs VTR01-04 -> Emerg / TripEx
P3 WATER TREATMENT (Siemens S7)
  P3-LC level loop    : LH01/LL01 -> discharge demand LCV01D + pumping demand LCP01D -> LIT01 (PV)
P4 HIL SIMULATION (dSPACE + S7-1500)
  Steam-turbine model : ST_PS -> ST_GOV -> ST_PO, ST_PT01/ST_TT01, ST_FD <-> P2 speed
  Pumped-storage model: HT_PS -> HT_PO, HT_FD; total demand LD
Internal setpoints    : x1001_05, x1001_15, x1002_07, x1002_08, x1003_10, x1003_18, x1003_24
```

**Functional groups identified**

- Control loops: `P1-PC`, `P1-LC`, `P1-FC`, `P1-TC`, `P1-CC`, `P2-SC`, `P3-LC`.
- Protection groups: `P1-PIT01_HH`; `P2-TRIP` (SIT01/RTR, VIBTR/VTR, Emerg/TripEx); `P3-LH01/LL01`.
- Actuator/sensor pairs: every `*D`/`*Z` valve pair; `PP01AD/AR`, `PP01BD/BR`, `PP02D/R`, `PP04D/PP04`; `SCO/SIT01`.
- Subsystem groups: `P1` boiler, `P2` turbine, `P3` water treatment, `P4` HIL.
- Cross-subsystem causal groups: boiler heat-exchanger ↔ HIL steam state; HIL grid frequency ↔ turbine speed; HIL power balance.

---

## A. Variable characterization table

| Tag | Subsystem | Functional role | Signal type | Dominant normal-behaviour invariant | Detector class(es) | Related variables | Reasoning | Confidence |
|---|---|---|---|---|---|---|---|---|
| `P1_FCV01D` | P1 Boiler / P1-TC | Position command, heat-exchanger flow valve FCV01 (temperature inner loop) | CO | physical/causal consistency+temporal dependency+multivariate relationship | D5_P1_FCV01_TRACK,D4_P1_FCV_PROFILE,D3_P1_TC_SPLIT | P1_FCV01Z,P1_FCV02D,P1_FCV02Z,P1_TIT01,P1_FT02Z,x1003_10_SETPOINT_OUT | Command drives a physical valve; normal invariant is (i) tracking of the measured position Z, (ii) rate-limited trajectory, (iii) coordinated split with FCV02 on the same heat-exchanger branch. | high |
| `P1_FCV01Z` | P1 Boiler / P1-TC | Measured position, FCV01 | PV | physical/causal consistency+statistical stability+temporal dependency | D5_P1_FCV01_TRACK,D2_P1_VALVE_POS,D4_P1_FCV_PROFILE | P1_FCV01D,P1_FCV02Z,P1_FT02Z | Valve feedback must follow its command within actuator tolerance and stay within a stationary noise band. | high |
| `P1_FCV02D` | P1 Boiler / P1-TC | Position command, heat-exchanger flow valve FCV02 (recirculation branch) | CO | physical/causal consistency+temporal dependency+explicit physical/logical constraint | D5_P1_FCV02_TRACK,D4_P1_FCV_PROFILE,D1_P1_VALVE_RANGE,D3_P1_TC_SPLIT | P1_FCV02Z,P1_FCV01D,P1_FCV01Z,P1_TIT01 | Second branch of the TC cascade; has a documented minimum opening (>=15%) to keep recirculation flow, which is an explicit rule on top of the tracking invariant. | high |
| `P1_FCV02Z` | P1 Boiler / P1-TC | Measured position, FCV02 | PV | physical/causal consistency+statistical stability | D5_P1_FCV02_TRACK,D2_P1_VALVE_POS,D1_P1_VALVE_RANGE | P1_FCV02D,P1_FCV01Z | Follows FCV02D; the large observed D/Z mismatch (std ~17%) indicates the valve has its own slow dynamics and the residual must be calibrated on normal data. | high |
| `P1_FCV03D` | P1 Boiler / P1-FC | Position command, outflow control valve FCV03 | CO | physical/causal consistency+temporal dependency | D5_P1_FCV03_TRACK,D4_P1_FCV_PROFILE | P1_FCV03Z,P1_FT03Z,x1002_08_SETPOINT_OUT | Outer-loop actuator of the flow controller; must track FCV03Z and follow the flow setpoint trajectory. | high |
| `P1_FCV03Z` | P1 Boiler / P1-FC | Measured position, FCV03 | PV | physical/causal consistency+statistical stability | D5_P1_FCV03_TRACK,D2_P1_VALVE_POS | P1_FCV03D,P1_FT03Z | Tight command tracking observed in normal data (std of residual ~0.5%). | high |
| `P1_FT01` | P1 Boiler / P1-PC | Measured inflow (pressure-drop transmitter), return water tank | PV | physical/causal consistency+statistical stability+temporal dependency | D5_PC_PV_FLOW,D2_P1_SENSOR_NOISE,D4_P1_LIT_INERTIA | P1_FT01Z,P1_LIT01,P1_FT03Z,P1_PIT01 | PV2 of the pressure loop and mass-balance term for the return tank; raw mmH2O signal is noisy, its converted signal FT01Z is the flow-rate invariant. | high |
| `P1_FT01Z` | P1 Boiler / P1-PC | Inflow rate to return tank, converted from FT01 | PV | physical/causal consistency+statistical stability | D5_PC_PV_FLOW,D5_P1_MASS_BALANCE,D2_P1_SENSOR_NOISE | P1_FT01,P1_FT03Z,P1_LIT01 | Engineering flow rate; participates in the tank mass balance LIT01 ~ integral(FT01Z-FT03Z). | high |
| `P1_FT02` | P1 Boiler / P1-TC | Measured flow (pressure-drop), heating water tank | PV | physical/causal consistency+statistical stability+temporal dependency | D5_P1_TC_TEMP,D2_P1_SENSOR_NOISE,D4_P1_THERMAL | P1_FT02Z,P1_FCV01Z,P1_FCV02Z,x1003_10_SETPOINT_OUT | PV of the TC inner flow loop; strongly correlated with the heat-transfer branch valve position. | high |
| `P1_FT02Z` | P1 Boiler / P1-TC | Heating water flow rate, converted from FT02 | PV | physical/causal consistency+statistical stability | D5_P1_FC02_FLOW,D2_P1_SENSOR_NOISE | P1_FT02,P1_FCV01Z,P1_FCV02Z,x1003_10_SETPOINT_OUT | Normal invariant is a causal relation with the loop setpoint (x1003_10) and with the heat-transfer valve split. | high |
| `P1_FT03` | P1 Boiler / P1-FC | Measured outflow (pressure-drop), return tank | PV | physical/causal consistency+statistical stability+temporal dependency | D5_P1_FC03_FLOW,D2_P1_SENSOR_NOISE,D4_P1_LIT_INERTIA | P1_FT03Z,P1_FCV03Z,x1002_08_SETPOINT_OUT,P1_LIT01 | PV of the flow controller; the level controller uses it as feed-forward, so its invariant is both setpoint tracking and causal coupling to LIT01. | high |
| `P1_FT03Z` | P1 Boiler / P1-FC | Outflow rate, converted from FT03 | PV | physical/causal consistency+statistical stability | D5_P1_FC03_FLOW,D5_P1_MASS_BALANCE,D2_P1_SENSOR_NOISE | P1_FT03,P1_FCV03Z,x1002_08_SETPOINT_OUT | Engineering flow rate used by the residual detector against the flow setpoint. | high |
| `P1_LCV01D` | P1 Boiler / P1-LC | Position command, level control valve LCV01 | CO | physical/causal consistency+temporal dependency | D5_P1_LCV01_TRACK,D4_P1_FCV_PROFILE | P1_LCV01Z,P1_LIT01,P1_FT03Z,x1002_07_SETPOINT_OUT | Outer-loop actuator of the level controller; must track its position feedback and the level setpoint trajectory. | high |
| `P1_LCV01Z` | P1 Boiler / P1-LC | Measured position, LCV01 | PV | physical/causal consistency+statistical stability | D5_P1_LCV01_TRACK,D2_P1_VALVE_POS | P1_LCV01D,P1_LIT01 | Command tracking residual is the primary invariant. | high |
| `P1_LIT01` | P1 Boiler / P1-LC | Water level, return water tank | PV | physical/causal consistency+statistical stability+temporal dependency | D5_P1_LC_LEVEL,D2_P1_SENSOR_NOISE,D4_P1_LIT_INERTIA,D5_P1_MASS_BALANCE | P1_LCV01D,P1_FT01Z,P1_FT03Z,x1002_07_SETPOINT_OUT | Controlled PV; invariant is setpoint tracking, slow inertial dynamics and mass balance with FT01Z/FT03Z. | high |
| `P1_PCV01D` | P1 Boiler / P1-PC | Position command, pressure control valve PCV01 (transfer to TK03) | CO | physical/causal consistency+temporal dependency+multivariate relationship | D5_P1_PCV01_TRACK,D4_P1_FCV_PROFILE,D3_P1_PC_SPLIT | P1_PCV01Z,P1_PCV02D,P1_PCV02Z,P1_PIT01,x1001_15_ASSIGN_OUT | Pressure-loop actuator; normal invariant includes coordination with PCV02 which splits transfer vs recirculation. | high |
| `P1_PCV01Z` | P1 Boiler / P1-PC | Measured position, PCV01 | PV | physical/causal consistency+statistical stability | D5_P1_PCV01_TRACK,D2_P1_VALVE_POS | P1_PCV01D,P1_PIT01 | Command tracking plus stationary noise. | high |
| `P1_PCV02D` | P1 Boiler / P1-PC | Position command, pressure control valve PCV02 (recirculation to TK01) | CO | multivariate relationship+explicit physical/logical constraint+temporal dependency | D3_P1_PC_SPLIT,D1_P1_VALVE_RANGE,D4_P1_FCV_PROFILE | P1_PCV02Z,P1_PCV01D,P1_PIT01 | Held near 12% in normal operation (recirculation minimum). The dominant invariant is the split configuration with PCV01 and the explicit minimum-opening rule, not its marginal statistics. | high |
| `P1_PCV02Z` | P1 Boiler / P1-PC | Measured position, PCV02 | PV | multivariate relationship+physical/causal consistency | D3_P1_PC_SPLIT,D5_P1_PCV02_TRACK | P1_PCV02D,P1_PCV01Z | Follows PCV02D and belongs to the PC valve-pair configuration. | high |
| `P1_PIT01` | P1 Boiler / P1-PC | Heat-exchanger outlet pressure | PV | physical/causal consistency+explicit physical/logical constraint+statistical stability | D5_P1_PC_PRESS,D1_P1_HH_TRIP,D2_P1_SENSOR_NOISE | x1001_15_ASSIGN_OUT,x1001_05_SETPOINT_OUT,P1_PCV01Z,P1_PIT01_HH | Controlled PV of P1-PC; invariant is setpoint tracking (via x1001_15), respect of the HH protection threshold, and slow stationarity. | high |
| `P1_PIT01_HH` | P1 Boiler / P1-PC | Highest outlet pressure / high-high protection threshold | PROT | explicit physical/logical constraint | D1_P1_HH_TRIP | P1_PIT01 | Pure protection constant; the only meaningful invariant is the explicit trip/alarm rule (SIT01-type HH limit). | medium |
| `P1_PIT02` | P1 Boiler / P1-PC | Water supply pressure of heating water pump | PV | statistical stability+physical/causal consistency | D2_P1_AUX_PRESSURE,D5_PC_PV_FLOW | P1_FT01Z,P1_PIT01,P1_PP02R | Auxiliary pressure which must hold a stationary operating band and remain causally linked to pump running state. | medium |
| `P1_PP01AD` | P1 Boiler / auxiliaries | Start command, main water pump PP01A | CMD | explicit physical/logical constraint | D1_BLR_INTERLOCK | P1_PP01AR,P1_PP01BD,P1_PP01BR,P1_STSP | Discrete pump command; monitored as interlock/state legality, not statistically. | medium |
| `P1_PP01AR` | P1 Boiler / auxiliaries | Running state, main water pump PP01A | STATE | explicit physical/logical constraint | D1_BLR_INTERLOCK | P1_PP01AD,P1_STSP | Running feedback must be consistent with its start command and the boiler run state. | medium |
| `P1_PP01BD` | P1 Boiler / auxiliaries | Start command, main water pump PP01B | CMD | explicit physical/logical constraint | D1_BLR_INTERLOCK | P1_PP01BR,P1_PP01AD,P1_STSP | Duty/standby pump command; part of the pump interlock group. | medium |
| `P1_PP01BR` | P1 Boiler / auxiliaries | Running state, main water pump PP01B | STATE | explicit physical/logical constraint | D1_BLR_INTERLOCK | P1_PP01BD,P1_STSP | Running feedback consistency. | medium |
| `P1_PP02D` | P1 Boiler / auxiliaries | Start command, heating water pump PP02 | CMD | explicit physical/logical constraint | D1_BLR_INTERLOCK | P1_PP02R,P1_STSP,P1_FCV01D | Heating-circuit pump command; must be enabled whenever the TC loop demands heat-exchanger flow. | medium |
| `P1_PP02R` | P1 Boiler / auxiliaries | Running state, heating water pump PP02 | STATE | explicit physical/logical constraint | D1_BLR_INTERLOCK | P1_PP02D,P1_FCV01D | Running feedback consistency with command and with TC loop demand. | medium |
| `P1_PP04` | P1 Boiler / P1-CC | Control output of the cooling water pump (frequency) | CO | physical/causal consistency+temporal dependency+statistical stability | D5_P1_CC_COOLING,D4_P1_THERMAL,D2_P1_AUX_PRESSURE | P1_TIT03,P1_PP04D,P1_PP04SP | Cooling controller output; invariant is the causal relation with main-tank temperature TIT03 and the setpoint PP04SP. | high |
| `P1_PP04D` | P1 Boiler / P1-CC | Run command, cooling pump | CMD | explicit physical/logical constraint | D1_BLR_INTERLOCK | P1_PP04,P1_TIT03 | Binary activation of the cooler pump; must be consistent with the cooling demand. | medium |
| `P1_PP04SP` | P1 Boiler / P1-CC | Cooler temperature setpoint | SP | explicit physical/logical constraint+temporal dependency+multivariate relationship | D1_SETPOINT_ENVELOPE,D4_P1_SP_SEQUENCE,D3_P1_SP_GROUP | P1_PP04,P1_TIT03,P1_TIT02,x1003_18_SETPOINT_OUT | Operator setpoint drawn from the HMM normal-operation model; invariant is the allowed range and allowed transition sequence, not its raw value. | medium |
| `P1_SOL01D` | P1 Boiler / auxiliaries | Open command, main water tank supply valve | CMD | explicit physical/logical constraint | D1_P1_VALVE_PERMISSIVE | P1_SOL03D,P1_LIT01,P1_STSP | Discrete permissive; must respect tank level interlocks (no supply with drain open / tank full). | medium |
| `P1_SOL03D` | P1 Boiler / auxiliaries | Open command, main water tank drain valve | CMD | explicit physical/logical constraint | D1_P1_VALVE_PERMISSIVE | P1_SOL01D,P1_LIT01,P1_STSP | Discrete permissive; forbidden simultaneous supply+drain combination. | medium |
| `P1_STSP` | P1 Boiler / auxiliaries | Start/stop command of the boiler DCS | CMD | explicit physical/logical constraint | D1_BLR_INTERLOCK | P1_PP01AR,P1_PP01BR,P1_PP02R,P1_PP04 | Master run permissive for the boiler subsystem; gates all downstream P1 detectors. | high |
| `P1_TIT01` | P1 Boiler / P1-TC | Heat-exchanger outlet temperature (main vessel) | PV | physical/causal consistency+statistical stability+temporal dependency | D5_P1_TC_TEMP,D2_P1_SENSOR_NOISE,D4_P1_THERMAL,D5_HEX_COUPLE | x1003_18_SETPOINT_OUT,P1_FCV01D,P1_FCV02D,P4_ST_TT01 | Controlled PV of the TC cascade; invariant is setpoint tracking, thermal inertia and the physical coupling to steam-side temperature. | high |
| `P1_TIT02` | P1 Boiler / P1-TC | Temperature of the heating water tank | PV | statistical stability+temporal dependency+physical/causal consistency | D2_P1_SENSOR_NOISE,D4_P1_THERMAL,D5_P1_TC_TEMP | P1_TIT01,P1_FT02Z,P1_PP04SP | Slow thermal state coupled to the heat-exchanger duty; stationary band plus inertia. | medium |
| `P1_TIT03` | P1 Boiler / P1-CC | Temperature of the main water tank (cooling PV) | PV | physical/causal consistency+statistical stability+temporal dependency | D5_P1_CC_COOLING,D2_P1_COOL_TEMP,D4_P1_THERMAL | P1_PP04,P1_PP04SP,P1_PP04D | PV of the cooling loop; invariant is the causal relation between cooler pump output and tank temperature. | high |
| `P2_24Vdc` | P2 Turbine / electrical | DCS 24 V input supply voltage | PV | statistical stability | D2_P2_ELECTRICAL | P2_OnOff,P2_Emerg | Supply voltage must remain in a tight stationary band; excursions affect all turbine logic. | high |
| `P2_ATSW_Lamp` | P2 Turbine / HMI | Lamp of the auto switch | LAMP | explicit physical/logical constraint | D1_P2_MODE | P2_AutoGO,P2_MASW,P2_MASW_Lamp | Lamp feedback must match the corresponding switch/button state. | medium |
| `P2_AutoGO` | P2 Turbine / HMI | Auto start button | CMD | explicit physical/logical constraint+multivariate relationship | D1_P2_MODE,D3_P2_SP_MODE | P2_ATSW_Lamp,P2_MASW,P2_AutoSD | Operator command; invariant is mode/state consistency, not value. | high |
| `P2_AutoSD` | P2 Turbine / P2-SC | Auto speed demand (setpoint) | SP | temporal dependency+physical/causal consistency+multivariate relationship | D4_P2_SPEED_RAMP,D5_P2_SC,D3_P2_SP_MODE | P2_SIT01,P2_SCO,P2_ManualSD,P2_MASW | Primary speed setpoint; normal invariant is a ramp-shaped, HMM-scheduled trajectory and causality with SIT01/SCO. | high |
| `P2_Emerg` | P2 Turbine / P2-TRIP | Emergency button state | STATE | explicit physical/logical constraint | D1_P2_TRIP,D1_P2_MODE | P2_SIT01,P2_RTR,P2_VIBTR01,P2_TripEx | Trip state; must only become active according to the over-speed / over-vibration trip logic. | high |
| `P2_MASW` | P2 Turbine / HMI | Manual(1)/Auto(0) selector switch | STATE | explicit physical/logical constraint+multivariate relationship | D1_P2_MODE,D3_P2_SP_MODE | P2_MASW_Lamp,P2_AutoSD,P2_ManualSD | Selects the active setpoint; invariant is the manual/auto configuration consistency. | high |
| `P2_MASW_Lamp` | P2 Turbine / HMI | Lamp of the manual switch | LAMP | explicit physical/logical constraint | D1_P2_MODE | P2_MASW,P2_ATSW_Lamp | State feedback consistency. | medium |
| `P2_ManualGO` | P2 Turbine / HMI | Manual start button | CMD | explicit physical/logical constraint+multivariate relationship | D1_P2_MODE,D3_P2_SP_MODE | P2_ManualSD,P2_MASW | Operator command; mode consistency. | high |
| `P2_ManualSD` | P2 Turbine / P2-SC | Manual speed demand (setpoint) | SP | temporal dependency+physical/causal consistency+multivariate relationship | D4_P2_SPEED_RAMP,D5_P2_SC,D3_P2_SP_MODE | P2_ManualGO,P2_MASW,P2_SIT01,P2_SCO | Alternative speed setpoint; invariant is the ramp trajectory and causality with the speed loop. | high |
| `P2_OnOff` | P2 Turbine / electrical | On/off switch of the turbine DCS | CMD | explicit physical/logical constraint | D1_P2_MODE | P2_Emerg,P2_24Vdc | Master turbine enable; gates the turbine detectors. | high |
| `P2_RTR` | P2 Turbine / P2-TRIP | RPM trip rate (over-speed protection threshold) | PROT | explicit physical/logical constraint | D1_P2_TRIP | P2_SIT01,P2_Emerg | Explicit protection constant; invariant is the trip rule, not statistics. | high |
| `P2_SCO` | P2 Turbine / P2-SC | Control output value of the speed controller | CO | physical/causal consistency+statistical stability+temporal dependency | D5_P2_SC,D2_P2_ELECTRICAL,D4_P2_SPEED_RAMP | P2_SIT01,P2_AutoSD,P2_ManualSD | Speed-loop actuator output; must be causally consistent with the active setpoint and speed feedback. | high |
| `P2_SCST` | P2 Turbine / P2-SC | Speed change proportional to frequency change of the STM | PV | physical/causal consistency+statistical stability | D5_P2_SC,D2_P2_PHASE | P2_SIT01,P4_ST_FD,P4_ST_GOV | Couples the HIL steam-turbine model to the rotor speed; invariant is consistency with P4_ST_FD and SIT01. | medium |
| `P2_SIT01` | P2 Turbine / P2-SC | Current turbine RPM measured by speed probe | PV | physical/causal consistency+temporal dependency+statistical stability+explicit physical/logical constraint | D5_P2_SC,D4_P2_SPEED_RAMP,D2_P2_PHASE,D1_P2_TRIP | P2_AutoSD,P2_ManualSD,P2_SCO,P2_RTR | Main controlled PV; invariants are setpoint tracking, ramp dynamics, stationarity and the trip threshold rule. | high |
| `P2_TripEx` | P2 Turbine / P2-TRIP | Trip emergency exit button | CMD | explicit physical/logical constraint | D1_P2_TRIP,D1_P2_MODE | P2_Emerg,P2_OnOff | Re-arms the turbine after a trip; must not be asserted while the trip condition still holds. | high |
| `P2_VIBTR01` | P2 Turbine / P2-TRIP | Shaft vibration, Y-axis near 1st mass wheel | PV | statistical stability+temporal dependency+explicit physical/logical constraint | D2_P2_VIB_DYN,D4_P2_VIB_DYNAMICS,D1_P2_TRIP | P2_VTR01,P2_VIBTR02,P2_SIT01 | Vibration is a zero-mean oscillatory signal; invariant is amplitude/envelope statistics plus the trip limit, not a fixed value. | high |
| `P2_VIBTR02` | P2 Turbine / P2-TRIP | Shaft vibration, X-axis near 1st mass wheel | PV | statistical stability+temporal dependency+explicit physical/logical constraint | D2_P2_VIB_DYN,D4_P2_VIB_DYNAMICS,D1_P2_TRIP | P2_VTR02,P2_VIBTR01,P2_SIT01 | Same invariant class as VIBTR01; cross-axis dependence with VIBTR01 handled by the dynamics detector. | high |
| `P2_VIBTR03` | P2 Turbine / P2-TRIP | Shaft vibration, Y-axis near 2nd mass wheel | PV | statistical stability+temporal dependency+explicit physical/logical constraint | D2_P2_VIB_DYN,D4_P2_VIB_DYNAMICS,D1_P2_TRIP | P2_VTR03,P2_VIBTR04,P2_SIT01 | Vibration envelope plus trip limit. | high |
| `P2_VIBTR04` | P2 Turbine / P2-TRIP | Shaft vibration, X-axis near 2nd mass wheel | PV | statistical stability+temporal dependency+explicit physical/logical constraint | D2_P2_VIB_DYN,D4_P2_VIB_DYNAMICS,D1_P2_TRIP | P2_VTR04,P2_VIBTR03,P2_SIT01 | Vibration envelope plus trip limit. | high |
| `P2_VT01` | P2 Turbine / P2-SC | Phase lag signal of the key phasor probe | PV | statistical stability | D2_P2_PHASE,D4_P2_VIB_DYNAMICS | P2_SIT01,P2_VIBTR01,P2_VIBTR03 | Rotor phase reference; invariant is a tight stationary band around ~11.95 rad/s. | medium |
| `P2_VTR01` | P2 Turbine / P2-TRIP | Preset vibration limit for P2_VIBTR01 | PROT | explicit physical/logical constraint | D1_P2_TRIP | P2_VIBTR01 | Protection threshold; invariant is the trip rule. | high |
| `P2_VTR02` | P2 Turbine / P2-TRIP | Preset vibration limit for P2_VIBTR02 | PROT | explicit physical/logical constraint | D1_P2_TRIP | P2_VIBTR02 | Protection threshold; invariant is the trip rule. | high |
| `P2_VTR03` | P2 Turbine / P2-TRIP | Preset vibration limit for P2_VIBTR03 | PROT | explicit physical/logical constraint | D1_P2_TRIP | P2_VIBTR03 | Protection threshold; invariant is the trip rule. | high |
| `P2_VTR04` | P2 Turbine / P2-TRIP | Preset vibration limit for P2_VIBTR04 | PROT | explicit physical/logical constraint | D1_P2_TRIP | P2_VIBTR04 | Protection threshold; invariant is the trip rule. | high |
| `P3_FIT01` | P3 Water treatment / P3-LC | Flow rate of water flowing into the upper tank | PV | statistical stability+physical/causal consistency | D2_P3_INFLOW,D5_P3_LEVEL,D5_P3_PUMP | P3_LCP01D,P3_LCV01D,P3_PIT01,P3_LIT01 | Inflow is driven by the level controller; invariant is stationarity and causal consistency with pump/valve demands. | medium |
| `P3_LCP01D` | P3 Water treatment / P3-LC | Speed command for the level-control pump LCP01 | CO | physical/causal consistency+temporal dependency+multivariate relationship | D5_P3_PUMP,D4_P3_LEVEL_DYN,D3_P3_DISPATCH | P3_FIT01,P3_PIT01,P3_LCV01D,P3_LIT01 | Pumping-demand actuator; invariant is its relation to inflow/pressure and coordination with the valve demand. | medium |
| `P3_LCV01D` | P3 Water treatment / P3-LC | Position command for the level-control valve LCV01 | CO | physical/causal consistency+temporal dependency+multivariate relationship | D5_P3_LEVEL,D4_P3_LEVEL_DYN,D3_P3_DISPATCH | P3_LIT01,P3_LCP01D,P3_FIT01 | Discharge-demand actuator of the reservoir level loop. | medium |
| `P3_LH01` | P3 Water Treatment / P3-LC | High water level setpoint | PROT | explicit physical/logical constraint | D1_P3_LEVELSW | P3_LIT01,P3_LL01 | High-level interlock threshold; invariant is the explicit limit. | medium |
| `P3_LIT01` | P3 Water Treatment / P3-LC | Water level of the upper water tank | PV | physical/causal consistency+statistical stability+temporal dependency+explicit physical/logical constraint | D5_P3_LEVEL,D2_P3_INFLOW,D4_P3_LEVEL_DYN,D1_P3_LEVELSW | P3_LCV01D,P3_LCP01D,P3_LH01,P3_LL01 | Controlled PV of P3-LC; invariants are setpoint/limit band, slow reservoir dynamics and mass balance with FIT01. | high |
| `P3_LL01` | P3 Water Treatment / P3-LC | Low water level setpoint | PROT | explicit physical/logical constraint | D1_P3_LEVELSW | P3_LIT01,P3_LH01 | Low-level interlock threshold. | medium |
| `P3_PIT01` | P3 Water Treatment / P3-LC | Pressure of water flowing into the upper tank | PV | statistical stability+physical/causal consistency | D2_P3_INFLOW,D5_P3_PUMP | P3_LCP01D,P3_FIT01 | Discharge head of the pump; invariant is a stationary relation with pump speed and flow. | medium |
| `P4_HT_FD` | P4 HIL / grid | Frequency deviation of HTM | SIM | statistical stability+physical/causal consistency | D2_P4_FREQ,D5_P4_FREQ_COUPLE | P4_HT_PO,P4_ST_FD,P4_LD | Grid-frequency deviation is zero-mean stationary noise; invariant is spectral/statistical behaviour and coupling to STM frequency. | medium |
| `P4_HT_PO` | P4 HIL / grid | Output power of HTM | SIM | physical/causal consistency+statistical stability | D5_P4_HT_POWER,D5_P4_LOAD_BAL,D2_P4_LOAD | P4_HT_PS,P4_LD,P4_ST_PO | Generated power must track the scheduled demand within a stationary residual band. | medium |
| `P4_HT_PS` | P4 HIL / grid | Scheduled power demand of HTM | SP | multivariate relationship+temporal dependency+explicit physical/logical constraint | D3_P4_LOAD_ALLOC,D4_P1_SP_SEQUENCE,D1_SETPOINT_ENVELOPE | P4_HT_PO,P4_ST_PS,P4_LD | HIL setpoint driven by the HMM normal model; invariant is the allowed envelope and load-allocation combination. | medium |
| `P4_LD` | P4 HIL / grid | Total electrical load demand | SP | multivariate relationship+physical/causal consistency+temporal dependency | D3_P4_LOAD_ALLOC,D5_P4_LOAD_BAL,D4_P1_SP_SEQUENCE | P4_ST_LD,P4_ST_PO,P4_HT_PO | Aggregate demand; invariant is the additive consistency with the per-unit demands and output powers. | medium |
| `P4_ST_FD` | P4 HIL / grid | Frequency deviation of STM | SIM | statistical stability+physical/causal consistency | D2_P4_FREQ,D5_P4_FREQ_COUPLE | P4_ST_PO,P2_SIT01,P4_HT_FD | Zero-mean frequency deviation; couples the HIL steam model to turbine speed. | medium |
| `P4_ST_GOV` | P4 HIL / grid | Gate opening rate of STM | SIM | physical/causal consistency+temporal dependency+statistical stability | D5_P4_ST_POWER,D4_P4_DYNAMICS,D2_P4_LOAD | P4_ST_LD,P4_ST_PO,P4_ST_PT01,P4_ST_TT01 | Governor/gate actuator; invariant is the slow mechanical ramp and the causal relation with power and steam pressure. | medium |
| `P4_ST_LD` | P4 HIL / grid | Electrical load demand of STM | SP | physical/causal consistency+multivariate relationship+temporal dependency | D5_P4_ST_POWER,D3_P4_LOAD_ALLOC,D4_P4_DYNAMICS | P4_ST_PO,P4_LD,P4_ST_GOV | Load demand; invariant is output-power tracking and consistency with the aggregate load. | medium |
| `P4_ST_PO` | P4 HIL / grid | Output power of STM | SIM | physical/causal consistency+statistical stability | D5_P4_ST_POWER,D5_P4_LOAD_BAL,D2_P4_LOAD | P4_ST_LD,P4_ST_GOV,P4_LD | Generated steam power; invariant is tracking of LD and consistency with governor opening. | medium |
| `P4_ST_PS` | P4 HIL / grid | Scheduled power demand of STM | SP | multivariate relationship+temporal dependency+explicit physical/logical constraint | D3_P4_LOAD_ALLOC,D4_P1_SP_SEQUENCE,D1_SETPOINT_ENVELOPE | P4_ST_LD,P4_HT_PS,P4_LD | HIL scheduled demand; envelope and allocation invariants. | medium |
| `P4_ST_PT01` | P4 HIL / steam | Digital value of steam pressure of STM | SIM | physical/causal consistency+statistical stability | D5_P4_STEAM,D2_P4_STEAM | P4_ST_TT01,P4_ST_GOV,P4_ST_PO,P1_PIT01 | Steam pressure must be physically consistent with steam temperature, governor opening and power; also observed coupled to boiler pressure. | medium |
| `P4_ST_TT01` | P4 HIL / steam | Digital value of steam temperature of STM | SIM | physical/causal consistency+statistical stability | D5_P4_STEAM,D2_P4_STEAM,D5_HEX_COUPLE | P4_ST_PT01,P4_ST_GOV,P1_TIT01 | Steam state variable; invariant is the steam-table consistency with pressure and the observed coupling to the heat-exchanger outlet temperature. | medium |
| `x1001_05_SETPOINT_OUT` | P1 Boiler / P1-PC internal | Internal setpoint output of control logic block 1001.05 | INT | temporal dependency+statistical stability+physical/causal consistency | D4_P1_SP_SEQUENCE,D2_P1_SENSOR_NOISE,D5_P1_PC_PRESS | P1_PIT01,P1_PCV01D,x1001_15_ASSIGN_OUT | Empirically couples to P1_PIT01 (rho~0.40) and PCV01. Functional role inferred from naming and correlation, not documented in the HAI point table. | low |
| `x1001_15_ASSIGN_OUT` | P1 Boiler / P1-PC internal | Assigned pressure setpoint (equivalent of operator setpoint P1_B2016) | INT | temporal dependency+physical/causal consistency+multivariate relationship | D4_P1_SP_SEQUENCE,D5_P1_PC_PRESS,D3_P1_SP_GROUP | P1_PIT01,P4_ST_PO,P4_ST_GOV,P1_PCV01D | Best matching driver of P1_PIT01 (residual std ~0.1 bar). Strongly co-varies with the steam-turbine load (rho ~0.9). Treated as the pressure-loop setpoint but needs expert confirmation. | medium |
| `x1002_07_SETPOINT_OUT` | P1 Boiler / P1-LC internal | Internal level setpoint (equivalent of P1_B3004) | INT | physical/causal consistency+temporal dependency+multivariate relationship | D5_P1_LC_LEVEL,D4_P1_SP_SEQUENCE,D3_P1_SP_GROUP | P1_LIT01,P1_LCV01D,P1_FT03Z | Near-perfect correlation (rho~0.97) with P1_LIT01 identifies it as the level-loop setpoint. | medium |
| `x1002_08_SETPOINT_OUT` | P1 Boiler / P1-FC internal | Internal flow setpoint (equivalent of P1_B3005) | INT | physical/causal consistency+temporal dependency+multivariate relationship | D5_P1_FC03_FLOW,D4_P1_SP_SEQUENCE,D3_P1_SP_GROUP | P1_FT03,P1_FT03Z,P1_FCV03D,P1_FT01 | rho~0.99 with P1_FT03Z identifies it as the outflow-rate setpoint. | medium |
| `x1003_10_SETPOINT_OUT` | P1 Boiler / P1-TC internal | Internal heat-transfer flow setpoint (equivalent of P1_B400B) | INT | physical/causal consistency+temporal dependency+multivariate relationship | D5_P1_FC02_FLOW,D4_P1_SP_SEQUENCE,D3_P1_SP_GROUP | P1_FT02,P1_FT02Z,P1_FCV01Z,P1_FCV02Z | rho~0.996 with P1_FT02Z identifies it as the heating-water flow setpoint. | medium |
| `x1003_18_SETPOINT_OUT` | P1 Boiler / P1-TC internal | Internal temperature/loop setpoint of control logic block 1003.18 | INT | temporal dependency+statistical stability+physical/causal consistency | D4_P1_SP_SEQUENCE,D2_P1_SENSOR_NOISE,D5_P1_TC_TEMP | P1_TIT01,P1_PP04SP,x1003_24_SUM_OUT | Correlates with PP04SP, TIT01 and steam temperature (rho~0.4); exact role requires the HAIEnd control-logic graph. | low |
| `x1003_24_SUM_OUT` | P1 Boiler / P1-TC internal | Sum/arithmetic output of control logic block 1003.24 (cascade term) | INT | temporal dependency+statistical stability+physical/causal consistency | D4_P1_SP_SEQUENCE,D2_P1_SENSOR_NOISE,D5_P1_TC_TEMP | x1003_18_SETPOINT_OUT,P1_TIT01,P1_FCV01D | Near-constant (27.96-33.09) arithmetic output; correlates with the TC/CC group. Role inferred only. | low |

---

## B. Functional detector groups

Each row defines one local detector: class, purpose, input variable set, process scope, monitored invariant, training/calibration requirement and related detector groups. `training_requirement` follows the prompt vocabulary: `none`, `calibration`, `normal-data-training`, `relationship-learning`.

| Detector ID | Class | Functional purpose | Input variables | Scope | Monitored invariant | Training/calibration requirement | Related detectors |
|---|---|---|---|---|---|---|---|
| `D1_BLR_INTERLOCK` | D1 | Verify boiler start/stop and pump interlock logic (commands, running feedback and boiler run state are mutually legal) and forbid inconsistent transitions. | `P1_STSP`, `P1_PP01AD`, `P1_PP01AR`, `P1_PP01BD`, `P1_PP01BR`, `P1_PP02D`, `P1_PP02R`, `P1_PP04D` | P1 Boiler | explicit logical interlock; forbidden state/transition combinations | none (predefined rules) | D1_P1_VALVE_PERMISSIVE,D4_P1_THERMAL |
| `D1_P1_VALVE_PERMISSIVE` | D1 | Enforce valve permissives and minimum-opening rule (supply/drain exclusivity, PCV02/FCV02 recirculation minimum) on the boiler water circuit. | `P1_SOL01D`, `P1_SOL03D`, `P1_PCV02D`, `P1_FCV02D` | P1 Boiler | explicit valve permissive and minimum-flow constraint | none (predefined rules) | D1_BLR_INTERLOCK,D3_P1_PC_SPLIT |
| `D1_P1_HH_TRIP` | D1 | Check the high-high pressure protection rule for the heat exchanger. | `P1_PIT01`, `P1_PIT01_HH` | P1-PC | explicit protection threshold (PIT01 must stay below HH) | none (predefined rules) | D5_P1_PC_PRESS |
| `D1_P1_VALVE_RANGE` | D1 | Validate engineering ranges and per-valve limits of all P1 actuator commands. | `P1_FCV01D`, `P1_FCV02D`, `P1_FCV03D`, `P1_LCV01D`, `P1_PCV01D`, `P1_PCV02D` | P1 Boiler | explicit engineering range [0,100]% and per-valve limit | none (predefined rules) | D1_P1_VALVE_PERMISSIVE |
| `D1_P2_TRIP` | D1 | Evaluate the turbine over-speed and over-vibration trip logic (Emerg only when SIT01>RTR or \|VIBTR[n]\|>VTR[n]). | `P2_SIT01`, `P2_RTR`, `P2_VIBTR01`, `P2_VIBTR02`, `P2_VIBTR03`, `P2_VIBTR04`, `P2_VTR01`, `P2_VTR02`, `P2_VTR03`, `P2_VTR04`, `P2_Emerg`, `P2_TripEx` | P2 Turbine | explicit protection rule; forbidden trip states | none (predefined rules) | D1_P2_MODE,D4_P2_SPEED_RAMP |
| `D1_P2_MODE` | D1 | Verify turbine operator-mode, button and lamp state consistency (auto/manual selection, on/off, emergency, trip exit). | `P2_OnOff`, `P2_Emerg`, `P2_TripEx`, `P2_ManualGO`, `P2_AutoGO`, `P2_MASW`, `P2_MASW_Lamp`, `P2_ATSW_Lamp` | P2 Turbine | explicit state-machine and HMI feedback rules | none (predefined rules) | D3_P2_SP_MODE,D1_P2_TRIP |
| `D1_P3_LEVELSW` | D1 | Check reservoir high/low level protection thresholds. | `P3_LIT01`, `P3_LH01`, `P3_LL01` | P3 Water Treatment | explicit protection thresholds | none (predefined rules) | D5_P3_LEVEL |
| `D1_SETPOINT_ENVELOPE` | D1 | Validate that every setpoint stays inside its experimentally validated normal range. | `x1001_05_SETPOINT_OUT`, `x1001_15_ASSIGN_OUT`, `x1002_07_SETPOINT_OUT`, `x1002_08_SETPOINT_OUT`, `x1003_10_SETPOINT_OUT`, `x1003_18_SETPOINT_OUT`, `P1_PP04SP`, `P2_AutoSD`, `P2_ManualSD`, `P4_HT_PS`, `P4_ST_PS` | Plant-wide | explicit normal operating envelope of setpoints | none (predefined rules) | D4_P1_SP_SEQUENCE,D3_P1_SP_GROUP |
| `D1_P4_DEMAND_RANGE` | D1 | Validate HIL demand signals against the normal generation envelope. | `P4_HT_PS`, `P4_ST_PS`, `P4_LD`, `P4_HT_PO`, `P4_ST_PO` | P4 HIL | explicit operating envelope of demand/output powers | none (predefined rules) | D3_P4_LOAD_ALLOC |
| `D2_P1_VALVE_POS` | D2 | Monitor statistical stability, noise level and slow drift of boiler valve position feedbacks. | `P1_FCV01Z`, `P1_FCV02Z`, `P1_FCV03Z`, `P1_LCV01Z`, `P1_PCV01Z` | P1 Boiler | stationary distribution, bounded noise, no slow drift | calibration (normal-operation data) | D5_P1_FCV01_TRACK,D5_P1_FCV02_TRACK,D5_P1_FCV03_TRACK,D5_P1_LCV01_TRACK |
| `D2_P1_SENSOR_NOISE` | D2 | Characterize stability/variability and detect drift or abrupt change on boiler process variables. | `P1_PIT01`, `P1_LIT01`, `P1_TIT01`, `P1_TIT02`, `P1_FT01Z`, `P1_FT02Z`, `P1_FT03Z` | P1 Boiler | statistical stationarity and drift-free normal behaviour | calibration (normal-operation data) | D5_P1_TC_TEMP,D5_P1_LC_LEVEL |
| `D2_P1_AUX_PRESSURE` | D2 | Monitor the auxiliary pressure and cooling-pump output operating band. | `P1_PIT02`, `P1_PP04` | P1 Boiler | stationary band of auxiliary pressure/cooling output | calibration (normal-operation data) | D5_P1_CC_COOLING,D5_PC_PV_FLOW |
| `D2_P1_COOL_TEMP` | D2 | Monitor main-tank cooling temperature stability and drift. | `P1_TIT03` | P1-CC | stationary thermal band | calibration (normal-operation data) | D5_P1_CC_COOLING |
| `D2_P2_ELECTRICAL` | D2 | Monitor turbine DCS supply voltage and speed-controller output statistics. | `P2_24Vdc`, `P2_SCO` | P2 Turbine | tight stationary band / bounded variance | calibration (normal-operation data) | D5_P2_SC |
| `D2_P2_VIB_DYN` | D2 | Characterize vibration amplitude/envelope statistics of the four shaft probes. | `P2_VIBTR01`, `P2_VIBTR02`, `P2_VIBTR03`, `P2_VIBTR04` | P2 Turbine | zero-mean oscillation, stable RMS/envelope | calibration (normal-operation data) | D4_P2_VIB_DYNAMICS,D1_P2_TRIP |
| `D2_P2_PHASE` | D2 | Monitor the key-phasor phase-lag stationarity and coupling to rotor speed. | `P2_VT01`, `P2_SCST` | P2 Turbine | stationary phase-lag band | calibration (normal-operation data) | D5_P2_SC |
| `D2_P3_INFLOW` | D2 | Monitor inflow flow-rate and pressure stationarity in the water-treatment process. | `P3_FIT01`, `P3_PIT01` | P3 Water Treatment | statistical stationarity / bounded variance | calibration (normal-operation data) | D5_P3_PUMP,D5_P3_LEVEL |
| `D2_P4_FREQ` | D2 | Characterize grid-frequency deviation statistics for STM and HTM. | `P4_ST_FD`, `P4_HT_FD` | P4 HIL | zero-mean stationary deviation with stable spectrum | calibration (normal-operation data) | D5_P4_FREQ_COUPLE |
| `D2_P4_LOAD` | D2 | Monitor stationarity of HIL output power and governor signals. | `P4_ST_PO`, `P4_HT_PO`, `P4_ST_GOV` | P4 HIL | stationary residual around scheduled demand | calibration (normal-operation data) | D5_P4_ST_POWER,D5_P4_LOAD_BAL |
| `D2_P4_STEAM` | D2 | Monitor steam pressure/temperature statistical stability. | `P4_ST_PT01`, `P4_ST_TT01` | P4 HIL | stationary steam state within a narrow band | calibration (normal-operation data) | D5_P4_STEAM,D5_HEX_COUPLE |
| `D3_P1_PC_SPLIT` | D3 | Detect abnormal simultaneous configuration of the two pressure-control valves (transfer PCV01 vs recirculation PCV02) even when each position is individually valid. | `P1_PCV01D`, `P1_PCV01Z`, `P1_PCV02D`, `P1_PCV02Z` | P1-PC | multivariate valve-split configuration | normal-data-training | D5_P1_PC_PRESS,D1_P1_VALVE_PERMISSIVE |
| `D3_P1_TC_SPLIT` | D3 | Detect abnormal simultaneous configuration of the heat-exchanger branch valves FCV01/FCV02. | `P1_FCV01D`, `P1_FCV01Z`, `P1_FCV02D`, `P1_FCV02Z` | P1-TC | multivariate branch-split configuration | normal-data-training | D5_P1_FCV01_TRACK,D5_P1_FCV02_TRACK |
| `D3_P2_SP_MODE` | D3 | Detect an invalid combination of active speed setpoint and manual/auto mode selection. | `P2_AutoSD`, `P2_ManualSD`, `P2_MASW`, `P2_MASW_Lamp`, `P2_AutoGO`, `P2_ManualGO` | P2-SC | mode/setpoint configuration consistency | normal-data-training | D1_P2_MODE,D5_P2_SC |
| `D3_P3_DISPATCH` | D3 | Detect abnormal simultaneous pumping/discharge demand combination of the level loop. | `P3_LCP01D`, `P3_LCV01D` | P3-LC | demand-allocation configuration | normal-data-training | D5_P3_LEVEL,D5_P3_PUMP |
| `D3_P4_LOAD_ALLOC` | D3 | Detect abnormal combination of total load and per-unit scheduled demands that is individually in range but violates load allocation. | `P4_LD`, `P4_HT_PS`, `P4_ST_PS`, `P4_HT_PO`, `P4_ST_PO` | P4 HIL | load-allocation configuration | normal-data-training | D5_P4_LOAD_BAL,D5_P4_ST_POWER |
| `D3_P1_SP_GROUP` | D3 | Detect abnormal simultaneous setpoint combinations across boiler loops. | `x1002_07_SETPOINT_OUT`, `x1002_08_SETPOINT_OUT`, `x1003_10_SETPOINT_OUT`, `P1_PP04SP` | P1 Boiler | coupled setpoint configuration | normal-data-training | D4_P1_SP_SEQUENCE,D1_SETPOINT_ENVELOPE |
| `D4_P1_SP_SEQUENCE` | D4 | Model the temporal sequence, dwell time and transition shape of operator/HIL setpoint changes (HMM-scheduled normal operation). | `x1001_05_SETPOINT_OUT`, `x1001_15_ASSIGN_OUT`, `x1002_07_SETPOINT_OUT`, `x1002_08_SETPOINT_OUT`, `x1003_10_SETPOINT_OUT`, `x1003_18_SETPOINT_OUT`, `P1_PP04SP`, `P2_AutoSD`, `P2_ManualSD`, `P4_HT_PS`, `P4_ST_PS` | Plant-wide | setpoint sequence / dwell / trapezoidal-ramp structure | normal-data-training | D3_P1_SP_GROUP,D3_P4_LOAD_ALLOC |
| `D4_P1_FCV_PROFILE` | D4 | Model rate-limited valve-command trajectories and actuator inertia for all P1 control valves. | `P1_FCV01D`, `P1_FCV02D`, `P1_FCV03D`, `P1_LCV01D`, `P1_PCV01D`, `P1_PCV02D` | P1 Boiler | temporal evolution: saturation rate limits, no abrupt steps | normal-data-training | D5_P1_FCV01_TRACK,D5_P1_FCV03_TRACK |
| `D4_P1_LIT_INERTIA` | D4 | Model return-tank level dynamics driven by in/outflow (feed-forward structure). | `P1_LIT01`, `P1_FCV03D`, `P1_LCV01D`, `P1_FT03Z`, `P1_FT01Z` | P1-LC | temporal inertia / delay of tank level | normal-data-training | D5_P1_LC_LEVEL,D5_P1_FC03_FLOW |
| `D4_P1_THERMAL` | D4 | Model thermal inertia of the boiler, heating tank and cooler response. | `P1_TIT01`, `P1_TIT02`, `P1_TIT03`, `P1_FCV01D`, `P1_FCV02D`, `P1_PP04` | P1 Boiler | temporal thermal dynamics / delays | normal-data-training | D5_P1_TC_TEMP,D5_P1_CC_COOLING |
| `D4_P2_SPEED_RAMP` | D4 | Model the turbine speed ramp (zero to minimum speed at constant rate) and PID settling dynamics. | `P2_AutoSD`, `P2_ManualSD`, `P2_SIT01`, `P2_SCO` | P2-SC | temporal ramp / inertia / settling | normal-data-training | D5_P2_SC,D1_P2_TRIP |
| `D4_P2_VIB_DYNAMICS` | D4 | Model the temporal/oscillatory dependence between the four vibration probes and the phase signal. | `P2_VIBTR01`, `P2_VIBTR02`, `P2_VIBTR03`, `P2_VIBTR04`, `P2_VT01` | P2 Turbine | temporal waveform / cross-probe dependence | normal-data-training | D2_P2_VIB_DYN |
| `D4_P3_LEVEL_DYN` | D4 | Model reservoir level dynamics and pump/valve response delays. | `P3_LIT01`, `P3_LCP01D`, `P3_LCV01D`, `P3_FIT01` | P3-LC | temporal reservoir dynamics / delays | normal-data-training | D5_P3_LEVEL |
| `D4_P4_DYNAMICS` | D4 | Model HIL generator load-following, governor-ramp and gate-opening dynamics. | `P4_ST_GOV`, `P4_ST_LD`, `P4_ST_PO`, `P4_HT_PO`, `P4_LD` | P4 HIL | temporal load-following dynamics | normal-data-training | D5_P4_ST_POWER,D5_P4_LOAD_BAL |
| `D5_P1_FCV01_TRACK` | D5 | Residual between FCV01 command and measured position. | `P1_FCV01D`, `P1_FCV01Z` | P1-TC | actuator command/feedback consistency | relationship-learning (normal-operation data) | D3_P1_TC_SPLIT,D4_P1_FCV_PROFILE |
| `D5_P1_FCV02_TRACK` | D5 | Residual between FCV02 command and measured position (large actuator lag). | `P1_FCV02D`, `P1_FCV02Z` | P1-TC | actuator command/feedback consistency | relationship-learning (normal-operation data) | D3_P1_TC_SPLIT,D4_P1_FCV_PROFILE |
| `D5_P1_FCV03_TRACK` | D5 | Residual between FCV03 command and measured position. | `P1_FCV03D`, `P1_FCV03Z` | P1-FC | actuator command/feedback consistency | relationship-learning (normal-operation data) | D5_P1_FC03_FLOW |
| `D5_P1_LCV01_TRACK` | D5 | Residual between LCV01 command and measured position. | `P1_LCV01D`, `P1_LCV01Z` | P1-LC | actuator command/feedback consistency | relationship-learning (normal-operation data) | D5_P1_LC_LEVEL |
| `D5_P1_PCV01_TRACK` | D5 | Residual between PCV01 command and measured position. | `P1_PCV01D`, `P1_PCV01Z` | P1-PC | actuator command/feedback consistency | relationship-learning (normal-operation data) | D5_P1_PC_PRESS,D3_P1_PC_SPLIT |
| `D5_P1_PCV02_TRACK` | D5 | Residual between PCV02 command and measured position. | `P1_PCV02D`, `P1_PCV02Z` | P1-PC | actuator command/feedback consistency | relationship-learning (normal-operation data) | D3_P1_PC_SPLIT |
| `D5_P1_FC03_FLOW` | D5 | Residual between the outflow setpoint and measured outflow rate (P1-FC loop closure). | `x1002_08_SETPOINT_OUT`, `P1_FT03Z`, `P1_FT03`, `P1_FCV03Z` | P1-FC | setpoint/PV control-loop consistency | relationship-learning (normal-operation data) | D5_P1_FCV03_TRACK,D4_P1_LIT_INERTIA |
| `D5_P1_FC02_FLOW` | D5 | Residual between the heat-transfer flow setpoint and measured FT02 flow. | `x1003_10_SETPOINT_OUT`, `P1_FT02Z`, `P1_FT02`, `P1_FCV01Z` | P1-TC | setpoint/PV control-loop consistency | relationship-learning (normal-operation data) | D5_P1_TC_TEMP,D3_P1_TC_SPLIT |
| `D5_P1_LC_LEVEL` | D5 | Residual between the level setpoint and measured tank level (P1-LC loop closure). | `x1002_07_SETPOINT_OUT`, `P1_LIT01`, `P1_LCV01Z`, `P1_FT03Z` | P1-LC | setpoint/PV control-loop consistency | relationship-learning (normal-operation data) | D5_P1_LCV01_TRACK,D4_P1_LIT_INERTIA |
| `D5_P1_TC_TEMP` | D5 | Residual between the temperature setpoint and measured TIT01, including the valve/flow inner loop. | `x1003_18_SETPOINT_OUT`, `P1_TIT01`, `P1_FCV01D`, `P1_FCV02D`, `P1_FT02Z` | P1-TC | cascade setpoint/PV and inner-loop consistency | relationship-learning (normal-operation data) | D5_P1_FC02_FLOW,D5_HEX_COUPLE |
| `D5_P1_PC_PRESS` | D5 | Residual between the assigned pressure setpoint and measured PIT01 (P1-PC loop closure). | `x1001_15_ASSIGN_OUT`, `x1001_05_SETPOINT_OUT`, `P1_PIT01`, `P1_PCV01Z`, `P1_PCV02Z` | P1-PC | setpoint/PV control-loop consistency | relationship-learning (normal-operation data) | D5_P1_PCV01_TRACK,D1_P1_HH_TRIP |
| `D5_P1_CC_COOLING` | D5 | Causal consistency between cooler-pump output, cooler setpoint and main-tank temperature. | `P1_PP04`, `P1_PP04SP`, `P1_PP04D`, `P1_TIT03` | P1-CC | actuator/cooling-demand causality | relationship-learning (normal-operation data) | D4_P1_THERMAL,D2_P1_COOL_TEMP |
| `D5_P1_MASS_BALANCE` | D5 | Mass-balance consistency of the return tank (inflow - outflow vs level change). | `P1_FT01Z`, `P1_FT03Z`, `P1_LIT01`, `P1_FT02Z` | P1 Boiler | physical mass-conservation relation | relationship-learning (normal-operation data) | D4_P1_LIT_INERTIA,D5_PC_PV_FLOW |
| `D5_P2_SC` | D5 | Speed-loop consistency: SIT01 vs active setpoint vs controller output and STM frequency coupling. | `P2_SIT01`, `P2_AutoSD`, `P2_ManualSD`, `P2_SCO`, `P2_SCST` | P2-SC | speed control-loop and HIL coupling consistency | relationship-learning (normal-operation data) | D4_P2_SPEED_RAMP,D5_P4_FREQ_COUPLE |
| `D5_P3_LEVEL` | D5 | Reservoir level-loop consistency: LIT01 vs valve/pump demands and inflow. | `P3_LIT01`, `P3_LCV01D`, `P3_LCP01D`, `P3_FIT01`, `P3_PIT01` | P3-LC | level control-loop / mass-balance consistency | relationship-learning (normal-operation data) | D4_P3_LEVEL_DYN,D3_P3_DISPATCH |
| `D5_P3_PUMP` | D5 | Pump consistency: speed command vs discharge pressure and flow. | `P3_LCP01D`, `P3_PIT01`, `P3_FIT01` | P3-LC | pump actuator/head/flow consistency | relationship-learning (normal-operation data) | D2_P3_INFLOW,D5_P3_LEVEL |
| `D5_P4_ST_POWER` | D5 | Steam-turbine generation consistency: load demand vs output power vs governor opening. | `P4_ST_LD`, `P4_ST_PO`, `P4_ST_GOV` | P4 HIL | power-balance / actuator causality | relationship-learning (normal-operation data) | D4_P4_DYNAMICS,D3_P4_LOAD_ALLOC |
| `D5_P4_HT_POWER` | D5 | Hydro/thermal-machine generation consistency: scheduled demand vs output power. | `P4_HT_PS`, `P4_HT_PO` | P4 HIL | power-balance consistency | relationship-learning (normal-operation data) | D3_P4_LOAD_ALLOC |
| `D5_P4_LOAD_BAL` | D5 | Aggregate load consistency: total demand vs sum of STM/HTM output powers. | `P4_LD`, `P4_ST_PO`, `P4_HT_PO`, `P4_ST_LD`, `P4_HT_PS` | P4 HIL | load-allocation / energy-balance consistency | relationship-learning (normal-operation data) | D5_P4_ST_POWER,D5_P4_HT_POWER |
| `D5_P4_FREQ_COUPLE` | D5 | Frequency coupling between steam-turbine model frequency and turbine rotor speed / HTM frequency. | `P4_ST_FD`, `P4_HT_FD`, `P2_SCST`, `P2_SIT01` | P4 HIL / P2 | physical frequency coupling | relationship-learning (normal-operation data) | D5_P2_SC,D4_P2_SPEED_RAMP |
| `D5_P4_STEAM` | D5 | Steam-state consistency: pressure vs temperature vs governor opening vs power. | `P4_ST_PT01`, `P4_ST_TT01`, `P4_ST_GOV`, `P4_ST_PO` | P4 HIL | thermodynamic/hydraulic consistency | relationship-learning (normal-operation data) | D2_P4_STEAM,D5_P4_ST_POWER |
| `D5_HEX_COUPLE` | D5 | Cross-subsystem coupling between boiler heat-exchanger temperature and HIL steam temperature / pressure. | `P1_TIT01`, `P1_PIT01`, `P4_ST_TT01`, `P4_ST_PT01` | P1 Boiler / P4 HIL | cross-subsystem physical coupling | relationship-learning (normal-operation data) | D5_P1_TC_TEMP,D5_P4_STEAM |
| `D5_PC_PV_FLOW` | D5 | Auxiliary pressure/flow consistency of the boiler water circuit. | `P1_PIT01`, `P1_PIT02`, `P1_FT01Z`, `P1_FT02Z` | P1-PC | hydraulic consistency between pressures and flows | relationship-learning (normal-operation data) | D5_P1_MASS_BALANCE,D2_P1_AUX_PRESSURE |

---

## C. Routing map

Mapping `process variable -> detector instance(s)`; a variable may be routed to multiple instances.

| Process variable | Detector instance(s) |
|---|---|
| `P1_FCV01D` | `D5_P1_FCV01_TRACK`, `D4_P1_FCV_PROFILE`, `D3_P1_TC_SPLIT` |
| `P1_FCV01Z` | `D5_P1_FCV01_TRACK`, `D2_P1_VALVE_POS`, `D4_P1_FCV_PROFILE` |
| `P1_FCV02D` | `D5_P1_FCV02_TRACK`, `D4_P1_FCV_PROFILE`, `D1_P1_VALVE_RANGE`, `D3_P1_TC_SPLIT` |
| `P1_FCV02Z` | `D5_P1_FCV02_TRACK`, `D2_P1_VALVE_POS`, `D1_P1_VALVE_RANGE` |
| `P1_FCV03D` | `D5_P1_FCV03_TRACK`, `D4_P1_FCV_PROFILE` |
| `P1_FCV03Z` | `D5_P1_FCV03_TRACK`, `D2_P1_VALVE_POS` |
| `P1_FT01` | `D5_PC_PV_FLOW`, `D2_P1_SENSOR_NOISE`, `D4_P1_LIT_INERTIA` |
| `P1_FT01Z` | `D5_PC_PV_FLOW`, `D5_P1_MASS_BALANCE`, `D2_P1_SENSOR_NOISE` |
| `P1_FT02` | `D5_P1_TC_TEMP`, `D2_P1_SENSOR_NOISE`, `D4_P1_THERMAL` |
| `P1_FT02Z` | `D5_P1_FC02_FLOW`, `D2_P1_SENSOR_NOISE` |
| `P1_FT03` | `D5_P1_FC03_FLOW`, `D2_P1_SENSOR_NOISE`, `D4_P1_LIT_INERTIA` |
| `P1_FT03Z` | `D5_P1_FC03_FLOW`, `D5_P1_MASS_BALANCE`, `D2_P1_SENSOR_NOISE` |
| `P1_LCV01D` | `D5_P1_LCV01_TRACK`, `D4_P1_FCV_PROFILE` |
| `P1_LCV01Z` | `D5_P1_LCV01_TRACK`, `D2_P1_VALVE_POS` |
| `P1_LIT01` | `D5_P1_LC_LEVEL`, `D2_P1_SENSOR_NOISE`, `D4_P1_LIT_INERTIA`, `D5_P1_MASS_BALANCE` |
| `P1_PCV01D` | `D5_P1_PCV01_TRACK`, `D4_P1_FCV_PROFILE`, `D3_P1_PC_SPLIT` |
| `P1_PCV01Z` | `D5_P1_PCV01_TRACK`, `D2_P1_VALVE_POS` |
| `P1_PCV02D` | `D3_P1_PC_SPLIT`, `D1_P1_VALVE_RANGE`, `D4_P1_FCV_PROFILE` |
| `P1_PCV02Z` | `D3_P1_PC_SPLIT`, `D5_P1_PCV02_TRACK` |
| `P1_PIT01` | `D5_P1_PC_PRESS`, `D1_P1_HH_TRIP`, `D2_P1_SENSOR_NOISE` |
| `P1_PIT01_HH` | `D1_P1_HH_TRIP` |
| `P1_PIT02` | `D2_P1_AUX_PRESSURE`, `D5_PC_PV_FLOW` |
| `P1_PP01AD` | `D1_BLR_INTERLOCK` |
| `P1_PP01AR` | `D1_BLR_INTERLOCK` |
| `P1_PP01BD` | `D1_BLR_INTERLOCK` |
| `P1_PP01BR` | `D1_BLR_INTERLOCK` |
| `P1_PP02D` | `D1_BLR_INTERLOCK` |
| `P1_PP02R` | `D1_BLR_INTERLOCK` |
| `P1_PP04` | `D5_P1_CC_COOLING`, `D4_P1_THERMAL`, `D2_P1_AUX_PRESSURE` |
| `P1_PP04D` | `D1_BLR_INTERLOCK` |
| `P1_PP04SP` | `D1_SETPOINT_ENVELOPE`, `D4_P1_SP_SEQUENCE`, `D3_P1_SP_GROUP` |
| `P1_SOL01D` | `D1_P1_VALVE_PERMISSIVE` |
| `P1_SOL03D` | `D1_P1_VALVE_PERMISSIVE` |
| `P1_STSP` | `D1_BLR_INTERLOCK` |
| `P1_TIT01` | `D5_P1_TC_TEMP`, `D2_P1_SENSOR_NOISE`, `D4_P1_THERMAL`, `D5_HEX_COUPLE` |
| `P1_TIT02` | `D2_P1_SENSOR_NOISE`, `D4_P1_THERMAL`, `D5_P1_TC_TEMP` |
| `P1_TIT03` | `D5_P1_CC_COOLING`, `D2_P1_COOL_TEMP`, `D4_P1_THERMAL` |
| `P2_24Vdc` | `D2_P2_ELECTRICAL` |
| `P2_ATSW_Lamp` | `D1_P2_MODE` |
| `P2_AutoGO` | `D1_P2_MODE`, `D3_P2_SP_MODE` |
| `P2_AutoSD` | `D4_P2_SPEED_RAMP`, `D5_P2_SC`, `D3_P2_SP_MODE` |
| `P2_Emerg` | `D1_P2_TRIP`, `D1_P2_MODE` |
| `P2_MASW` | `D1_P2_MODE`, `D3_P2_SP_MODE` |
| `P2_MASW_Lamp` | `D1_P2_MODE` |
| `P2_ManualGO` | `D1_P2_MODE`, `D3_P2_SP_MODE` |
| `P2_ManualSD` | `D4_P2_SPEED_RAMP`, `D5_P2_SC`, `D3_P2_SP_MODE` |
| `P2_OnOff` | `D1_P2_MODE` |
| `P2_RTR` | `D1_P2_TRIP` |
| `P2_SCO` | `D5_P2_SC`, `D2_P2_ELECTRICAL`, `D4_P2_SPEED_RAMP` |
| `P2_SCST` | `D5_P2_SC`, `D2_P2_PHASE` |
| `P2_SIT01` | `D5_P2_SC`, `D4_P2_SPEED_RAMP`, `D2_P2_PHASE`, `D1_P2_TRIP` |
| `P2_TripEx` | `D1_P2_TRIP`, `D1_P2_MODE` |
| `P2_VIBTR01` | `D2_P2_VIB_DYN`, `D4_P2_VIB_DYNAMICS`, `D1_P2_TRIP` |
| `P2_VIBTR02` | `D2_P2_VIB_DYN`, `D4_P2_VIB_DYNAMICS`, `D1_P2_TRIP` |
| `P2_VIBTR03` | `D2_P2_VIB_DYN`, `D4_P2_VIB_DYNAMICS`, `D1_P2_TRIP` |
| `P2_VIBTR04` | `D2_P2_VIB_DYN`, `D4_P2_VIB_DYNAMICS`, `D1_P2_TRIP` |
| `P2_VT01` | `D2_P2_PHASE`, `D4_P2_VIB_DYNAMICS` |
| `P2_VTR01` | `D1_P2_TRIP` |
| `P2_VTR02` | `D1_P2_TRIP` |
| `P2_VTR03` | `D1_P2_TRIP` |
| `P2_VTR04` | `D1_P2_TRIP` |
| `P3_FIT01` | `D2_P3_INFLOW`, `D5_P3_LEVEL`, `D5_P3_PUMP` |
| `P3_LCP01D` | `D5_P3_PUMP`, `D4_P3_LEVEL_DYN`, `D3_P3_DISPATCH` |
| `P3_LCV01D` | `D5_P3_LEVEL`, `D4_P3_LEVEL_DYN`, `D3_P3_DISPATCH` |
| `P3_LH01` | `D1_P3_LEVELSW` |
| `P3_LIT01` | `D5_P3_LEVEL`, `D2_P3_INFLOW`, `D4_P3_LEVEL_DYN`, `D1_P3_LEVELSW` |
| `P3_LL01` | `D1_P3_LEVELSW` |
| `P3_PIT01` | `D2_P3_INFLOW`, `D5_P3_PUMP` |
| `P4_HT_FD` | `D2_P4_FREQ`, `D5_P4_FREQ_COUPLE` |
| `P4_HT_PO` | `D5_P4_HT_POWER`, `D5_P4_LOAD_BAL`, `D2_P4_LOAD` |
| `P4_HT_PS` | `D3_P4_LOAD_ALLOC`, `D4_P1_SP_SEQUENCE`, `D1_SETPOINT_ENVELOPE` |
| `P4_LD` | `D3_P4_LOAD_ALLOC`, `D5_P4_LOAD_BAL`, `D4_P1_SP_SEQUENCE` |
| `P4_ST_FD` | `D2_P4_FREQ`, `D5_P4_FREQ_COUPLE` |
| `P4_ST_GOV` | `D5_P4_ST_POWER`, `D4_P4_DYNAMICS`, `D2_P4_LOAD` |
| `P4_ST_LD` | `D5_P4_ST_POWER`, `D3_P4_LOAD_ALLOC`, `D4_P4_DYNAMICS` |
| `P4_ST_PO` | `D5_P4_ST_POWER`, `D5_P4_LOAD_BAL`, `D2_P4_LOAD` |
| `P4_ST_PS` | `D3_P4_LOAD_ALLOC`, `D4_P1_SP_SEQUENCE`, `D1_SETPOINT_ENVELOPE` |
| `P4_ST_PT01` | `D5_P4_STEAM`, `D2_P4_STEAM` |
| `P4_ST_TT01` | `D5_P4_STEAM`, `D2_P4_STEAM`, `D5_HEX_COUPLE` |
| `x1001_05_SETPOINT_OUT` | `D4_P1_SP_SEQUENCE`, `D2_P1_SENSOR_NOISE`, `D5_P1_PC_PRESS` |
| `x1001_15_ASSIGN_OUT` | `D4_P1_SP_SEQUENCE`, `D5_P1_PC_PRESS`, `D3_P1_SP_GROUP` |
| `x1002_07_SETPOINT_OUT` | `D5_P1_LC_LEVEL`, `D4_P1_SP_SEQUENCE`, `D3_P1_SP_GROUP` |
| `x1002_08_SETPOINT_OUT` | `D5_P1_FC03_FLOW`, `D4_P1_SP_SEQUENCE`, `D3_P1_SP_GROUP` |
| `x1003_10_SETPOINT_OUT` | `D5_P1_FC02_FLOW`, `D4_P1_SP_SEQUENCE`, `D3_P1_SP_GROUP` |
| `x1003_18_SETPOINT_OUT` | `D4_P1_SP_SEQUENCE`, `D2_P1_SENSOR_NOISE`, `D5_P1_TC_TEMP` |
| `x1003_24_SUM_OUT` | `D4_P1_SP_SEQUENCE`, `D2_P1_SENSOR_NOISE`, `D5_P1_TC_TEMP` |

---

## D. Training / configuration plan

For each detector instance, the variables to be extracted from the historian, the modelling requirement, the input/expected-reference variables and the need for explicit engineering rules.

| Detector ID | Class | Variables to extract | Training / calibration | Inputs / expected reference | Explicit rules or thresholds |
|---|---|---|---|---|---|
| `D1_BLR_INTERLOCK` | D1 | `P1_STSP`, `P1_PP01AD`, `P1_PP01AR`, `P1_PP01BD`, `P1_PP01BR`, `P1_PP02D`, `P1_PP02R`, `P1_PP04D` | No model training. Encode explicit interlock/protection/range rules. | Engineering rule table and thresholds (documented DCS limits, per-valve limits, trip constants). Reference (where applicable): `-` | Yes - rules/thresholds must be transcribed from control documentation and validated by the ICS expert. |
| `D1_P1_VALVE_PERMISSIVE` | D1 | `P1_SOL01D`, `P1_SOL03D`, `P1_PCV02D`, `P1_FCV02D` | No model training. Encode explicit interlock/protection/range rules. | Engineering rule table and thresholds (documented DCS limits, per-valve limits, trip constants). Reference (where applicable): `-` | Yes - rules/thresholds must be transcribed from control documentation and validated by the ICS expert. |
| `D1_P1_HH_TRIP` | D1 | `P1_PIT01`, `P1_PIT01_HH` | No model training. Encode explicit interlock/protection/range rules. | Engineering rule table and thresholds (documented DCS limits, per-valve limits, trip constants). Reference (where applicable): `-` | Yes - rules/thresholds must be transcribed from control documentation and validated by the ICS expert. |
| `D1_P1_VALVE_RANGE` | D1 | `P1_FCV01D`, `P1_FCV02D`, `P1_FCV03D`, `P1_LCV01D`, `P1_PCV01D`, `P1_PCV02D` | No model training. Encode explicit interlock/protection/range rules. | Engineering rule table and thresholds (documented DCS limits, per-valve limits, trip constants). Reference (where applicable): `-` | Yes - rules/thresholds must be transcribed from control documentation and validated by the ICS expert. |
| `D1_P2_TRIP` | D1 | `P2_SIT01`, `P2_RTR`, `P2_VIBTR01`, `P2_VIBTR02`, `P2_VIBTR03`, `P2_VIBTR04`, `P2_VTR01`, `P2_VTR02`, `P2_VTR03`, `P2_VTR04`, `P2_Emerg`, `P2_TripEx` | No model training. Encode explicit interlock/protection/range rules. | Engineering rule table and thresholds (documented DCS limits, per-valve limits, trip constants). Reference (where applicable): `-` | Yes - rules/thresholds must be transcribed from control documentation and validated by the ICS expert. |
| `D1_P2_MODE` | D1 | `P2_OnOff`, `P2_Emerg`, `P2_TripEx`, `P2_ManualGO`, `P2_AutoGO`, `P2_MASW`, `P2_MASW_Lamp`, `P2_ATSW_Lamp` | No model training. Encode explicit interlock/protection/range rules. | Engineering rule table and thresholds (documented DCS limits, per-valve limits, trip constants). Reference (where applicable): `-` | Yes - rules/thresholds must be transcribed from control documentation and validated by the ICS expert. |
| `D1_P3_LEVELSW` | D1 | `P3_LIT01`, `P3_LH01`, `P3_LL01` | No model training. Encode explicit interlock/protection/range rules. | Engineering rule table and thresholds (documented DCS limits, per-valve limits, trip constants). Reference (where applicable): `-` | Yes - rules/thresholds must be transcribed from control documentation and validated by the ICS expert. |
| `D1_SETPOINT_ENVELOPE` | D1 | `x1001_05_SETPOINT_OUT`, `x1001_15_ASSIGN_OUT`, `x1002_07_SETPOINT_OUT`, `x1002_08_SETPOINT_OUT`, `x1003_10_SETPOINT_OUT`, `x1003_18_SETPOINT_OUT`, `P1_PP04SP`, `P2_AutoSD`, `P2_ManualSD`, `P4_HT_PS`, `P4_ST_PS` | No model training. Encode explicit interlock/protection/range rules. | Engineering rule table and thresholds (documented DCS limits, per-valve limits, trip constants). Reference (where applicable): `-` | Yes - rules/thresholds must be transcribed from control documentation and validated by the ICS expert. |
| `D1_P4_DEMAND_RANGE` | D1 | `P4_HT_PS`, `P4_ST_PS`, `P4_LD`, `P4_HT_PO`, `P4_ST_PO` | No model training. Encode explicit interlock/protection/range rules. | Engineering rule table and thresholds (documented DCS limits, per-valve limits, trip constants). Reference (where applicable): `-` | Yes - rules/thresholds must be transcribed from control documentation and validated by the ICS expert. |
| `D2_P1_VALVE_POS` | D2 | `P1_FCV01Z`, `P1_FCV02Z`, `P1_FCV03Z`, `P1_LCV01Z`, `P1_PCV01Z` | Statistical calibration (mean/variance/robust limits, drift trend) from normal-operation history. | Historian extraction of the listed tags over the complete normal-operation periods (hai-train1..4). Reference (where applicable): `-` | No explicit rules; alarm thresholds derived from calibrated quantiles. |
| `D2_P1_SENSOR_NOISE` | D2 | `P1_PIT01`, `P1_LIT01`, `P1_TIT01`, `P1_TIT02`, `P1_FT01Z`, `P1_FT02Z`, `P1_FT03Z` | Statistical calibration (mean/variance/robust limits, drift trend) from normal-operation history. | Historian extraction of the listed tags over the complete normal-operation periods (hai-train1..4). Reference (where applicable): `-` | No explicit rules; alarm thresholds derived from calibrated quantiles. |
| `D2_P1_AUX_PRESSURE` | D2 | `P1_PIT02`, `P1_PP04` | Statistical calibration (mean/variance/robust limits, drift trend) from normal-operation history. | Historian extraction of the listed tags over the complete normal-operation periods (hai-train1..4). Reference (where applicable): `-` | No explicit rules; alarm thresholds derived from calibrated quantiles. |
| `D2_P1_COOL_TEMP` | D2 | `P1_TIT03` | Statistical calibration (mean/variance/robust limits, drift trend) from normal-operation history. | Historian extraction of the listed tags over the complete normal-operation periods (hai-train1..4). Reference (where applicable): `-` | No explicit rules; alarm thresholds derived from calibrated quantiles. |
| `D2_P2_ELECTRICAL` | D2 | `P2_24Vdc`, `P2_SCO` | Statistical calibration (mean/variance/robust limits, drift trend) from normal-operation history. | Historian extraction of the listed tags over the complete normal-operation periods (hai-train1..4). Reference (where applicable): `-` | No explicit rules; alarm thresholds derived from calibrated quantiles. |
| `D2_P2_VIB_DYN` | D2 | `P2_VIBTR01`, `P2_VIBTR02`, `P2_VIBTR03`, `P2_VIBTR04` | Statistical calibration (mean/variance/robust limits, drift trend) from normal-operation history. | Historian extraction of the listed tags over the complete normal-operation periods (hai-train1..4). Reference (where applicable): `-` | No explicit rules; alarm thresholds derived from calibrated quantiles. |
| `D2_P2_PHASE` | D2 | `P2_VT01`, `P2_SCST` | Statistical calibration (mean/variance/robust limits, drift trend) from normal-operation history. | Historian extraction of the listed tags over the complete normal-operation periods (hai-train1..4). Reference (where applicable): `-` | No explicit rules; alarm thresholds derived from calibrated quantiles. |
| `D2_P3_INFLOW` | D2 | `P3_FIT01`, `P3_PIT01` | Statistical calibration (mean/variance/robust limits, drift trend) from normal-operation history. | Historian extraction of the listed tags over the complete normal-operation periods (hai-train1..4). Reference (where applicable): `-` | No explicit rules; alarm thresholds derived from calibrated quantiles. |
| `D2_P4_FREQ` | D2 | `P4_ST_FD`, `P4_HT_FD` | Statistical calibration (mean/variance/robust limits, drift trend) from normal-operation history. | Historian extraction of the listed tags over the complete normal-operation periods (hai-train1..4). Reference (where applicable): `-` | No explicit rules; alarm thresholds derived from calibrated quantiles. |
| `D2_P4_LOAD` | D2 | `P4_ST_PO`, `P4_HT_PO`, `P4_ST_GOV` | Statistical calibration (mean/variance/robust limits, drift trend) from normal-operation history. | Historian extraction of the listed tags over the complete normal-operation periods (hai-train1..4). Reference (where applicable): `-` | No explicit rules; alarm thresholds derived from calibrated quantiles. |
| `D2_P4_STEAM` | D2 | `P4_ST_PT01`, `P4_ST_TT01` | Statistical calibration (mean/variance/robust limits, drift trend) from normal-operation history. | Historian extraction of the listed tags over the complete normal-operation periods (hai-train1..4). Reference (where applicable): `-` | No explicit rules; alarm thresholds derived from calibrated quantiles. |
| `D3_P1_PC_SPLIT` | D3 | `P1_PCV01D`, `P1_PCV01Z`, `P1_PCV02D`, `P1_PCV02Z` | Train a configuration model that learns the joint normal region of the listed variables. | Historian extraction of the listed tags over all normal-operation periods, including mode changes. Reference (where applicable): `-` | No; only the accepted joint configuration region must be reviewed. |
| `D3_P1_TC_SPLIT` | D3 | `P1_FCV01D`, `P1_FCV01Z`, `P1_FCV02D`, `P1_FCV02Z` | Train a configuration model that learns the joint normal region of the listed variables. | Historian extraction of the listed tags over all normal-operation periods, including mode changes. Reference (where applicable): `-` | No; only the accepted joint configuration region must be reviewed. |
| `D3_P2_SP_MODE` | D3 | `P2_AutoSD`, `P2_ManualSD`, `P2_MASW`, `P2_MASW_Lamp`, `P2_AutoGO`, `P2_ManualGO` | Train a configuration model that learns the joint normal region of the listed variables. | Historian extraction of the listed tags over all normal-operation periods, including mode changes. Reference (where applicable): `-` | No; only the accepted joint configuration region must be reviewed. |
| `D3_P3_DISPATCH` | D3 | `P3_LCP01D`, `P3_LCV01D` | Train a configuration model that learns the joint normal region of the listed variables. | Historian extraction of the listed tags over all normal-operation periods, including mode changes. Reference (where applicable): `-` | No; only the accepted joint configuration region must be reviewed. |
| `D3_P4_LOAD_ALLOC` | D3 | `P4_LD`, `P4_HT_PS`, `P4_ST_PS`, `P4_HT_PO`, `P4_ST_PO` | Train a configuration model that learns the joint normal region of the listed variables. | Historian extraction of the listed tags over all normal-operation periods, including mode changes. Reference (where applicable): `-` | No; only the accepted joint configuration region must be reviewed. |
| `D3_P1_SP_GROUP` | D3 | `x1002_07_SETPOINT_OUT`, `x1002_08_SETPOINT_OUT`, `x1003_10_SETPOINT_OUT`, `P1_PP04SP` | Train a configuration model that learns the joint normal region of the listed variables. | Historian extraction of the listed tags over all normal-operation periods, including mode changes. Reference (where applicable): `-` | No; only the accepted joint configuration region must be reviewed. |
| `D4_P1_SP_SEQUENCE` | D4 | `x1001_05_SETPOINT_OUT`, `x1001_15_ASSIGN_OUT`, `x1002_07_SETPOINT_OUT`, `x1002_08_SETPOINT_OUT`, `x1003_10_SETPOINT_OUT`, `x1003_18_SETPOINT_OUT`, `P1_PP04SP`, `P2_AutoSD`, `P2_ManualSD`, `P4_HT_PS`, `P4_ST_PS` | Train a temporal model of sequence/ramp/inertia from normal-operation windows. | Historian extraction of the listed tags, resampled to the 1 s native period, with transition windows retained. Reference (where applicable): `-` | Possibly - minimum/maximum ramp rates and dwell times to be reviewed. |
| `D4_P1_FCV_PROFILE` | D4 | `P1_FCV01D`, `P1_FCV02D`, `P1_FCV03D`, `P1_LCV01D`, `P1_PCV01D`, `P1_PCV02D` | Train a temporal model of sequence/ramp/inertia from normal-operation windows. | Historian extraction of the listed tags, resampled to the 1 s native period, with transition windows retained. Reference (where applicable): `-` | Possibly - minimum/maximum ramp rates and dwell times to be reviewed. |
| `D4_P1_LIT_INERTIA` | D4 | `P1_LIT01`, `P1_FCV03D`, `P1_LCV01D`, `P1_FT03Z`, `P1_FT01Z` | Train a temporal model of sequence/ramp/inertia from normal-operation windows. | Historian extraction of the listed tags, resampled to the 1 s native period, with transition windows retained. Reference (where applicable): `-` | Possibly - minimum/maximum ramp rates and dwell times to be reviewed. |
| `D4_P1_THERMAL` | D4 | `P1_TIT01`, `P1_TIT02`, `P1_TIT03`, `P1_FCV01D`, `P1_FCV02D`, `P1_PP04` | Train a temporal model of sequence/ramp/inertia from normal-operation windows. | Historian extraction of the listed tags, resampled to the 1 s native period, with transition windows retained. Reference (where applicable): `-` | Possibly - minimum/maximum ramp rates and dwell times to be reviewed. |
| `D4_P2_SPEED_RAMP` | D4 | `P2_AutoSD`, `P2_ManualSD`, `P2_SIT01`, `P2_SCO` | Train a temporal model of sequence/ramp/inertia from normal-operation windows. | Historian extraction of the listed tags, resampled to the 1 s native period, with transition windows retained. Reference (where applicable): `-` | Possibly - minimum/maximum ramp rates and dwell times to be reviewed. |
| `D4_P2_VIB_DYNAMICS` | D4 | `P2_VIBTR01`, `P2_VIBTR02`, `P2_VIBTR03`, `P2_VIBTR04`, `P2_VT01` | Train a temporal model of sequence/ramp/inertia from normal-operation windows. | Historian extraction of the listed tags, resampled to the 1 s native period, with transition windows retained. Reference (where applicable): `-` | Possibly - minimum/maximum ramp rates and dwell times to be reviewed. |
| `D4_P3_LEVEL_DYN` | D4 | `P3_LIT01`, `P3_LCP01D`, `P3_LCV01D`, `P3_FIT01` | Train a temporal model of sequence/ramp/inertia from normal-operation windows. | Historian extraction of the listed tags, resampled to the 1 s native period, with transition windows retained. Reference (where applicable): `-` | Possibly - minimum/maximum ramp rates and dwell times to be reviewed. |
| `D4_P4_DYNAMICS` | D4 | `P4_ST_GOV`, `P4_ST_LD`, `P4_ST_PO`, `P4_HT_PO`, `P4_LD` | Train a temporal model of sequence/ramp/inertia from normal-operation windows. | Historian extraction of the listed tags, resampled to the 1 s native period, with transition windows retained. Reference (where applicable): `-` | Possibly - minimum/maximum ramp rates and dwell times to be reviewed. |
| `D5_P1_FCV01_TRACK` | D5 | `P1_FCV01D`, `P1_FCV01Z` | Learn the expected relationship/residual model between the listed variables. | Historian extraction of the listed tags over normal operation; residual statistics computed on normal data. Reference (where applicable): `P1_FCV01D` | No; residual tolerance derived from normal data (engineering sanity check recommended). |
| `D5_P1_FCV02_TRACK` | D5 | `P1_FCV02D`, `P1_FCV02Z` | Learn the expected relationship/residual model between the listed variables. | Historian extraction of the listed tags over normal operation; residual statistics computed on normal data. Reference (where applicable): `P1_FCV02D` | No; residual tolerance derived from normal data (engineering sanity check recommended). |
| `D5_P1_FCV03_TRACK` | D5 | `P1_FCV03D`, `P1_FCV03Z` | Learn the expected relationship/residual model between the listed variables. | Historian extraction of the listed tags over normal operation; residual statistics computed on normal data. Reference (where applicable): `P1_FCV03D` | No; residual tolerance derived from normal data (engineering sanity check recommended). |
| `D5_P1_LCV01_TRACK` | D5 | `P1_LCV01D`, `P1_LCV01Z` | Learn the expected relationship/residual model between the listed variables. | Historian extraction of the listed tags over normal operation; residual statistics computed on normal data. Reference (where applicable): `P1_LCV01D` | No; residual tolerance derived from normal data (engineering sanity check recommended). |
| `D5_P1_PCV01_TRACK` | D5 | `P1_PCV01D`, `P1_PCV01Z` | Learn the expected relationship/residual model between the listed variables. | Historian extraction of the listed tags over normal operation; residual statistics computed on normal data. Reference (where applicable): `P1_PCV01D` | No; residual tolerance derived from normal data (engineering sanity check recommended). |
| `D5_P1_PCV02_TRACK` | D5 | `P1_PCV02D`, `P1_PCV02Z` | Learn the expected relationship/residual model between the listed variables. | Historian extraction of the listed tags over normal operation; residual statistics computed on normal data. Reference (where applicable): `P1_PCV02D` | No; residual tolerance derived from normal data (engineering sanity check recommended). |
| `D5_P1_FC03_FLOW` | D5 | `x1002_08_SETPOINT_OUT`, `P1_FT03Z`, `P1_FT03`, `P1_FCV03Z` | Learn the expected relationship/residual model between the listed variables. | Historian extraction of the listed tags over normal operation; residual statistics computed on normal data. Reference (where applicable): `x1002_08_SETPOINT_OUT` | No; residual tolerance derived from normal data (engineering sanity check recommended). |
| `D5_P1_FC02_FLOW` | D5 | `x1003_10_SETPOINT_OUT`, `P1_FT02Z`, `P1_FT02`, `P1_FCV01Z` | Learn the expected relationship/residual model between the listed variables. | Historian extraction of the listed tags over normal operation; residual statistics computed on normal data. Reference (where applicable): `x1003_10_SETPOINT_OUT` | No; residual tolerance derived from normal data (engineering sanity check recommended). |
| `D5_P1_LC_LEVEL` | D5 | `x1002_07_SETPOINT_OUT`, `P1_LIT01`, `P1_LCV01Z`, `P1_FT03Z` | Learn the expected relationship/residual model between the listed variables. | Historian extraction of the listed tags over normal operation; residual statistics computed on normal data. Reference (where applicable): `x1002_07_SETPOINT_OUT` | No; residual tolerance derived from normal data (engineering sanity check recommended). |
| `D5_P1_TC_TEMP` | D5 | `x1003_18_SETPOINT_OUT`, `P1_TIT01`, `P1_FCV01D`, `P1_FCV02D`, `P1_FT02Z` | Learn the expected relationship/residual model between the listed variables. | Historian extraction of the listed tags over normal operation; residual statistics computed on normal data. Reference (where applicable): `x1003_18_SETPOINT_OUT` | No; residual tolerance derived from normal data (engineering sanity check recommended). |
| `D5_P1_PC_PRESS` | D5 | `x1001_15_ASSIGN_OUT`, `x1001_05_SETPOINT_OUT`, `P1_PIT01`, `P1_PCV01Z`, `P1_PCV02Z` | Learn the expected relationship/residual model between the listed variables. | Historian extraction of the listed tags over normal operation; residual statistics computed on normal data. Reference (where applicable): `x1001_15_ASSIGN_OUT` | No; residual tolerance derived from normal data (engineering sanity check recommended). |
| `D5_P1_CC_COOLING` | D5 | `P1_PP04`, `P1_PP04SP`, `P1_PP04D`, `P1_TIT03` | Learn the expected relationship/residual model between the listed variables. | Historian extraction of the listed tags over normal operation; residual statistics computed on normal data. Reference (where applicable): `P1_PP04` | No; residual tolerance derived from normal data (engineering sanity check recommended). |
| `D5_P1_MASS_BALANCE` | D5 | `P1_FT01Z`, `P1_FT03Z`, `P1_LIT01`, `P1_FT02Z` | Learn the expected relationship/residual model between the listed variables. | Historian extraction of the listed tags over normal operation; residual statistics computed on normal data. Reference (where applicable): `P1_FT01Z` | No; residual tolerance derived from normal data (engineering sanity check recommended). |
| `D5_P2_SC` | D5 | `P2_SIT01`, `P2_AutoSD`, `P2_ManualSD`, `P2_SCO`, `P2_SCST` | Learn the expected relationship/residual model between the listed variables. | Historian extraction of the listed tags over normal operation; residual statistics computed on normal data. Reference (where applicable): `P2_SIT01` | No; residual tolerance derived from normal data (engineering sanity check recommended). |
| `D5_P3_LEVEL` | D5 | `P3_LIT01`, `P3_LCV01D`, `P3_LCP01D`, `P3_FIT01`, `P3_PIT01` | Learn the expected relationship/residual model between the listed variables. | Historian extraction of the listed tags over normal operation; residual statistics computed on normal data. Reference (where applicable): `P3_LIT01` | No; residual tolerance derived from normal data (engineering sanity check recommended). |
| `D5_P3_PUMP` | D5 | `P3_LCP01D`, `P3_PIT01`, `P3_FIT01` | Learn the expected relationship/residual model between the listed variables. | Historian extraction of the listed tags over normal operation; residual statistics computed on normal data. Reference (where applicable): `P3_LCP01D` | No; residual tolerance derived from normal data (engineering sanity check recommended). |
| `D5_P4_ST_POWER` | D5 | `P4_ST_LD`, `P4_ST_PO`, `P4_ST_GOV` | Learn the expected relationship/residual model between the listed variables. | Historian extraction of the listed tags over normal operation; residual statistics computed on normal data. Reference (where applicable): `P4_ST_LD` | No; residual tolerance derived from normal data (engineering sanity check recommended). |
| `D5_P4_HT_POWER` | D5 | `P4_HT_PS`, `P4_HT_PO` | Learn the expected relationship/residual model between the listed variables. | Historian extraction of the listed tags over normal operation; residual statistics computed on normal data. Reference (where applicable): `P4_HT_PS` | No; residual tolerance derived from normal data (engineering sanity check recommended). |
| `D5_P4_LOAD_BAL` | D5 | `P4_LD`, `P4_ST_PO`, `P4_HT_PO`, `P4_ST_LD`, `P4_HT_PS` | Learn the expected relationship/residual model between the listed variables. | Historian extraction of the listed tags over normal operation; residual statistics computed on normal data. Reference (where applicable): `P4_LD` | No; residual tolerance derived from normal data (engineering sanity check recommended). |
| `D5_P4_FREQ_COUPLE` | D5 | `P4_ST_FD`, `P4_HT_FD`, `P2_SCST`, `P2_SIT01` | Learn the expected relationship/residual model between the listed variables. | Historian extraction of the listed tags over normal operation; residual statistics computed on normal data. Reference (where applicable): `P4_ST_FD` | No; residual tolerance derived from normal data (engineering sanity check recommended). |
| `D5_P4_STEAM` | D5 | `P4_ST_PT01`, `P4_ST_TT01`, `P4_ST_GOV`, `P4_ST_PO` | Learn the expected relationship/residual model between the listed variables. | Historian extraction of the listed tags over normal operation; residual statistics computed on normal data. Reference (where applicable): `P4_ST_PT01` | No; residual tolerance derived from normal data (engineering sanity check recommended). |
| `D5_HEX_COUPLE` | D5 | `P1_TIT01`, `P1_PIT01`, `P4_ST_TT01`, `P4_ST_PT01` | Learn the expected relationship/residual model between the listed variables. | Historian extraction of the listed tags over normal operation; residual statistics computed on normal data. Reference (where applicable): `P1_TIT01` | No; residual tolerance derived from normal data (engineering sanity check recommended). |
| `D5_PC_PV_FLOW` | D5 | `P1_PIT01`, `P1_PIT02`, `P1_FT01Z`, `P1_FT02Z` | Learn the expected relationship/residual model between the listed variables. | Historian extraction of the listed tags over normal operation; residual statistics computed on normal data. Reference (where applicable): `P1_PIT01` | No; residual tolerance derived from normal data (engineering sanity check recommended). |

**Global configuration notes**

- D1 instances require **no data**: they encode interlocks, protection limits and engineering ranges from DCS documentation.
- D2 instances require **statistical calibration** on the normal-operation history (robust mean/σ or quantiles, drift slope, step limits).
- D3/D4/D5 instances require **normal-operation training**, and D5 additionally requires learning an expected relationship (residual model) between a reference variable and its dependants.
- All normal-operation extraction should use `hai-train1..4.csv`; the labelled `hai-test*` files must **not** be used for calibration.
- Native 1 s sampling is sufficient for all detectors; no down-sampling is required, but transition windows must be preserved for D4.

---

## E. Unresolved configuration issues

1. The seven `x100*_*_OUT` tags are not described in the HAI 23.05 data-point table. Their roles were inferred from correlation with documented variables (e.g. x1002_08 <-> P1_FT03Z, x1003_10 <-> P1_FT02Z) and from the HAIEnd control-logic blocks 1001/1002/1003; the exact block-to-tag mapping in dcs_1001h.json/dcs_1002h.json/dcs_1003h.json must be confirmed.
2. Operator setpoints documented for HAI (P1_B2016, P1_B3004, P1_B3005, P1_B4002, P1_B400B) are absent from the 23.05 CSV. It is assumed they are represented by the x1001_15/x1002_07/x1002_08/x1003_10/x1003_18 internal points; this assumption requires expert validation.
3. P1_PIT01_HH, P1_SOL01D and P1_SOL03D are constant 524320 in the training data although the documentation declares 0-10 bar / Boolean ranges. This is presumably a signal-quality/placeholder code; the true semantics must be confirmed before rule thresholds are set.
4. P1_PP01AD/P1_PP01AR/P1_PP01BD/P1_PP01BR/P1_PP02D/P1_PP02R, P1_STSP, P2_Emerg, P2_OnOff, P2_RTR, P2_TripEx, P2_VTR01-04, P3_LH01, P3_LL01 are constant during normal operation. D1 rules for them cannot be calibrated on these data and must come from controller documentation (constant tags give no transition evidence).
5. Two conflicting normal ranges for the turbine speed setpoints appear in the documentation (AutoSD [100,120] RPM in the HMM figure vs [11,12] for ManualSD); the observed AutoSD range is ~100.7-129.4 and ManualSD ~0-12.9, so the documented ManualSD range appears inconsistent and must be resolved.
6. P1_PP04D (cooling-pump run command) is not listed in the HAI data-point table; its role was inferred from the HAIEnd graph (DM-PP04-D) and its 37.5% duty cycle.
7. P4_HT_LD (electrical load demand of HTM) is referenced in the documentation but is not present in the 23.05 CSV; the HTM load-balance detector therefore uses P4_HT_PS / P4_HT_PO only.
8. Several units are undocumented or dimensionless ('-'): P3_FIT01, P3_LCP01D, P3_LCV01D, P3_PIT01, P4_ST_GOV, P4_ST_PT01, P4_ST_TT01. Range/limit rules for these signals require unit clarification.
9. label-test2.csv timestamps are truncated to the minute ('2022-08-17 0:00') and do not align with the second-resolution timestamps of hai-test2.csv; label alignment must be repaired before any later evaluation (not used at this configuration stage).
10. P2_SCST is documented in RPM as 'speed change proportional to frequency change of the STM' and takes near-constant values (~720) for long periods with occasional small steps; its dynamic role in the speed loop needs clarification.
11. The physical boiler graph (phy_boiler.json) does not expose numeric tag names for most devices (only DM-* labels), so several cross-subsystem relations (e.g. HEX01S/TK02 coupling) are taken from the process control description rather than from tag-level wiring.
12. The HMM normal-operation model uses only seven setpoints and a subset of controllers; the coverage of P4 HIL setpoints (P4_ST_PS, P4_HT_PS) by the HMM in the 23.05 release is not fully documented.
13. Detector thresholds for the D1 protection group (P1_PIT01_HH, P2_RTR, P2_VTR*) must be read from the DCS project files; the CSV only contains the constant runtime values.

**Assumptions requiring validation by an ICS expert**

- The `x100*` points are the internal setpoint/control outputs of the corresponding boiler loops (pressure, level, flow, temperature).
- x1001_15_ASSIGN_OUT is the assigned setpoint of the pressure controller (the CSV counterpart of documented `P1_B2016`).
- FCV02 and PCV02 have a minimum opening of 15% during normal operation (documented valve minimum, visible in the observed range).
- The four training files together constitute the normal-operation baseline, including operator setpoint changes and manual/auto mode changes.

---

## F. Machine-readable configuration

The complete routing configuration is also written to `process_oriented_ics_anomaly_detection_config.json`.

```json
{
  "dataset": {
    "name": "HAI 23.05",
    "normal_files": [
      "hai-train1.csv",
      "hai-train2.csv",
      "hai-train3.csv",
      "hai-train4.csv"
    ],
    "test_files": [
      "hai-test1.csv",
      "hai-test2.csv"
    ],
    "n_variables": 86,
    "sampling_period_s": 1,
    "note": "Normal-operation characterization used the four training files only; no anomaly detection was performed at this stage."
  },
  "detectors": [
    {
      "detector_id": "D1_BLR_INTERLOCK",
      "detector_class": "D1",
      "purpose": "Verify boiler start/stop and pump interlock logic (commands, running feedback and boiler run state are mutually legal) and forbid inconsistent transitions.",
      "inputs": [
        "P1_STSP",
        "P1_PP01AD",
        "P1_PP01AR",
        "P1_PP01BD",
        "P1_PP01BR",
        "P1_PP02D",
        "P1_PP02R",
        "P1_PP04D"
      ],
      "monitored_invariant": "explicit logical interlock; forbidden state/transition combinations",
      "training_requirement": "none",
      "confidence": "high"
    },
    {
      "detector_id": "D1_P1_VALVE_PERMISSIVE",
      "detector_class": "D1",
      "purpose": "Enforce valve permissives and minimum-opening rule (supply/drain exclusivity, PCV02/FCV02 recirculation minimum) on the boiler water circuit.",
      "inputs": [
        "P1_SOL01D",
        "P1_SOL03D",
        "P1_PCV02D",
        "P1_FCV02D"
      ],
      "monitored_invariant": "explicit valve permissive and minimum-flow constraint",
      "training_requirement": "none",
      "confidence": "high"
    },
    {
      "detector_id": "D1_P1_HH_TRIP",
      "detector_class": "D1",
      "purpose": "Check the high-high pressure protection rule for the heat exchanger.",
      "inputs": [
        "P1_PIT01",
        "P1_PIT01_HH"
      ],
      "monitored_invariant": "explicit protection threshold (PIT01 must stay below HH)",
      "training_requirement": "none",
      "confidence": "high"
    },
    {
      "detector_id": "D1_P1_VALVE_RANGE",
      "detector_class": "D1",
      "purpose": "Validate engineering ranges and per-valve limits of all P1 actuator commands.",
      "inputs": [
        "P1_FCV01D",
        "P1_FCV02D",
        "P1_FCV03D",
        "P1_LCV01D",
        "P1_PCV01D",
        "P1_PCV02D"
      ],
      "monitored_invariant": "explicit engineering range [0,100]% and per-valve limit",
      "training_requirement": "none",
      "confidence": "high"
    },
    {
      "detector_id": "D1_P2_TRIP",
      "detector_class": "D1",
      "purpose": "Evaluate the turbine over-speed and over-vibration trip logic (Emerg only when SIT01>RTR or |VIBTR[n]|>VTR[n]).",
      "inputs": [
        "P2_SIT01",
        "P2_RTR",
        "P2_VIBTR01",
        "P2_VIBTR02",
        "P2_VIBTR03",
        "P2_VIBTR04",
        "P2_VTR01",
        "P2_VTR02",
        "P2_VTR03",
        "P2_VTR04",
        "P2_Emerg",
        "P2_TripEx"
      ],
      "monitored_invariant": "explicit protection rule; forbidden trip states",
      "training_requirement": "none",
      "confidence": "high"
    },
    {
      "detector_id": "D1_P2_MODE",
      "detector_class": "D1",
      "purpose": "Verify turbine operator-mode, button and lamp state consistency (auto/manual selection, on/off, emergency, trip exit).",
      "inputs": [
        "P2_OnOff",
        "P2_Emerg",
        "P2_TripEx",
        "P2_ManualGO",
        "P2_AutoGO",
        "P2_MASW",
        "P2_MASW_Lamp",
        "P2_ATSW_Lamp"
      ],
      "monitored_invariant": "explicit state-machine and HMI feedback rules",
      "training_requirement": "none",
      "confidence": "high"
    },
    {
      "detector_id": "D1_P3_LEVELSW",
      "detector_class": "D1",
      "purpose": "Check reservoir high/low level protection thresholds.",
      "inputs": [
        "P3_LIT01",
        "P3_LH01",
        "P3_LL01"
      ],
      "monitored_invariant": "explicit protection thresholds",
      "training_requirement": "none",
      "confidence": "high"
    },
    {
      "detector_id": "D1_SETPOINT_ENVELOPE",
      "detector_class": "D1",
      "purpose": "Validate that every setpoint stays inside its experimentally validated normal range.",
      "inputs": [
        "x1001_05_SETPOINT_OUT",
        "x1001_15_ASSIGN_OUT",
        "x1002_07_SETPOINT_OUT",
        "x1002_08_SETPOINT_OUT",
        "x1003_10_SETPOINT_OUT",
        "x1003_18_SETPOINT_OUT",
        "P1_PP04SP",
        "P2_AutoSD",
        "P2_ManualSD",
        "P4_HT_PS",
        "P4_ST_PS"
      ],
      "monitored_invariant": "explicit normal operating envelope of setpoints",
      "training_requirement": "none",
      "confidence": "high"
    },
    {
      "detector_id": "D1_P4_DEMAND_RANGE",
      "detector_class": "D1",
      "purpose": "Validate HIL demand signals against the normal generation envelope.",
      "inputs": [
        "P4_HT_PS",
        "P4_ST_PS",
        "P4_LD",
        "P4_HT_PO",
        "P4_ST_PO"
      ],
      "monitored_invariant": "explicit operating envelope of demand/output powers",
      "training_requirement": "none",
      "confidence": "high"
    },
    {
      "detector_id": "D2_P1_VALVE_POS",
      "detector_class": "D2",
      "purpose": "Monitor statistical stability, noise level and slow drift of boiler valve position feedbacks.",
      "inputs": [
        "P1_FCV01Z",
        "P1_FCV02Z",
        "P1_FCV03Z",
        "P1_LCV01Z",
        "P1_PCV01Z"
      ],
      "monitored_invariant": "stationary distribution, bounded noise, no slow drift",
      "training_requirement": "calibration",
      "confidence": "medium"
    },
    {
      "detector_id": "D2_P1_SENSOR_NOISE",
      "detector_class": "D2",
      "purpose": "Characterize stability/variability and detect drift or abrupt change on boiler process variables.",
      "inputs": [
        "P1_PIT01",
        "P1_LIT01",
        "P1_TIT01",
        "P1_TIT02",
        "P1_FT01Z",
        "P1_FT02Z",
        "P1_FT03Z"
      ],
      "monitored_invariant": "statistical stationarity and drift-free normal behaviour",
      "training_requirement": "calibration",
      "confidence": "medium"
    },
    {
      "detector_id": "D2_P1_AUX_PRESSURE",
      "detector_class": "D2",
      "purpose": "Monitor the auxiliary pressure and cooling-pump output operating band.",
      "inputs": [
        "P1_PIT02",
        "P1_PP04"
      ],
      "monitored_invariant": "stationary band of auxiliary pressure/cooling output",
      "training_requirement": "calibration",
      "confidence": "medium"
    },
    {
      "detector_id": "D2_P1_COOL_TEMP",
      "detector_class": "D2",
      "purpose": "Monitor main-tank cooling temperature stability and drift.",
      "inputs": [
        "P1_TIT03"
      ],
      "monitored_invariant": "stationary thermal band",
      "training_requirement": "calibration",
      "confidence": "medium"
    },
    {
      "detector_id": "D2_P2_ELECTRICAL",
      "detector_class": "D2",
      "purpose": "Monitor turbine DCS supply voltage and speed-controller output statistics.",
      "inputs": [
        "P2_24Vdc",
        "P2_SCO"
      ],
      "monitored_invariant": "tight stationary band / bounded variance",
      "training_requirement": "calibration",
      "confidence": "medium"
    },
    {
      "detector_id": "D2_P2_VIB_DYN",
      "detector_class": "D2",
      "purpose": "Characterize vibration amplitude/envelope statistics of the four shaft probes.",
      "inputs": [
        "P2_VIBTR01",
        "P2_VIBTR02",
        "P2_VIBTR03",
        "P2_VIBTR04"
      ],
      "monitored_invariant": "zero-mean oscillation, stable RMS/envelope",
      "training_requirement": "calibration",
      "confidence": "medium"
    },
    {
      "detector_id": "D2_P2_PHASE",
      "detector_class": "D2",
      "purpose": "Monitor the key-phasor phase-lag stationarity and coupling to rotor speed.",
      "inputs": [
        "P2_VT01",
        "P2_SCST"
      ],
      "monitored_invariant": "stationary phase-lag band",
      "training_requirement": "calibration",
      "confidence": "medium"
    },
    {
      "detector_id": "D2_P3_INFLOW",
      "detector_class": "D2",
      "purpose": "Monitor inflow flow-rate and pressure stationarity in the water-treatment process.",
      "inputs": [
        "P3_FIT01",
        "P3_PIT01"
      ],
      "monitored_invariant": "statistical stationarity / bounded variance",
      "training_requirement": "calibration",
      "confidence": "medium"
    },
    {
      "detector_id": "D2_P4_FREQ",
      "detector_class": "D2",
      "purpose": "Characterize grid-frequency deviation statistics for STM and HTM.",
      "inputs": [
        "P4_ST_FD",
        "P4_HT_FD"
      ],
      "monitored_invariant": "zero-mean stationary deviation with stable spectrum",
      "training_requirement": "calibration",
      "confidence": "medium"
    },
    {
      "detector_id": "D2_P4_LOAD",
      "detector_class": "D2",
      "purpose": "Monitor stationarity of HIL output power and governor signals.",
      "inputs": [
        "P4_ST_PO",
        "P4_HT_PO",
        "P4_ST_GOV"
      ],
      "monitored_invariant": "stationary residual around scheduled demand",
      "training_requirement": "calibration",
      "confidence": "medium"
    },
    {
      "detector_id": "D2_P4_STEAM",
      "detector_class": "D2",
      "purpose": "Monitor steam pressure/temperature statistical stability.",
      "inputs": [
        "P4_ST_PT01",
        "P4_ST_TT01"
      ],
      "monitored_invariant": "stationary steam state within a narrow band",
      "training_requirement": "calibration",
      "confidence": "medium"
    },
    {
      "detector_id": "D3_P1_PC_SPLIT",
      "detector_class": "D3",
      "purpose": "Detect abnormal simultaneous configuration of the two pressure-control valves (transfer PCV01 vs recirculation PCV02) even when each position is individually valid.",
      "inputs": [
        "P1_PCV01D",
        "P1_PCV01Z",
        "P1_PCV02D",
        "P1_PCV02Z"
      ],
      "monitored_invariant": "multivariate valve-split configuration",
      "training_requirement": "normal-data-training",
      "confidence": "medium"
    },
    {
      "detector_id": "D3_P1_TC_SPLIT",
      "detector_class": "D3",
      "purpose": "Detect abnormal simultaneous configuration of the heat-exchanger branch valves FCV01/FCV02.",
      "inputs": [
        "P1_FCV01D",
        "P1_FCV01Z",
        "P1_FCV02D",
        "P1_FCV02Z"
      ],
      "monitored_invariant": "multivariate branch-split configuration",
      "training_requirement": "normal-data-training",
      "confidence": "medium"
    },
    {
      "detector_id": "D3_P2_SP_MODE",
      "detector_class": "D3",
      "purpose": "Detect an invalid combination of active speed setpoint and manual/auto mode selection.",
      "inputs": [
        "P2_AutoSD",
        "P2_ManualSD",
        "P2_MASW",
        "P2_MASW_Lamp",
        "P2_AutoGO",
        "P2_ManualGO"
      ],
      "monitored_invariant": "mode/setpoint configuration consistency",
      "training_requirement": "normal-data-training",
      "confidence": "medium"
    },
    {
      "detector_id": "D3_P3_DISPATCH",
      "detector_class": "D3",
      "purpose": "Detect abnormal simultaneous pumping/discharge demand combination of the level loop.",
      "inputs": [
        "P3_LCP01D",
        "P3_LCV01D"
      ],
      "monitored_invariant": "demand-allocation configuration",
      "training_requirement": "normal-data-training",
      "confidence": "medium"
    },
    {
      "detector_id": "D3_P4_LOAD_ALLOC",
      "detector_class": "D3",
      "purpose": "Detect abnormal combination of total load and per-unit scheduled demands that is individually in range but violates load allocation.",
      "inputs": [
        "P4_LD",
        "P4_HT_PS",
        "P4_ST_PS",
        "P4_HT_PO",
        "P4_ST_PO"
      ],
      "monitored_invariant": "load-allocation configuration",
      "training_requirement": "normal-data-training",
      "confidence": "medium"
    },
    {
      "detector_id": "D3_P1_SP_GROUP",
      "detector_class": "D3",
      "purpose": "Detect abnormal simultaneous setpoint combinations across boiler loops.",
      "inputs": [
        "x1002_07_SETPOINT_OUT",
        "x1002_08_SETPOINT_OUT",
        "x1003_10_SETPOINT_OUT",
        "P1_PP04SP"
      ],
      "monitored_invariant": "coupled setpoint configuration",
      "training_requirement": "normal-data-training",
      "confidence": "medium"
    },
    {
      "detector_id": "D4_P1_SP_SEQUENCE",
      "detector_class": "D4",
      "purpose": "Model the temporal sequence, dwell time and transition shape of operator/HIL setpoint changes (HMM-scheduled normal operation).",
      "inputs": [
        "x1001_05_SETPOINT_OUT",
        "x1001_15_ASSIGN_OUT",
        "x1002_07_SETPOINT_OUT",
        "x1002_08_SETPOINT_OUT",
        "x1003_10_SETPOINT_OUT",
        "x1003_18_SETPOINT_OUT",
        "P1_PP04SP",
        "P2_AutoSD",
        "P2_ManualSD",
        "P4_HT_PS",
        "P4_ST_PS"
      ],
      "monitored_invariant": "setpoint sequence / dwell / trapezoidal-ramp structure",
      "training_requirement": "normal-data-training",
      "confidence": "medium"
    },
    {
      "detector_id": "D4_P1_FCV_PROFILE",
      "detector_class": "D4",
      "purpose": "Model rate-limited valve-command trajectories and actuator inertia for all P1 control valves.",
      "inputs": [
        "P1_FCV01D",
        "P1_FCV02D",
        "P1_FCV03D",
        "P1_LCV01D",
        "P1_PCV01D",
        "P1_PCV02D"
      ],
      "monitored_invariant": "temporal evolution: saturation rate limits, no abrupt steps",
      "training_requirement": "normal-data-training",
      "confidence": "medium"
    },
    {
      "detector_id": "D4_P1_LIT_INERTIA",
      "detector_class": "D4",
      "purpose": "Model return-tank level dynamics driven by in/outflow (feed-forward structure).",
      "inputs": [
        "P1_LIT01",
        "P1_FCV03D",
        "P1_LCV01D",
        "P1_FT03Z",
        "P1_FT01Z"
      ],
      "monitored_invariant": "temporal inertia / delay of tank level",
      "training_requirement": "normal-data-training",
      "confidence": "medium"
    },
    {
      "detector_id": "D4_P1_THERMAL",
      "detector_class": "D4",
      "purpose": "Model thermal inertia of the boiler, heating tank and cooler response.",
      "inputs": [
        "P1_TIT01",
        "P1_TIT02",
        "P1_TIT03",
        "P1_FCV01D",
        "P1_FCV02D",
        "P1_PP04"
      ],
      "monitored_invariant": "temporal thermal dynamics / delays",
      "training_requirement": "normal-data-training",
      "confidence": "medium"
    },
    {
      "detector_id": "D4_P2_SPEED_RAMP",
      "detector_class": "D4",
      "purpose": "Model the turbine speed ramp (zero to minimum speed at constant rate) and PID settling dynamics.",
      "inputs": [
        "P2_AutoSD",
        "P2_ManualSD",
        "P2_SIT01",
        "P2_SCO"
      ],
      "monitored_invariant": "temporal ramp / inertia / settling",
      "training_requirement": "normal-data-training",
      "confidence": "medium"
    },
    {
      "detector_id": "D4_P2_VIB_DYNAMICS",
      "detector_class": "D4",
      "purpose": "Model the temporal/oscillatory dependence between the four vibration probes and the phase signal.",
      "inputs": [
        "P2_VIBTR01",
        "P2_VIBTR02",
        "P2_VIBTR03",
        "P2_VIBTR04",
        "P2_VT01"
      ],
      "monitored_invariant": "temporal waveform / cross-probe dependence",
      "training_requirement": "normal-data-training",
      "confidence": "medium"
    },
    {
      "detector_id": "D4_P3_LEVEL_DYN",
      "detector_class": "D4",
      "purpose": "Model reservoir level dynamics and pump/valve response delays.",
      "inputs": [
        "P3_LIT01",
        "P3_LCP01D",
        "P3_LCV01D",
        "P3_FIT01"
      ],
      "monitored_invariant": "temporal reservoir dynamics / delays",
      "training_requirement": "normal-data-training",
      "confidence": "medium"
    },
    {
      "detector_id": "D4_P4_DYNAMICS",
      "detector_class": "D4",
      "purpose": "Model HIL generator load-following, governor-ramp and gate-opening dynamics.",
      "inputs": [
        "P4_ST_GOV",
        "P4_ST_LD",
        "P4_ST_PO",
        "P4_HT_PO",
        "P4_LD"
      ],
      "monitored_invariant": "temporal load-following dynamics",
      "training_requirement": "normal-data-training",
      "confidence": "medium"
    },
    {
      "detector_id": "D5_P1_FCV01_TRACK",
      "detector_class": "D5",
      "purpose": "Residual between FCV01 command and measured position.",
      "inputs": [
        "P1_FCV01D",
        "P1_FCV01Z"
      ],
      "monitored_invariant": "actuator command/feedback consistency",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D5_P1_FCV02_TRACK",
      "detector_class": "D5",
      "purpose": "Residual between FCV02 command and measured position (large actuator lag).",
      "inputs": [
        "P1_FCV02D",
        "P1_FCV02Z"
      ],
      "monitored_invariant": "actuator command/feedback consistency",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D5_P1_FCV03_TRACK",
      "detector_class": "D5",
      "purpose": "Residual between FCV03 command and measured position.",
      "inputs": [
        "P1_FCV03D",
        "P1_FCV03Z"
      ],
      "monitored_invariant": "actuator command/feedback consistency",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D5_P1_LCV01_TRACK",
      "detector_class": "D5",
      "purpose": "Residual between LCV01 command and measured position.",
      "inputs": [
        "P1_LCV01D",
        "P1_LCV01Z"
      ],
      "monitored_invariant": "actuator command/feedback consistency",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D5_P1_PCV01_TRACK",
      "detector_class": "D5",
      "purpose": "Residual between PCV01 command and measured position.",
      "inputs": [
        "P1_PCV01D",
        "P1_PCV01Z"
      ],
      "monitored_invariant": "actuator command/feedback consistency",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D5_P1_PCV02_TRACK",
      "detector_class": "D5",
      "purpose": "Residual between PCV02 command and measured position.",
      "inputs": [
        "P1_PCV02D",
        "P1_PCV02Z"
      ],
      "monitored_invariant": "actuator command/feedback consistency",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D5_P1_FC03_FLOW",
      "detector_class": "D5",
      "purpose": "Residual between the outflow setpoint and measured outflow rate (P1-FC loop closure).",
      "inputs": [
        "x1002_08_SETPOINT_OUT",
        "P1_FT03Z",
        "P1_FT03",
        "P1_FCV03Z"
      ],
      "monitored_invariant": "setpoint/PV control-loop consistency",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D5_P1_FC02_FLOW",
      "detector_class": "D5",
      "purpose": "Residual between the heat-transfer flow setpoint and measured FT02 flow.",
      "inputs": [
        "x1003_10_SETPOINT_OUT",
        "P1_FT02Z",
        "P1_FT02",
        "P1_FCV01Z"
      ],
      "monitored_invariant": "setpoint/PV control-loop consistency",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D5_P1_LC_LEVEL",
      "detector_class": "D5",
      "purpose": "Residual between the level setpoint and measured tank level (P1-LC loop closure).",
      "inputs": [
        "x1002_07_SETPOINT_OUT",
        "P1_LIT01",
        "P1_LCV01Z",
        "P1_FT03Z"
      ],
      "monitored_invariant": "setpoint/PV control-loop consistency",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D5_P1_TC_TEMP",
      "detector_class": "D5",
      "purpose": "Residual between the temperature setpoint and measured TIT01, including the valve/flow inner loop.",
      "inputs": [
        "x1003_18_SETPOINT_OUT",
        "P1_TIT01",
        "P1_FCV01D",
        "P1_FCV02D",
        "P1_FT02Z"
      ],
      "monitored_invariant": "cascade setpoint/PV and inner-loop consistency",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D5_P1_PC_PRESS",
      "detector_class": "D5",
      "purpose": "Residual between the assigned pressure setpoint and measured PIT01 (P1-PC loop closure).",
      "inputs": [
        "x1001_15_ASSIGN_OUT",
        "x1001_05_SETPOINT_OUT",
        "P1_PIT01",
        "P1_PCV01Z",
        "P1_PCV02Z"
      ],
      "monitored_invariant": "setpoint/PV control-loop consistency",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D5_P1_CC_COOLING",
      "detector_class": "D5",
      "purpose": "Causal consistency between cooler-pump output, cooler setpoint and main-tank temperature.",
      "inputs": [
        "P1_PP04",
        "P1_PP04SP",
        "P1_PP04D",
        "P1_TIT03"
      ],
      "monitored_invariant": "actuator/cooling-demand causality",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D5_P1_MASS_BALANCE",
      "detector_class": "D5",
      "purpose": "Mass-balance consistency of the return tank (inflow - outflow vs level change).",
      "inputs": [
        "P1_FT01Z",
        "P1_FT03Z",
        "P1_LIT01",
        "P1_FT02Z"
      ],
      "monitored_invariant": "physical mass-conservation relation",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D5_P2_SC",
      "detector_class": "D5",
      "purpose": "Speed-loop consistency: SIT01 vs active setpoint vs controller output and STM frequency coupling.",
      "inputs": [
        "P2_SIT01",
        "P2_AutoSD",
        "P2_ManualSD",
        "P2_SCO",
        "P2_SCST"
      ],
      "monitored_invariant": "speed control-loop and HIL coupling consistency",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D5_P3_LEVEL",
      "detector_class": "D5",
      "purpose": "Reservoir level-loop consistency: LIT01 vs valve/pump demands and inflow.",
      "inputs": [
        "P3_LIT01",
        "P3_LCV01D",
        "P3_LCP01D",
        "P3_FIT01",
        "P3_PIT01"
      ],
      "monitored_invariant": "level control-loop / mass-balance consistency",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D5_P3_PUMP",
      "detector_class": "D5",
      "purpose": "Pump consistency: speed command vs discharge pressure and flow.",
      "inputs": [
        "P3_LCP01D",
        "P3_PIT01",
        "P3_FIT01"
      ],
      "monitored_invariant": "pump actuator/head/flow consistency",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D5_P4_ST_POWER",
      "detector_class": "D5",
      "purpose": "Steam-turbine generation consistency: load demand vs output power vs governor opening.",
      "inputs": [
        "P4_ST_LD",
        "P4_ST_PO",
        "P4_ST_GOV"
      ],
      "monitored_invariant": "power-balance / actuator causality",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D5_P4_HT_POWER",
      "detector_class": "D5",
      "purpose": "Hydro/thermal-machine generation consistency: scheduled demand vs output power.",
      "inputs": [
        "P4_HT_PS",
        "P4_HT_PO"
      ],
      "monitored_invariant": "power-balance consistency",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D5_P4_LOAD_BAL",
      "detector_class": "D5",
      "purpose": "Aggregate load consistency: total demand vs sum of STM/HTM output powers.",
      "inputs": [
        "P4_LD",
        "P4_ST_PO",
        "P4_HT_PO",
        "P4_ST_LD",
        "P4_HT_PS"
      ],
      "monitored_invariant": "load-allocation / energy-balance consistency",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D5_P4_FREQ_COUPLE",
      "detector_class": "D5",
      "purpose": "Frequency coupling between steam-turbine model frequency and turbine rotor speed / HTM frequency.",
      "inputs": [
        "P4_ST_FD",
        "P4_HT_FD",
        "P2_SCST",
        "P2_SIT01"
      ],
      "monitored_invariant": "physical frequency coupling",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D5_P4_STEAM",
      "detector_class": "D5",
      "purpose": "Steam-state consistency: pressure vs temperature vs governor opening vs power.",
      "inputs": [
        "P4_ST_PT01",
        "P4_ST_TT01",
        "P4_ST_GOV",
        "P4_ST_PO"
      ],
      "monitored_invariant": "thermodynamic/hydraulic consistency",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D5_HEX_COUPLE",
      "detector_class": "D5",
      "purpose": "Cross-subsystem coupling between boiler heat-exchanger temperature and HIL steam temperature / pressure.",
      "inputs": [
        "P1_TIT01",
        "P1_PIT01",
        "P4_ST_TT01",
        "P4_ST_PT01"
      ],
      "monitored_invariant": "cross-subsystem physical coupling",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D5_PC_PV_FLOW",
      "detector_class": "D5",
      "purpose": "Auxiliary pressure/flow consistency of the boiler water circuit.",
      "inputs": [
        "P1_PIT01",
        "P1_PIT02",
        "P1_FT01Z",
        "P1_FT02Z"
      ],
      "monitored_invariant": "hydraulic consistency between pressures and flows",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    }
  ],
  "routing": {
    "P1_FCV01D": [
      "D5_P1_FCV01_TRACK",
      "D4_P1_FCV_PROFILE",
      "D3_P1_TC_SPLIT"
    ],
    "P1_FCV01Z": [
      "D5_P1_FCV01_TRACK",
      "D2_P1_VALVE_POS",
      "D4_P1_FCV_PROFILE"
    ],
    "P1_FCV02D": [
      "D5_P1_FCV02_TRACK",
      "D4_P1_FCV_PROFILE",
      "D1_P1_VALVE_RANGE",
      "D3_P1_TC_SPLIT"
    ],
    "P1_FCV02Z": [
      "D5_P1_FCV02_TRACK",
      "D2_P1_VALVE_POS",
      "D1_P1_VALVE_RANGE"
    ],
    "P1_FCV03D": [
      "D5_P1_FCV03_TRACK",
      "D4_P1_FCV_PROFILE"
    ],
    "P1_FCV03Z": [
      "D5_P1_FCV03_TRACK",
      "D2_P1_VALVE_POS"
    ],
    "P1_FT01": [
      "D5_PC_PV_FLOW",
      "D2_P1_SENSOR_NOISE",
      "D4_P1_LIT_INERTIA"
    ],
    "P1_FT01Z": [
      "D5_PC_PV_FLOW",
      "D5_P1_MASS_BALANCE",
      "D2_P1_SENSOR_NOISE"
    ],
    "P1_FT02": [
      "D5_P1_TC_TEMP",
      "D2_P1_SENSOR_NOISE",
      "D4_P1_THERMAL"
    ],
    "P1_FT02Z": [
      "D5_P1_FC02_FLOW",
      "D2_P1_SENSOR_NOISE"
    ],
    "P1_FT03": [
      "D5_P1_FC03_FLOW",
      "D2_P1_SENSOR_NOISE",
      "D4_P1_LIT_INERTIA"
    ],
    "P1_FT03Z": [
      "D5_P1_FC03_FLOW",
      "D5_P1_MASS_BALANCE",
      "D2_P1_SENSOR_NOISE"
    ],
    "P1_LCV01D": [
      "D5_P1_LCV01_TRACK",
      "D4_P1_FCV_PROFILE"
    ],
    "P1_LCV01Z": [
      "D5_P1_LCV01_TRACK",
      "D2_P1_VALVE_POS"
    ],
    "P1_LIT01": [
      "D5_P1_LC_LEVEL",
      "D2_P1_SENSOR_NOISE",
      "D4_P1_LIT_INERTIA",
      "D5_P1_MASS_BALANCE"
    ],
    "P1_PCV01D": [
      "D5_P1_PCV01_TRACK",
      "D4_P1_FCV_PROFILE",
      "D3_P1_PC_SPLIT"
    ],
    "P1_PCV01Z": [
      "D5_P1_PCV01_TRACK",
      "D2_P1_VALVE_POS"
    ],
    "P1_PCV02D": [
      "D3_P1_PC_SPLIT",
      "D1_P1_VALVE_RANGE",
      "D4_P1_FCV_PROFILE"
    ],
    "P1_PCV02Z": [
      "D3_P1_PC_SPLIT",
      "D5_P1_PCV02_TRACK"
    ],
    "P1_PIT01": [
      "D5_P1_PC_PRESS",
      "D1_P1_HH_TRIP",
      "D2_P1_SENSOR_NOISE"
    ],
    "P1_PIT01_HH": [
      "D1_P1_HH_TRIP"
    ],
    "P1_PIT02": [
      "D2_P1_AUX_PRESSURE",
      "D5_PC_PV_FLOW"
    ],
    "P1_PP01AD": [
      "D1_BLR_INTERLOCK"
    ],
    "P1_PP01AR": [
      "D1_BLR_INTERLOCK"
    ],
    "P1_PP01BD": [
      "D1_BLR_INTERLOCK"
    ],
    "P1_PP01BR": [
      "D1_BLR_INTERLOCK"
    ],
    "P1_PP02D": [
      "D1_BLR_INTERLOCK"
    ],
    "P1_PP02R": [
      "D1_BLR_INTERLOCK"
    ],
    "P1_PP04": [
      "D5_P1_CC_COOLING",
      "D4_P1_THERMAL",
      "D2_P1_AUX_PRESSURE"
    ],
    "P1_PP04D": [
      "D1_BLR_INTERLOCK"
    ],
    "P1_PP04SP": [
      "D1_SETPOINT_ENVELOPE",
      "D4_P1_SP_SEQUENCE",
      "D3_P1_SP_GROUP"
    ],
    "P1_SOL01D": [
      "D1_P1_VALVE_PERMISSIVE"
    ],
    "P1_SOL03D": [
      "D1_P1_VALVE_PERMISSIVE"
    ],
    "P1_STSP": [
      "D1_BLR_INTERLOCK"
    ],
    "P1_TIT01": [
      "D5_P1_TC_TEMP",
      "D2_P1_SENSOR_NOISE",
      "D4_P1_THERMAL",
      "D5_HEX_COUPLE"
    ],
    "P1_TIT02": [
      "D2_P1_SENSOR_NOISE",
      "D4_P1_THERMAL",
      "D5_P1_TC_TEMP"
    ],
    "P1_TIT03": [
      "D5_P1_CC_COOLING",
      "D2_P1_COOL_TEMP",
      "D4_P1_THERMAL"
    ],
    "P2_24Vdc": [
      "D2_P2_ELECTRICAL"
    ],
    "P2_ATSW_Lamp": [
      "D1_P2_MODE"
    ],
    "P2_AutoGO": [
      "D1_P2_MODE",
      "D3_P2_SP_MODE"
    ],
    "P2_AutoSD": [
      "D4_P2_SPEED_RAMP",
      "D5_P2_SC",
      "D3_P2_SP_MODE"
    ],
    "P2_Emerg": [
      "D1_P2_TRIP",
      "D1_P2_MODE"
    ],
    "P2_MASW": [
      "D1_P2_MODE",
      "D3_P2_SP_MODE"
    ],
    "P2_MASW_Lamp": [
      "D1_P2_MODE"
    ],
    "P2_ManualGO": [
      "D1_P2_MODE",
      "D3_P2_SP_MODE"
    ],
    "P2_ManualSD": [
      "D4_P2_SPEED_RAMP",
      "D5_P2_SC",
      "D3_P2_SP_MODE"
    ],
    "P2_OnOff": [
      "D1_P2_MODE"
    ],
    "P2_RTR": [
      "D1_P2_TRIP"
    ],
    "P2_SCO": [
      "D5_P2_SC",
      "D2_P2_ELECTRICAL",
      "D4_P2_SPEED_RAMP"
    ],
    "P2_SCST": [
      "D5_P2_SC",
      "D2_P2_PHASE"
    ],
    "P2_SIT01": [
      "D5_P2_SC",
      "D4_P2_SPEED_RAMP",
      "D2_P2_PHASE",
      "D1_P2_TRIP"
    ],
    "P2_TripEx": [
      "D1_P2_TRIP",
      "D1_P2_MODE"
    ],
    "P2_VIBTR01": [
      "D2_P2_VIB_DYN",
      "D4_P2_VIB_DYNAMICS",
      "D1_P2_TRIP"
    ],
    "P2_VIBTR02": [
      "D2_P2_VIB_DYN",
      "D4_P2_VIB_DYNAMICS",
      "D1_P2_TRIP"
    ],
    "P2_VIBTR03": [
      "D2_P2_VIB_DYN",
      "D4_P2_VIB_DYNAMICS",
      "D1_P2_TRIP"
    ],
    "P2_VIBTR04": [
      "D2_P2_VIB_DYN",
      "D4_P2_VIB_DYNAMICS",
      "D1_P2_TRIP"
    ],
    "P2_VT01": [
      "D2_P2_PHASE",
      "D4_P2_VIB_DYNAMICS"
    ],
    "P2_VTR01": [
      "D1_P2_TRIP"
    ],
    "P2_VTR02": [
      "D1_P2_TRIP"
    ],
    "P2_VTR03": [
      "D1_P2_TRIP"
    ],
    "P2_VTR04": [
      "D1_P2_TRIP"
    ],
    "P3_FIT01": [
      "D2_P3_INFLOW",
      "D5_P3_LEVEL",
      "D5_P3_PUMP"
    ],
    "P3_LCP01D": [
      "D5_P3_PUMP",
      "D4_P3_LEVEL_DYN",
      "D3_P3_DISPATCH"
    ],
    "P3_LCV01D": [
      "D5_P3_LEVEL",
      "D4_P3_LEVEL_DYN",
      "D3_P3_DISPATCH"
    ],
    "P3_LH01": [
      "D1_P3_LEVELSW"
    ],
    "P3_LIT01": [
      "D5_P3_LEVEL",
      "D2_P3_INFLOW",
      "D4_P3_LEVEL_DYN",
      "D1_P3_LEVELSW"
    ],
    "P3_LL01": [
      "D1_P3_LEVELSW"
    ],
    "P3_PIT01": [
      "D2_P3_INFLOW",
      "D5_P3_PUMP"
    ],
    "P4_HT_FD": [
      "D2_P4_FREQ",
      "D5_P4_FREQ_COUPLE"
    ],
    "P4_HT_PO": [
      "D5_P4_HT_POWER",
      "D5_P4_LOAD_BAL",
      "D2_P4_LOAD"
    ],
    "P4_HT_PS": [
      "D3_P4_LOAD_ALLOC",
      "D4_P1_SP_SEQUENCE",
      "D1_SETPOINT_ENVELOPE"
    ],
    "P4_LD": [
      "D3_P4_LOAD_ALLOC",
      "D5_P4_LOAD_BAL",
      "D4_P1_SP_SEQUENCE"
    ],
    "P4_ST_FD": [
      "D2_P4_FREQ",
      "D5_P4_FREQ_COUPLE"
    ],
    "P4_ST_GOV": [
      "D5_P4_ST_POWER",
      "D4_P4_DYNAMICS",
      "D2_P4_LOAD"
    ],
    "P4_ST_LD": [
      "D5_P4_ST_POWER",
      "D3_P4_LOAD_ALLOC",
      "D4_P4_DYNAMICS"
    ],
    "P4_ST_PO": [
      "D5_P4_ST_POWER",
      "D5_P4_LOAD_BAL",
      "D2_P4_LOAD"
    ],
    "P4_ST_PS": [
      "D3_P4_LOAD_ALLOC",
      "D4_P1_SP_SEQUENCE",
      "D1_SETPOINT_ENVELOPE"
    ],
    "P4_ST_PT01": [
      "D5_P4_STEAM",
      "D2_P4_STEAM"
    ],
    "P4_ST_TT01": [
      "D5_P4_STEAM",
      "D2_P4_STEAM",
      "D5_HEX_COUPLE"
    ],
    "x1001_05_SETPOINT_OUT": [
      "D4_P1_SP_SEQUENCE",
      "D2_P1_SENSOR_NOISE",
      "D5_P1_PC_PRESS"
    ],
    "x1001_15_ASSIGN_OUT": [
      "D4_P1_SP_SEQUENCE",
      "D5_P1_PC_PRESS",
      "D3_P1_SP_GROUP"
    ],
    "x1002_07_SETPOINT_OUT": [
      "D5_P1_LC_LEVEL",
      "D4_P1_SP_SEQUENCE",
      "D3_P1_SP_GROUP"
    ],
    "x1002_08_SETPOINT_OUT": [
      "D5_P1_FC03_FLOW",
      "D4_P1_SP_SEQUENCE",
      "D3_P1_SP_GROUP"
    ],
    "x1003_10_SETPOINT_OUT": [
      "D5_P1_FC02_FLOW",
      "D4_P1_SP_SEQUENCE",
      "D3_P1_SP_GROUP"
    ],
    "x1003_18_SETPOINT_OUT": [
      "D4_P1_SP_SEQUENCE",
      "D2_P1_SENSOR_NOISE",
      "D5_P1_TC_TEMP"
    ],
    "x1003_24_SUM_OUT": [
      "D4_P1_SP_SEQUENCE",
      "D2_P1_SENSOR_NOISE",
      "D5_P1_TC_TEMP"
    ]
  },
  "dependencies": [
    {
      "source": "D1_BLR_INTERLOCK",
      "target": "D1_P1_VALVE_PERMISSIVE",
      "relationship": "Boiler run permissive gates valve permissives"
    },
    {
      "source": "D1_BLR_INTERLOCK",
      "target": "P1-PC zone",
      "relationship": "Pump/run interlocks gate all P1 control-loop detectors"
    },
    {
      "source": "D1_P1_HH_TRIP",
      "target": "D5_P1_PC_PRESS",
      "relationship": "Protection trip overrides pressure-loop residual interpretation"
    },
    {
      "source": "D1_P2_TRIP",
      "target": "D4_P2_SPEED_RAMP",
      "relationship": "Trip overrides speed-control dynamics"
    },
    {
      "source": "D1_P2_MODE",
      "target": "D3_P2_SP_MODE",
      "relationship": "Mode state machine constrains active setpoint configuration"
    },
    {
      "source": "D4_P1_SP_SEQUENCE",
      "target": "D3_P1_SP_GROUP",
      "relationship": "Setpoint sequence feeds the joint setpoint configuration"
    },
    {
      "source": "D3_P1_SP_GROUP",
      "target": "D5_P1_LC_LEVEL",
      "relationship": "Setpoint configuration conditions loop residuals"
    },
    {
      "source": "D5_P1_FC03_FLOW",
      "target": "D4_P1_LIT_INERTIA",
      "relationship": "Outflow feed-forward drives tank-level dynamics"
    },
    {
      "source": "D4_P1_LIT_INERTIA",
      "target": "D5_P1_LC_LEVEL",
      "relationship": "Level dynamics define expected level-loop residual"
    },
    {
      "source": "D5_P4_FREQ_COUPLE",
      "target": "D4_P2_SPEED_RAMP",
      "relationship": "STM grid-frequency deviation perturbs turbine speed dynamics"
    },
    {
      "source": "D5_P4_ST_POWER",
      "target": "D5_P4_LOAD_BAL",
      "relationship": "Unit generation feeds aggregate load balance"
    },
    {
      "source": "D5_P4_HT_POWER",
      "target": "D5_P4_LOAD_BAL",
      "relationship": "Unit generation feeds aggregate load balance"
    },
    {
      "source": "D5_HEX_COUPLE",
      "target": "P1-TC zone",
      "relationship": "Steam-side temperature couples to boiler heat-exchanger temperature"
    },
    {
      "source": "D1_P3_LEVELSW",
      "target": "D5_P3_LEVEL",
      "relationship": "Reservoir protection limits condition level-loop monitoring"
    }
  ],
  "unresolved": [
    "The seven `x100*_*_OUT` tags are not described in the HAI 23.05 data-point table. Their roles were inferred from correlation with documented variables (e.g. x1002_08 <-> P1_FT03Z, x1003_10 <-> P1_FT02Z) and from the HAIEnd control-logic blocks 1001/1002/1003; the exact block-to-tag mapping in dcs_1001h.json/dcs_1002h.json/dcs_1003h.json must be confirmed.",
    "Operator setpoints documented for HAI (P1_B2016, P1_B3004, P1_B3005, P1_B4002, P1_B400B) are absent from the 23.05 CSV. It is assumed they are represented by the x1001_15/x1002_07/x1002_08/x1003_10/x1003_18 internal points; this assumption requires expert validation.",
    "P1_PIT01_HH, P1_SOL01D and P1_SOL03D are constant 524320 in the training data although the documentation declares 0-10 bar / Boolean ranges. This is presumably a signal-quality/placeholder code; the true semantics must be confirmed before rule thresholds are set.",
    "P1_PP01AD/P1_PP01AR/P1_PP01BD/P1_PP01BR/P1_PP02D/P1_PP02R, P1_STSP, P2_Emerg, P2_OnOff, P2_RTR, P2_TripEx, P2_VTR01-04, P3_LH01, P3_LL01 are constant during normal operation. D1 rules for them cannot be calibrated on these data and must come from controller documentation (constant tags give no transition evidence).",
    "Two conflicting normal ranges for the turbine speed setpoints appear in the documentation (AutoSD [100,120] RPM in the HMM figure vs [11,12] for ManualSD); the observed AutoSD range is ~100.7-129.4 and ManualSD ~0-12.9, so the documented ManualSD range appears inconsistent and must be resolved.",
    "P1_PP04D (cooling-pump run command) is not listed in the HAI data-point table; its role was inferred from the HAIEnd graph (DM-PP04-D) and its 37.5% duty cycle.",
    "P4_HT_LD (electrical load demand of HTM) is referenced in the documentation but is not present in the 23.05 CSV; the HTM load-balance detector therefore uses P4_HT_PS / P4_HT_PO only.",
    "Several units are undocumented or dimensionless ('-'): P3_FIT01, P3_LCP01D, P3_LCV01D, P3_PIT01, P4_ST_GOV, P4_ST_PT01, P4_ST_TT01. Range/limit rules for these signals require unit clarification.",
    "label-test2.csv timestamps are truncated to the minute ('2022-08-17 0:00') and do not align with the second-resolution timestamps of hai-test2.csv; label alignment must be repaired before any later evaluation (not used at this configuration stage).",
    "P2_SCST is documented in RPM as 'speed change proportional to frequency change of the STM' and takes near-constant values (~720) for long periods with occasional small steps; its dynamic role in the speed loop needs clarification.",
    "The physical boiler graph (phy_boiler.json) does not expose numeric tag names for most devices (only DM-* labels), so several cross-subsystem relations (e.g. HEX01S/TK02 coupling) are taken from the process control description rather than from tag-level wiring.",
    "The HMM normal-operation model uses only seven setpoints and a subset of controllers; the coverage of P4 HIL setpoints (P4_ST_PS, P4_HT_PS) by the HMM in the 23.05 release is not fully documented.",
    "Detector thresholds for the D1 protection group (P1_PIT01_HH, P2_RTR, P2_VTR*) must be read from the DCS project files; the CSV only contains the constant runtime values."
  ]
}
```
