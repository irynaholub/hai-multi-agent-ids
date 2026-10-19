# HAI 23.05 — Process-Oriented Anomaly-Detector Architecture

## Scope and interpretation

This document applies the supplied detector-routing instruction to the **HAI 23.05** industrial-control-system dataset. It configures process-anomaly detector classes only. It **does not perform anomaly detection**, does **not use attack labels to infer detector routing**, and does **not classify anomalies as cyberattacks**.

The architecture is based primarily on process semantics: boiler feedback loops and actuator feedback (P1), turbine speed/trip logic (P2), water-treatment level/hydraulic behavior (P3), and the steam-/hydropower HIL model plus cross-zone coupling (P4). Normal-operation files are proposed only for calibration/training of expected behavior.

### Dataset basis

- Official repository: `https://github.com/icsdataset/hai`
- HAI 23.05 directory: `https://github.com/icsdataset/hai/tree/master/hai-23.05`
- Technical manual: `https://github.com/icsdataset/hai/blob/master/hai_dataset_technical_details.pdf`
- HAI 23.05 provides four normal/training files (`hai-train1` … `hai-train4`) and two test files, sampled as SCADA time series.
- The official repository reports **86 process data points per second** for HAI 23.05.
- The testbed has four coupled process zones: P1 boiler, P2 turbine/rotor kit, P3 water treatment, and P4 HIL simulation.

> **Schema caution.** The technical manual's cross-version table is numbered 1–87 although the official HAI 23.05 summary reports 86 points/s. Because the Git-LFS CSV header is not rendered by GitHub's web page, the table below characterizes all 87 documented candidate names. Before implementation, intersect this routing map with the actual HAI 23.05 CSV header. This uncertainty is intentionally preserved rather than resolved by guessing.

## Detector-class legend

| Class | Meaning |
|---|---|
| D1 | Rule-based detector: explicit engineering, Boolean, transition, operational or protection constraints. |
| D2 | Statistical detector: stable univariate/small-group properties, abrupt deviation or drift. |
| D3 | Multivariate configuration detector: individually valid values can form an invalid simultaneous configuration. |
| D4 | Temporal-dynamics detector: sequence, inertia, lag, ramp, settling or previous-state dependence. |
| D5 | Consistency/residual detector: physical, causal, functional or control-loop relationship among variables. |

# A. Variable characterization table

| Tag | Subsystem | Functional role | Signal type | Dominant normal-behavior invariant | Recommended detector class(es) / instances | Related variables | Reasoning | Confidence |
|---|---|---|---|---|---|---|---|---|
| `P1_B2004` | P1 | Heat-exchanger outlet pressure setpoint/reference. | setpoint | Valid pressure-reference configuration; exact relation to B2016 must be established. | D1 `D1-P1-ENG-RANGE`, D3 `D3-P1-PC-CONFIG` | `P1_B2016`, `P1_PIT01`, `P1_STSP` | Use hard domain rules for impossible values and a configuration detector for valid-but-incompatible simultaneous settings. | low |
| `P1_B2016` | P1 | Pressure demand used by the documented P1-PC feedback loop. | setpoint/demand | SP–PV–CV consistency and normal pressure-loop dynamics. | D1 `D1-P1-ENG-RANGE`, D3 `D3-P1-PC-CONFIG`, D5 `D5-P1-PC-LOOP`, D4 `D4-P1-PC-DYNAMICS` | `P1_PIT01`, `P1_PCV01D`, `P1_PCV02D` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P1_B3004` | P1 | Return-water-tank level setpoint. | setpoint | Level-control residual and tank-level temporal response. | D1 `D1-P1-ENG-RANGE`, D5 `D5-P1-LC-LOOP`, D4 `D4-P1-LC-DYNAMICS` | `P1_LIT01`, `P1_LCV01D`, `P1_FCV03D` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P1_B3005` | P1 | Return-water-tank discharge-flow setpoint. | setpoint | Flow SP–PV–valve consistency. | D1 `D1-P1-ENG-RANGE`, D5 `D5-P1-FC-LOOP` | `P1_FT03`, `P1_FT03Z`, `P1_FCV03D` | The tag is meaningful mainly through an engineering/causal relationship with other process variables; an isolated univariate detector would lose that invariant. | high |
| `P1_B4002` | P1 | Heat-exchanger outlet temperature setpoint; also referenced as a P1-TC target in scenario documentation. | setpoint | Valid temperature-control configuration plus thermal-loop residual/dynamics. | D1 `D1-P1-ENG-RANGE`, D3 `D3-P1-TC-CONFIG`, D5 `D5-P1-TC-LOOP`, D4 `D4-P1-TC-DYNAMICS` | `P1_B4022`, `P1_TIT01`, `P1_B4005`, `P1_FCV01D` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | medium |
| `P1_B4005` | P1 | Temperature PID control output. | control output | Must be compatible with temperature error, cascade stage and valve actions. | D1 `D1-P1-ENG-RANGE`, D3 `D3-P1-TC-CONFIG`, D5 `D5-P1-TC-LOOP` | `P1_TIT01`, `P1_B4022`, `P1_FCV01D`, `P1_FCV02D` | The tag is meaningful mainly through an engineering/causal relationship with other process variables; an isolated univariate detector would lose that invariant. | medium |
| `P1_B400B` | P1 | Heating-water-tank water-outflow-rate setpoint. | setpoint | Thermal/hydraulic operating configuration must remain consistent with heating-water flow and temperatures. | D1 `D1-P1-ENG-RANGE`, D3 `D3-P1-TC-CONFIG`, D5 `D5-P1-THERMAL-CONSISTENCY` | `P1_FT02Z`, `P1_TIT02`, `P1_TIT01` | The tag is meaningful mainly through an engineering/causal relationship with other process variables; an isolated univariate detector would lose that invariant. | medium |
| `P1_B4022` | P1 | Temperature demand used by the documented P1-TC loop. | setpoint/demand | Temperature SP–PV–cascade-action consistency and thermal dynamics. | D1 `D1-P1-ENG-RANGE`, D3 `D3-P1-TC-CONFIG`, D5 `D5-P1-TC-LOOP`, D4 `D4-P1-TC-DYNAMICS` | `P1_TIT01`, `P1_FCV01D`, `P1_FCV02D`, `P1_FT02` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P1_FCV01D` | P1 | Position command for FCV01. | analog actuator command | Command must track process error/function and agree with measured actuator position. | D1 `D1-P1-ENG-RANGE`, D5 `D5-P1-ACTUATOR-TRACK`, D5 `D5-P1-TC-LOOP`, D4 `D4-P1-TC-DYNAMICS`, D5 `D5-P1-THERMAL-CONSISTENCY` | `P1_FCV01Z` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P1_FCV01Z` | P1 | Current position feedback for FCV01. | actuator feedback | Position must follow command within normal lag/tolerance. | D1 `D1-P1-ENG-RANGE`, D5 `D5-P1-ACTUATOR-TRACK`, D5 `D5-P1-TC-LOOP` | `P1_FCV01D` | The tag is meaningful mainly through an engineering/causal relationship with other process variables; an isolated univariate detector would lose that invariant. | high |
| `P1_FCV02D` | P1 | Position command for FCV02. | analog actuator command | Command must track process error/function and agree with measured actuator position. | D1 `D1-P1-ENG-RANGE`, D5 `D5-P1-ACTUATOR-TRACK`, D5 `D5-P1-TC-LOOP`, D4 `D4-P1-TC-DYNAMICS`, D5 `D5-P1-THERMAL-CONSISTENCY` | `P1_FCV02Z` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P1_FCV02Z` | P1 | Current position feedback for FCV02. | actuator feedback | Position must follow command within normal lag/tolerance. | D1 `D1-P1-ENG-RANGE`, D5 `D5-P1-ACTUATOR-TRACK`, D5 `D5-P1-TC-LOOP` | `P1_FCV02D` | The tag is meaningful mainly through an engineering/causal relationship with other process variables; an isolated univariate detector would lose that invariant. | high |
| `P1_FCV03D` | P1 | Position command for FCV03. | analog actuator command | Command must track process error/function and agree with measured actuator position. | D1 `D1-P1-ENG-RANGE`, D5 `D5-P1-ACTUATOR-TRACK`, D5 `D5-P1-FC-LOOP`, D5 `D5-P1-LC-LOOP`, D4 `D4-P1-LC-DYNAMICS`, D5 `D5-P1-MASS-BALANCE` | `P1_FCV03Z` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P1_FCV03Z` | P1 | Current position feedback for FCV03. | actuator feedback | Position must follow command within normal lag/tolerance. | D1 `D1-P1-ENG-RANGE`, D5 `D5-P1-ACTUATOR-TRACK`, D5 `D5-P1-FC-LOOP` | `P1_FCV03D` | The tag is meaningful mainly through an engineering/causal relationship with other process variables; an isolated univariate detector would lose that invariant. | high |
| `P1_FT01` | P1 | Raw differential-pressure/flow measurement paired with P1_FT01Z. | process variable / raw flow signal | Raw signal must agree with its engineering-unit conversion and subsystem flow behavior. | D1 `D1-P1-ENG-RANGE`, D5 `D5-P1-FLOW-CONVERSION`, D5 `D5-P1-MASS-BALANCE` | `P1_FT01Z` | The tag is meaningful mainly through an engineering/causal relationship with other process variables; an isolated univariate detector would lose that invariant. | high |
| `P1_FT01Z` | P1 | Engineering-unit flow value converted from P1_FT01. | derived process variable | Converted flow must agree with its raw signal and subsystem balance/control behavior. | D1 `D1-P1-ENG-RANGE`, D5 `D5-P1-FLOW-CONVERSION`, D5 `D5-P1-MASS-BALANCE` | `P1_FT01` | The tag is meaningful mainly through an engineering/causal relationship with other process variables; an isolated univariate detector would lose that invariant. | high |
| `P1_FT02` | P1 | Raw differential-pressure/flow measurement paired with P1_FT02Z. | process variable / raw flow signal | Raw signal must agree with its engineering-unit conversion and subsystem flow behavior. | D1 `D1-P1-ENG-RANGE`, D5 `D5-P1-FLOW-CONVERSION`, D5 `D5-P1-TC-LOOP`, D4 `D4-P1-TC-DYNAMICS`, D5 `D5-P1-THERMAL-CONSISTENCY`, D5 `D5-X-P1-P4-STEAM` | `P1_FT02Z` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P1_FT02Z` | P1 | Engineering-unit flow value converted from P1_FT02. | derived process variable | Converted flow must agree with its raw signal and subsystem balance/control behavior. | D1 `D1-P1-ENG-RANGE`, D5 `D5-P1-FLOW-CONVERSION`, D5 `D5-P1-TC-LOOP`, D4 `D4-P1-TC-DYNAMICS`, D5 `D5-P1-THERMAL-CONSISTENCY`, D5 `D5-X-P1-P4-STEAM` | `P1_FT02` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P1_FT03` | P1 | Raw differential-pressure/flow measurement paired with P1_FT03Z. | process variable / raw flow signal | Raw signal must agree with its engineering-unit conversion and subsystem flow behavior. | D1 `D1-P1-ENG-RANGE`, D5 `D5-P1-FLOW-CONVERSION`, D5 `D5-P1-FC-LOOP`, D5 `D5-P1-LC-LOOP`, D4 `D4-P1-LC-DYNAMICS`, D5 `D5-P1-MASS-BALANCE` | `P1_FT03Z` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P1_FT03Z` | P1 | Engineering-unit flow value converted from P1_FT03. | derived process variable | Converted flow must agree with its raw signal and subsystem balance/control behavior. | D1 `D1-P1-ENG-RANGE`, D5 `D5-P1-FLOW-CONVERSION`, D5 `D5-P1-FC-LOOP`, D5 `D5-P1-LC-LOOP`, D4 `D4-P1-LC-DYNAMICS`, D5 `D5-P1-MASS-BALANCE` | `P1_FT03` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P1_LCV01D` | P1 | Position command for return-water-tank level-control valve LCV01. | analog actuator command | Command–position agreement and consistency with level error/outflow disturbance. | D1 `D1-P1-ENG-RANGE`, D5 `D5-P1-ACTUATOR-TRACK`, D5 `D5-P1-LC-LOOP`, D4 `D4-P1-LC-DYNAMICS`, D5 `D5-P1-MASS-BALANCE` | `P1_LCV01Z`, `P1_LIT01`, `P1_B3004` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P1_LCV01Z` | P1 | Current position of LCV01. | actuator feedback | Position must track command and remain consistent with level response. | D1 `D1-P1-ENG-RANGE`, D5 `D5-P1-ACTUATOR-TRACK`, D5 `D5-P1-LC-LOOP` | `P1_LCV01D`, `P1_LIT01` | The tag is meaningful mainly through an engineering/causal relationship with other process variables; an isolated univariate detector would lose that invariant. | high |
| `P1_LIT01` | P1 | Return-water-tank level. | process variable | Level must follow LC setpoint and physically integrate net flow over time. | D1 `D1-P1-ENG-RANGE`, D5 `D5-P1-LC-LOOP`, D4 `D4-P1-LC-DYNAMICS`, D5 `D5-P1-MASS-BALANCE` | `P1_B3004`, `P1_LCV01D`, `P1_FT01Z`, `P1_FT03Z` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P1_PCV01D` | P1 | Position command for pressure-control valve PCV01. | analog actuator command | Command–position agreement and consistency with pressure-control error. | D1 `D1-P1-ENG-RANGE`, D5 `D5-P1-ACTUATOR-TRACK`, D5 `D5-P1-PC-LOOP`, D4 `D4-P1-PC-DYNAMICS` | `P1_PCV01Z`, `P1_PIT01`, `P1_B2016` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P1_PCV01Z` | P1 | Current position feedback for pressure-control valve PCV01. | actuator feedback | Position must track command and remain consistent with pressure-loop behavior. | D1 `D1-P1-ENG-RANGE`, D5 `D5-P1-ACTUATOR-TRACK`, D5 `D5-P1-PC-LOOP` | `P1_PCV01D`, `P1_PIT01` | The tag is meaningful mainly through an engineering/causal relationship with other process variables; an isolated univariate detector would lose that invariant. | high |
| `P1_PCV02D` | P1 | Position command for pressure-control valve PCV02. | analog actuator command | Command–position agreement and consistency with pressure-control error. | D1 `D1-P1-ENG-RANGE`, D5 `D5-P1-ACTUATOR-TRACK`, D5 `D5-P1-PC-LOOP`, D4 `D4-P1-PC-DYNAMICS` | `P1_PCV02Z`, `P1_PIT01`, `P1_B2016` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P1_PCV02Z` | P1 | Current position feedback for pressure-control valve PCV02. | actuator feedback | Position must track command and remain consistent with pressure-loop behavior. | D1 `D1-P1-ENG-RANGE`, D5 `D5-P1-ACTUATOR-TRACK`, D5 `D5-P1-PC-LOOP` | `P1_PCV02D`, `P1_PIT01` | The tag is meaningful mainly through an engineering/causal relationship with other process variables; an isolated univariate detector would lose that invariant. | high |
| `P1_PIT01` | P1 | Heat-exchanger outlet / pressure-control process pressure. | process variable | Pressure must be consistent with pressure demand, valve action and downstream steam-model state. | D1 `D1-P1-ENG-RANGE`, D3 `D3-P1-PC-CONFIG`, D5 `D5-P1-PC-LOOP`, D4 `D4-P1-PC-DYNAMICS`, D5 `D5-P1-PIT01HH-CONSISTENCY`, D5 `D5-X-P1-P4-STEAM` | `P1_B2016`, `P1_PCV01D`, `P1_PCV02D`, `P1_PIT01_HH`, `P4_ST_PT01` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P1_PIT01_HH` | P1 | Documented highest outlet pressure of the heat exchanger. | derived/monitor pressure signal | Must be consistent with PIT01 according to the actual high/highest aggregation or monitor logic. | D1 `D1-P1-ENG-RANGE`, D5 `D5-P1-PIT01HH-CONSISTENCY` | `P1_PIT01` | The tag is meaningful mainly through an engineering/causal relationship with other process variables; an isolated univariate detector would lose that invariant. | low |
| `P1_PIT02` | P1 | Heating-water-pump supply pressure. | process variable | State-conditional statistical stability and consistency with pump operation. | D1 `D1-P1-ENG-RANGE`, D2 `D2-P1-PIT02-STABILITY` | `P1_PP02D`, `P1_PP02R` | Use hard engineering bounds plus normal-operation calibration for tighter state-conditional stability. | medium |
| `P1_PP01AD` | P1 | Start command for pump PP01A. | discrete actuator command | Only Boolean values; run feedback must follow command with valid transition delay. | D1 `D1-P1-ENG-RANGE`, D1 `D1-P1-PUMP-STATE` | `P1_PP01AR` | The dominant invariant is explicit engineering, discrete-state or protection logic; a learned model is not required for the basic check. | high |
| `P1_PP01AR` | P1 | Running-state feedback for pump PP01A. | discrete state feedback | Running state must be logically compatible with command and permitted transition delay. | D1 `D1-P1-ENG-RANGE`, D1 `D1-P1-PUMP-STATE` | `P1_PP01AD` | The dominant invariant is explicit engineering, discrete-state or protection logic; a learned model is not required for the basic check. | high |
| `P1_PP01BD` | P1 | Start command for pump PP01B. | discrete actuator command | Only Boolean values; run feedback must follow command with valid transition delay. | D1 `D1-P1-ENG-RANGE`, D1 `D1-P1-PUMP-STATE` | `P1_PP01BR` | The dominant invariant is explicit engineering, discrete-state or protection logic; a learned model is not required for the basic check. | high |
| `P1_PP01BR` | P1 | Running-state feedback for pump PP01B. | discrete state feedback | Running state must be logically compatible with command and permitted transition delay. | D1 `D1-P1-ENG-RANGE`, D1 `D1-P1-PUMP-STATE` | `P1_PP01BD` | The dominant invariant is explicit engineering, discrete-state or protection logic; a learned model is not required for the basic check. | high |
| `P1_PP02D` | P1 | Start command for pump PP02. | discrete actuator command | Only Boolean values; run feedback must follow command with valid transition delay. | D1 `D1-P1-ENG-RANGE`, D1 `D1-P1-PUMP-STATE`, D2 `D2-P1-PIT02-STABILITY` | `P1_PP02R` | Use hard engineering bounds plus normal-operation calibration for tighter state-conditional stability. | high |
| `P1_PP02R` | P1 | Running-state feedback for pump PP02. | discrete state feedback | Running state must be logically compatible with command and permitted transition delay. | D1 `D1-P1-ENG-RANGE`, D1 `D1-P1-PUMP-STATE`, D2 `D2-P1-PIT02-STABILITY` | `P1_PP02D` | Use hard engineering bounds plus normal-operation calibration for tighter state-conditional stability. | high |
| `P1_PP04` | P1 | Cooling-water pump control output. | control output | Cooling command must be consistent with TIT03/PP04SP and produce plausible delayed thermal response. | D1 `D1-P1-ENG-RANGE`, D5 `D5-P1-CC-LOOP`, D4 `D4-P1-CC-DYNAMICS`, D5 `D5-P1-THERMAL-CONSISTENCY` | `P1_PP04SP`, `P1_TIT03` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P1_PP04SP` | P1 | Cooling-temperature setpoint. | setpoint | Cooling activation/output must be consistent with setpoint and main-tank temperature. | D1 `D1-P1-ENG-RANGE`, D5 `D5-P1-CC-LOOP`, D4 `D4-P1-CC-DYNAMICS` | `P1_PP04`, `P1_TIT03` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P1_SOL01D` | P1 | Main-water-tank supply-valve open command. | discrete actuator command | Valid Boolean state/transition and hydraulic consistency with net tank flow. | D1 `D1-P1-ENG-RANGE`, D1 `D1-P1-PLANT-STATE`, D5 `D5-P1-MASS-BALANCE` | `P1_SOL03D`, `P1_FT01Z`, `P1_LIT01` | The tag is meaningful mainly through an engineering/causal relationship with other process variables; an isolated univariate detector would lose that invariant. | medium |
| `P1_SOL03D` | P1 | Main-water-tank drain-valve open command. | discrete actuator command | Valid Boolean state/transition and hydraulic consistency with net tank flow. | D1 `D1-P1-ENG-RANGE`, D1 `D1-P1-PLANT-STATE`, D5 `D5-P1-MASS-BALANCE` | `P1_SOL01D`, `P1_FT03Z`, `P1_LIT01` | The tag is meaningful mainly through an engineering/causal relationship with other process variables; an isolated univariate detector would lose that invariant. | medium |
| `P1_STSP` | P1 | Boiler DCS start/stop command. | discrete process state/command | Valid Boolean plant state; other loop interpretation should be conditioned on plant running state. | D1 `D1-P1-ENG-RANGE`, D1 `D1-P1-PLANT-STATE`, D3 `D3-P1-PC-CONFIG` | `P1_SOL01D`, `P1_SOL03D`, `P1_B2016` | Use hard domain rules for impossible values and a configuration detector for valid-but-incompatible simultaneous settings. | medium |
| `P1_TIT01` | P1 | Heat-exchanger outlet temperature / P1-TC process variable. | process variable | Temperature-loop residual, thermal dynamics and steam-model coupling. | D1 `D1-P1-ENG-RANGE`, D3 `D3-P1-TC-CONFIG`, D5 `D5-P1-TC-LOOP`, D4 `D4-P1-TC-DYNAMICS`, D5 `D5-P1-THERMAL-CONSISTENCY`, D5 `D5-X-P1-P4-STEAM` | `P1_B4022`, `P1_FCV01D`, `P1_FCV02D`, `P1_FT02Z`, `P4_ST_TT01` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P1_TIT02` | P1 | Heating-water-tank temperature. | process variable | Thermal consistency with heating-water flow, valve action and outlet temperature. | D1 `D1-P1-ENG-RANGE`, D5 `D5-P1-TC-LOOP`, D4 `D4-P1-TC-DYNAMICS`, D5 `D5-P1-THERMAL-CONSISTENCY`, D5 `D5-X-P1-P4-STEAM` | `P1_FT02Z`, `P1_TIT01`, `P1_FCV01D`, `P1_FCV02D` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | medium |
| `P1_TIT03` | P1 | Main-water-tank temperature used by cooling control. | process variable | Cooling control residual and delayed thermal response. | D1 `D1-P1-ENG-RANGE`, D5 `D5-P1-CC-LOOP`, D4 `D4-P1-CC-DYNAMICS`, D5 `D5-P1-THERMAL-CONSISTENCY` | `P1_PP04SP`, `P1_PP04` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P2_24Vdc` | P2 | DCS 24-V input supply. | health/process-support variable | Stable supply around calibrated normal level; abrupt shifts/drift are abnormal. | D1 `D1-P2-ENG-RANGE`, D2 `D2-P2-24V-STABILITY` | — | Use hard engineering bounds plus normal-operation calibration for tighter state-conditional stability. | high |
| `P2_ATSW_Lamp` | P2 | Auto-mode switch lamp. | discrete state/command | Allowed Boolean combinations and transition order depend on operating/trip mode. | D1 `D1-P2-ENG-RANGE`, D1 `D1-P2-MODE-LOGIC` | `P2_MASW`, `P2_OnOff`, `P2_Emerg`, `P2_TripEx` | The dominant invariant is explicit engineering, discrete-state or protection logic; a learned model is not required for the basic check. | medium |
| `P2_AutoGo` | P2 | Auto start button. | discrete state/command | Allowed Boolean combinations and transition order depend on operating/trip mode. | D1 `D1-P2-ENG-RANGE`, D1 `D1-P2-MODE-LOGIC` | `P2_MASW`, `P2_OnOff`, `P2_Emerg`, `P2_TripEx` | The dominant invariant is explicit engineering, discrete-state or protection logic; a learned model is not required for the basic check. | medium |
| `P2_Emerg` | P2 | Emergency button/state. | discrete state/command | Allowed Boolean combinations and transition order depend on operating/trip mode. | D1 `D1-P2-ENG-RANGE`, D1 `D1-P2-MODE-LOGIC`, D1 `D1-P2-TRIP-LOGIC` | `P2_MASW`, `P2_OnOff`, `P2_Emerg`, `P2_TripEx` | The dominant invariant is explicit engineering, discrete-state or protection logic; a learned model is not required for the basic check. | medium |
| `P2_MASW` | P2 | Manual(1)/Auto(0) selector. | discrete state/command | Allowed Boolean combinations and transition order depend on operating/trip mode. | D1 `D1-P2-ENG-RANGE`, D1 `D1-P2-MODE-LOGIC` | `P2_MASW`, `P2_OnOff`, `P2_Emerg`, `P2_TripEx` | The dominant invariant is explicit engineering, discrete-state or protection logic; a learned model is not required for the basic check. | medium |
| `P2_MASW_Lamp` | P2 | Manual-mode lamp. | discrete state/command | Allowed Boolean combinations and transition order depend on operating/trip mode. | D1 `D1-P2-ENG-RANGE`, D1 `D1-P2-MODE-LOGIC` | `P2_MASW`, `P2_OnOff`, `P2_Emerg`, `P2_TripEx` | The dominant invariant is explicit engineering, discrete-state or protection logic; a learned model is not required for the basic check. | medium |
| `P2_ManualGO` | P2 | Manual start button. | discrete state/command | Allowed Boolean combinations and transition order depend on operating/trip mode. | D1 `D1-P2-ENG-RANGE`, D1 `D1-P2-MODE-LOGIC` | `P2_MASW`, `P2_OnOff`, `P2_Emerg`, `P2_TripEx` | The dominant invariant is explicit engineering, discrete-state or protection logic; a learned model is not required for the basic check. | medium |
| `P2_OnOff` | P2 | Turbine DCS on/off switch. | discrete state/command | Allowed Boolean combinations and transition order depend on operating/trip mode. | D1 `D1-P2-ENG-RANGE`, D1 `D1-P2-MODE-LOGIC`, D1 `D1-P2-TRIP-LOGIC` | `P2_MASW`, `P2_OnOff`, `P2_Emerg`, `P2_TripEx` | The dominant invariant is explicit engineering, discrete-state or protection logic; a learned model is not required for the basic check. | medium |
| `P2_TripEx` | P2 | Trip emergency exit/reset button. | discrete state/command | Allowed Boolean combinations and transition order depend on operating/trip mode. | D1 `D1-P2-ENG-RANGE`, D1 `D1-P2-MODE-LOGIC`, D1 `D1-P2-TRIP-LOGIC` | `P2_MASW`, `P2_OnOff`, `P2_Emerg`, `P2_TripEx` | The dominant invariant is explicit engineering, discrete-state or protection logic; a learned model is not required for the basic check. | medium |
| `P2_AutoSD` | P2 | Automatic speed demand. | setpoint/demand | Active-mode SP–controller-output–RPM consistency and normal ramp/settling behavior. | D1 `D1-P2-ENG-RANGE`, D5 `D5-P2-SPEED-LOOP`, D4 `D4-P2-SPEED-DYNAMICS`, D5 `D5-X-P2-P4-SYNC` | `P2_MASW`, `P2_SCO`, `P2_SIT01`, `P4_ST_FD` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P2_ManualSD` | P2 | Manual speed demand. | setpoint/demand | When manual mode is active, speed demand must be consistent with controller/RPM evolution. | D1 `D1-P2-ENG-RANGE`, D5 `D5-P2-SPEED-LOOP`, D4 `D4-P2-SPEED-DYNAMICS` | `P2_MASW`, `P2_SCO`, `P2_SIT01` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P2_RTR` | P2 | RPM trip threshold. | protection threshold | Trip logic must respond consistently to SIT01 relative to RTR. | D1 `D1-P2-ENG-RANGE`, D1 `D1-P2-TRIP-LOGIC` | `P2_SIT01`, `P2_Emerg`, `P2_TripEx` | The dominant invariant is explicit engineering, discrete-state or protection logic; a learned model is not required for the basic check. | high |
| `P2_SCO` | P2 | Speed-controller output. | control output | Controller output must be consistent with active speed demand, RPM and temporal control response. | D1 `D1-P2-ENG-RANGE`, D5 `D5-P2-SPEED-LOOP`, D4 `D4-P2-SPEED-DYNAMICS`, D5 `D5-X-P2-P4-SYNC` | `P2_AutoSD`, `P2_ManualSD`, `P2_SIT01` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P2_SCST` | P2 | Speed change proportional to STM frequency change. | derived coupling signal | Must remain causally consistent with STM frequency and rotor-speed evolution. | D1 `D1-P2-ENG-RANGE`, D5 `D5-P2-SPEED-LOOP`, D5 `D5-X-P2-P4-SYNC` | `P4_ST_FD`, `P2_SIT01` | The tag is meaningful mainly through an engineering/causal relationship with other process variables; an isolated univariate detector would lose that invariant. | high |
| `P2_SIT01` | P2 | Current turbine RPM measured by speed probe. | process variable | SP–PV–CO consistency, normal run-up dynamics, trip-threshold logic and speed-dependent vibration configuration. | D1 `D1-P2-ENG-RANGE`, D1 `D1-P2-TRIP-LOGIC`, D5 `D5-P2-SPEED-LOOP`, D4 `D4-P2-SPEED-DYNAMICS`, D3 `D3-P2-VIB-CONFIG`, D5 `D5-X-P2-P4-SYNC` | `P2_AutoSD`, `P2_ManualSD`, `P2_SCO`, `P2_RTR`, `P2_VIBTR01`, `P4_ST_FD` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P2_VIBTR01` | P2 | Shaft-vibration displacement channel 1. | process variable / vibration sensor | Speed-conditioned multichannel vibration configuration plus explicit protection-threshold relationship. | D1 `D1-P2-ENG-RANGE`, D1 `D1-P2-TRIP-LOGIC`, D3 `D3-P2-VIB-CONFIG` | `P2_SIT01`, `P2_VTR01`, `P2_VT01` | Use hard domain rules for impossible values and a configuration detector for valid-but-incompatible simultaneous settings. | high |
| `P2_VIBTR02` | P2 | Shaft-vibration displacement channel 2. | process variable / vibration sensor | Speed-conditioned multichannel vibration configuration plus explicit protection-threshold relationship. | D1 `D1-P2-ENG-RANGE`, D1 `D1-P2-TRIP-LOGIC`, D3 `D3-P2-VIB-CONFIG` | `P2_SIT01`, `P2_VTR02`, `P2_VT01` | Use hard domain rules for impossible values and a configuration detector for valid-but-incompatible simultaneous settings. | high |
| `P2_VIBTR03` | P2 | Shaft-vibration displacement channel 3. | process variable / vibration sensor | Speed-conditioned multichannel vibration configuration plus explicit protection-threshold relationship. | D1 `D1-P2-ENG-RANGE`, D1 `D1-P2-TRIP-LOGIC`, D3 `D3-P2-VIB-CONFIG` | `P2_SIT01`, `P2_VTR03`, `P2_VT01` | Use hard domain rules for impossible values and a configuration detector for valid-but-incompatible simultaneous settings. | high |
| `P2_VIBTR04` | P2 | Shaft-vibration displacement channel 4. | process variable / vibration sensor | Speed-conditioned multichannel vibration configuration plus explicit protection-threshold relationship. | D1 `D1-P2-ENG-RANGE`, D1 `D1-P2-TRIP-LOGIC`, D3 `D3-P2-VIB-CONFIG` | `P2_SIT01`, `P2_VTR04`, `P2_VT01` | Use hard domain rules for impossible values and a configuration detector for valid-but-incompatible simultaneous settings. | high |
| `P2_VT01` | P2 | Key-phasor probe phase-lag signal. | process variable / phase reference | Must remain compatible with rotor speed and multichannel shaft-vibration regime. | D1 `D1-P2-ENG-RANGE`, D3 `D3-P2-VIB-CONFIG` | `P2_SIT01`, `P2_VIBTR01`, `P2_VIBTR02`, `P2_VIBTR03`, `P2_VIBTR04` | Use hard domain rules for impossible values and a configuration detector for valid-but-incompatible simultaneous settings. | medium |
| `P2_VTR01` | P2 | Preset vibration limit for vibration channel 1. | protection threshold | Protection-state logic must be consistent with the corresponding vibration measurement relative to its threshold. | D1 `D1-P2-ENG-RANGE`, D1 `D1-P2-TRIP-LOGIC` | `P2_VIBTR01`, `P2_Emerg`, `P2_TripEx` | The dominant invariant is explicit engineering, discrete-state or protection logic; a learned model is not required for the basic check. | high |
| `P2_VTR02` | P2 | Preset vibration limit for vibration channel 2. | protection threshold | Protection-state logic must be consistent with the corresponding vibration measurement relative to its threshold. | D1 `D1-P2-ENG-RANGE`, D1 `D1-P2-TRIP-LOGIC` | `P2_VIBTR02`, `P2_Emerg`, `P2_TripEx` | The dominant invariant is explicit engineering, discrete-state or protection logic; a learned model is not required for the basic check. | high |
| `P2_VTR03` | P2 | Preset vibration limit for vibration channel 3. | protection threshold | Protection-state logic must be consistent with the corresponding vibration measurement relative to its threshold. | D1 `D1-P2-ENG-RANGE`, D1 `D1-P2-TRIP-LOGIC` | `P2_VIBTR03`, `P2_Emerg`, `P2_TripEx` | The dominant invariant is explicit engineering, discrete-state or protection logic; a learned model is not required for the basic check. | high |
| `P2_VTR04` | P2 | Preset vibration limit for vibration channel 4. | protection threshold | Protection-state logic must be consistent with the corresponding vibration measurement relative to its threshold. | D1 `D1-P2-ENG-RANGE`, D1 `D1-P2-TRIP-LOGIC` | `P2_VIBTR04`, `P2_Emerg`, `P2_TripEx` | The dominant invariant is explicit engineering, discrete-state or protection logic; a learned model is not required for the basic check. | high |
| `P3_FIT01` | P3 | Flow rate into the upper water tank (raw/unspecified engineering scaling). | process variable | Hydraulic relationship with pump/valve command and reservoir-level dynamics. | D1 `D1-P3-ENG-RANGE`, D4 `D4-P3-LEVEL-DYNAMICS`, D5 `D5-P3-HYDRAULIC-CONSISTENCY`, D5 `D5-X-P3-P4-HYDRO` | `P3_LCP01D`, `P3_LCV01D`, `P3_PIT01`, `P3_LIT01` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | medium |
| `P3_LCP01D` | P3 | Pump LCP01 speed command. | analog actuator command | Command must be compatible with level thresholds/HIL demand and resulting flow/pressure/level response. | D1 `D1-P3-ENG-RANGE`, D5 `D5-P3-LEVEL-CONTROL`, D4 `D4-P3-LEVEL-DYNAMICS`, D5 `D5-P3-HYDRAULIC-CONSISTENCY`, D5 `D5-X-P3-P4-HYDRO` | `P3_LIT01`, `P3_FIT01`, `P3_PIT01`, `P4_HT_PS` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P3_LCV01D` | P3 | Valve LCV01 position command. | analog actuator command | Command must be compatible with level thresholds/HIL demand and resulting hydraulic response. | D1 `D1-P3-ENG-RANGE`, D5 `D5-P3-LEVEL-CONTROL`, D4 `D4-P3-LEVEL-DYNAMICS`, D5 `D5-P3-HYDRAULIC-CONSISTENCY`, D5 `D5-X-P3-P4-HYDRO` | `P3_LIT01`, `P3_FIT01`, `P3_PIT01`, `P4_HT_PS` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P3_LH01` | P3 | High water-level setpoint. | setpoint/protection threshold | High threshold must be correctly ordered relative to LL01 and interpreted consistently with level-control state. | D1 `D1-P3-ENG-RANGE`, D1 `D1-P3-LEVEL-LIMITS`, D5 `D5-P3-LEVEL-CONTROL` | `P3_LL01`, `P3_LIT01` | The tag is meaningful mainly through an engineering/causal relationship with other process variables; an isolated univariate detector would lose that invariant. | high |
| `P3_LIT01` | P3 | Upper-water-tank level. | process variable | Threshold, pump/valve, flow and temporal tank-balance consistency. | D1 `D1-P3-ENG-RANGE`, D1 `D1-P3-LEVEL-LIMITS`, D5 `D5-P3-LEVEL-CONTROL`, D4 `D4-P3-LEVEL-DYNAMICS`, D5 `D5-P3-HYDRAULIC-CONSISTENCY`, D5 `D5-X-P3-P4-HYDRO` | `P3_LH01`, `P3_LL01`, `P3_LCP01D`, `P3_LCV01D`, `P3_FIT01` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P3_LL01` | P3 | Low water-level setpoint. | setpoint/protection threshold | Low threshold must be correctly ordered relative to LH01 and interpreted consistently with level-control state. | D1 `D1-P3-ENG-RANGE`, D1 `D1-P3-LEVEL-LIMITS`, D5 `D5-P3-LEVEL-CONTROL` | `P3_LH01`, `P3_LIT01` | The tag is meaningful mainly through an engineering/causal relationship with other process variables; an isolated univariate detector would lose that invariant. | high |
| `P3_PIT01` | P3 | Upper-water-tank inlet pressure (raw/unspecified engineering scaling). | process variable | Pressure must be hydraulically consistent with pump/valve commands, inflow and level. | D1 `D1-P3-ENG-RANGE`, D5 `D5-P3-HYDRAULIC-CONSISTENCY`, D5 `D5-X-P3-P4-HYDRO` | `P3_LCP01D`, `P3_LCV01D`, `P3_FIT01`, `P3_LIT01` | The tag is meaningful mainly through an engineering/causal relationship with other process variables; an isolated univariate detector would lose that invariant. | medium |
| `P4_HT_FD` | P4 | Hydropower-turbine-model frequency deviation. | process variable | Hydropower power/load relation and temporal response; cross-zone hydraulic consistency. | D1 `D1-P4-ENG-RANGE`, D5 `D5-P4-HT-CONSISTENCY`, D4 `D4-P4-HT-DYNAMICS`, D5 `D5-X-P3-P4-HYDRO` | `P4_HT_PS`, `P4_HT_LD`, `P4_HT_PO`, `P3_LCP01D` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P4_HT_LD` | P4 | Hydropower-model electrical load demand. | demand | Joint consistency with schedule, output power and frequency deviation. | D1 `D1-P4-ENG-RANGE`, D5 `D5-P4-HT-CONSISTENCY`, D4 `D4-P4-HT-DYNAMICS`, D5 `D5-P4-LOAD-BALANCE`, D5 `D5-X-P3-P4-HYDRO` | `P4_HT_PS`, `P4_HT_PO`, `P4_HT_FD`, `P4_LD` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P4_HT_PO` | P4 | Hydropower-model output power. | process output | Must be compatible with schedule/load/frequency and P3 hydraulic response. | D1 `D1-P4-ENG-RANGE`, D5 `D5-P4-HT-CONSISTENCY`, D4 `D4-P4-HT-DYNAMICS`, D5 `D5-P4-LOAD-BALANCE`, D5 `D5-X-P3-P4-HYDRO` | `P4_HT_PS`, `P4_HT_LD`, `P4_HT_FD`, `P3_LCP01D` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P4_HT_PS` | P4 | Hydropower scheduled power demand. | setpoint/schedule | Schedule changes should cause valid hydropower/P3 configurations and temporal response. | D1 `D1-P4-ENG-RANGE`, D5 `D5-P4-HT-CONSISTENCY`, D4 `D4-P4-HT-DYNAMICS`, D5 `D5-P4-LOAD-BALANCE`, D5 `D5-P3-LEVEL-CONTROL`, D5 `D5-X-P3-P4-HYDRO` | `P4_HT_LD`, `P4_HT_PO`, `P4_HT_FD`, `P3_LCP01D`, `P3_LCV01D` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P4_LD` | P4 | Total electrical load demand. | system demand | Must occupy a valid joint configuration with steam and hydro load/output variables; exact balance equation requires model documentation. | D1 `D1-P4-ENG-RANGE`, D5 `D5-P4-LOAD-BALANCE` | `P4_ST_LD`, `P4_ST_PO`, `P4_HT_LD`, `P4_HT_PO` | The tag is meaningful mainly through an engineering/causal relationship with other process variables; an isolated univariate detector would lose that invariant. | medium |
| `P4_ST_FD` | P4 | Steam-turbine-model frequency deviation. | process variable | Steam-model power/governor consistency and synchronization with P2 rotor speed. | D1 `D1-P4-ENG-RANGE`, D5 `D5-P4-ST-CONSISTENCY`, D4 `D4-P4-ST-DYNAMICS`, D5 `D5-X-P2-P4-SYNC` | `P4_ST_PS`, `P4_ST_PO`, `P4_ST_GOV`, `P2_SCST`, `P2_SIT01` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P4_ST_GOV` | P4 | Steam-turbine-model governor/gate opening value. | control output / simulated actuator | Governor action must be consistent with steam-model power/frequency response and P2 synchronization. | D1 `D1-P4-ENG-RANGE`, D5 `D5-P4-ST-CONSISTENCY`, D4 `D4-P4-ST-DYNAMICS`, D5 `D5-X-P2-P4-SYNC` | `P4_ST_FD`, `P4_ST_PO`, `P4_ST_PS`, `P2_SIT01` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P4_ST_LD` | P4 | Steam-turbine-model electrical load demand. | demand | Joint consistency with schedule, output power, frequency and total-load configuration. | D1 `D1-P4-ENG-RANGE`, D5 `D5-P4-ST-CONSISTENCY`, D4 `D4-P4-ST-DYNAMICS`, D5 `D5-P4-LOAD-BALANCE` | `P4_ST_PS`, `P4_ST_PO`, `P4_ST_FD`, `P4_LD` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P4_ST_PO` | P4 | Steam-turbine-model output power. | process output | Power must be compatible with schedule/load/frequency/governor and cross-zone steam/rotor state. | D1 `D1-P4-ENG-RANGE`, D5 `D5-P4-ST-CONSISTENCY`, D4 `D4-P4-ST-DYNAMICS`, D5 `D5-P4-LOAD-BALANCE`, D5 `D5-X-P1-P4-STEAM`, D5 `D5-X-P2-P4-SYNC` | `P4_ST_PS`, `P4_ST_LD`, `P4_ST_FD`, `P4_ST_GOV`, `P2_SIT01` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P4_ST_PS` | P4 | Steam-turbine scheduled power demand. | setpoint/schedule | Schedule changes should drive valid steam-model power/governor/frequency dynamics. | D1 `D1-P4-ENG-RANGE`, D5 `D5-P4-ST-CONSISTENCY`, D4 `D4-P4-ST-DYNAMICS`, D5 `D5-P4-LOAD-BALANCE` | `P4_ST_LD`, `P4_ST_PO`, `P4_ST_FD`, `P4_ST_GOV` | Use process/causal consistency for the primary invariant, with temporal monitoring where the physical response has inertia or sequencing. | high |
| `P4_ST_PT01` | P4 | Digital steam-pressure value of STM. | simulated process variable | Must be consistent with boiler pressure/thermal state and STM output behavior. | D1 `D1-P4-ENG-RANGE`, D5 `D5-P4-ST-CONSISTENCY`, D5 `D5-X-P1-P4-STEAM` | `P1_PIT01`, `P4_ST_TT01`, `P4_ST_PO` | The tag is meaningful mainly through an engineering/causal relationship with other process variables; an isolated univariate detector would lose that invariant. | medium |
| `P4_ST_TT01` | P4 | Digital steam-temperature value of STM. | simulated process variable | Must be consistent with boiler temperature/flow state and STM output behavior. | D1 `D1-P4-ENG-RANGE`, D5 `D5-P4-ST-CONSISTENCY`, D5 `D5-X-P1-P4-STEAM` | `P1_TIT01`, `P1_TIT02`, `P4_ST_PT01`, `P4_ST_PO` | The tag is meaningful mainly through an engineering/causal relationship with other process variables; an isolated univariate detector would lose that invariant. | medium |

# B. Functional detector groups

| detector_id | class | Functional purpose | input_variables | Scope | Monitored invariant | Training / calibration requirement | Related detector groups |
|---|---|---|---|---|---|---|---|
| `D1-P1-ENG-RANGE` | D1 | Engineering-domain and discrete-domain validation for boiler-process tags. | `P1_B2004`, `P1_B2016`, `P1_B3004`, `P1_B3005`, `P1_B4002`, `P1_B4005`, `P1_B400B`, `P1_B4022`, `P1_FCV01D`, `P1_FCV01Z`, `P1_FCV02D`, `P1_FCV02Z`, `P1_FCV03D`, `P1_FCV03Z`, `P1_FT01`, `P1_FT01Z`, `P1_FT02`, `P1_FT02Z`, `P1_FT03`, `P1_FT03Z`, `P1_LCV01D`, `P1_LCV01Z`, `P1_LIT01`, `P1_PCV01D`, `P1_PCV01Z`, `P1_PCV02D`, `P1_PCV02Z`, `P1_PIT01`, `P1_PIT01_HH`, `P1_PIT02`, `P1_PP01AD`, `P1_PP01AR`, `P1_PP01BD`, `P1_PP01BR`, `P1_PP02D`, `P1_PP02R`, `P1_PP04`, `P1_PP04SP`, `P1_SOL01D`, `P1_SOL03D`, `P1_STSP`, `P1_TIT01`, `P1_TIT02`, `P1_TIT03` | P1 boiler | Published engineering/representation ranges and Boolean domains must not be violated. | none | — |
| `D1-P1-PUMP-STATE` | D1 | Validate pump command/running-state logic for PP01A, PP01B and PP02. | `P1_PP01AD`, `P1_PP01AR`, `P1_PP01BD`, `P1_PP01BR`, `P1_PP02D`, `P1_PP02R` | P1 pumps | Pump run feedback must be logically compatible with start commands, allowing an engineering-defined start/stop delay. | none | — |
| `D1-P1-PLANT-STATE` | D1 | Validate boiler DCS and discrete supply/drain valve operating states. | `P1_STSP`, `P1_SOL01D`, `P1_SOL03D` | P1 boiler discrete-state logic | Only valid Boolean states and expert-approved combinations/transitions are allowed. | none | `P1 loop detectors` |
| `D3-P1-PC-CONFIG` | D3 | Check compatibility of the two documented pressure-reference tags and active pressure-control configuration. | `P1_B2004`, `P1_B2016`, `P1_PIT01`, `P1_STSP` | P1 pressure-control configuration | The simultaneous configuration of pressure references, measured pressure and plant state must match a valid operating mode. | normal-data-training | — |
| `D5-P1-ACTUATOR-TRACK` | D5 | Check analog valve command-to-position consistency. | `P1_FCV01D`, `P1_FCV01Z`, `P1_FCV02D`, `P1_FCV02Z`, `P1_FCV03D`, `P1_FCV03Z`, `P1_LCV01D`, `P1_LCV01Z`, `P1_PCV01D`, `P1_PCV01Z`, `P1_PCV02D`, `P1_PCV02Z` | P1 analog valves | Measured/current valve position should track the corresponding position command within actuator lag and tolerance. | relationship-learning | `P1 loop detectors` |
| `D5-P1-FLOW-CONVERSION` | D5 | Validate raw/transformed flow-signal conversion pairs. | `P1_FT01`, `P1_FT01Z`, `P1_FT02`, `P1_FT02Z`, `P1_FT03`, `P1_FT03Z` | P1 flow instrumentation | Each Z flow value must remain consistent with the documented conversion of its paired raw FT signal. | relationship-learning | — |
| `D5-P1-PC-LOOP` | D5 | Monitor pressure-control loop consistency. | `P1_B2016`, `P1_PIT01`, `P1_PCV01D`, `P1_PCV02D`, `P1_PCV01Z`, `P1_PCV02Z`, `P1_PP01AD`, `P1_PP01AR`, `P1_PP01BD`, `P1_PP01BR` | P1-PC | Pressure error, pressure-valve commands/positions and pump availability must exhibit a physically and functionally consistent control response. | relationship-learning | `D5-X-P1-P4-STEAM` |
| `D4-P1-PC-DYNAMICS` | D4 | Monitor pressure-loop transient evolution after reference or actuator changes. | `P1_B2016`, `P1_PIT01`, `P1_PCV01D`, `P1_PCV02D` | P1-PC | Pressure response must have normal delay, rate, settling and temporal dependence for the pressure loop. | normal-data-training | — |
| `D5-P1-LC-LOOP` | D5 | Monitor return-water-tank level-control consistency including documented feed-forward coupling. | `P1_B3004`, `P1_LIT01`, `P1_LCV01D`, `P1_LCV01Z`, `P1_FCV03D`, `P1_FT03`, `P1_FT03Z` | P1-LC | Level error, LCV action and the FCV03/outflow disturbance must remain mutually consistent. | relationship-learning | `D5-P1-FC-LOOP` |
| `D4-P1-LC-DYNAMICS` | D4 | Monitor tank-level inertia and response to inflow/outflow actuator changes. | `P1_B3004`, `P1_LIT01`, `P1_LCV01D`, `P1_FCV03D`, `P1_FT03Z` | P1-LC | Tank level must evolve with physically plausible delay and slope under valve/flow changes. | normal-data-training | — |
| `D5-P1-FC-LOOP` | D5 | Monitor return-water-tank discharge flow control. | `P1_B3005`, `P1_FT03`, `P1_FT03Z`, `P1_FCV03D`, `P1_FCV03Z` | P1-FC | Discharge-flow error and FCV03 command/position must be functionally consistent. | relationship-learning | `D5-P1-LC-LOOP` |
| `D3-P1-TC-CONFIG` | D3 | Validate the documented temperature/thermal-demand configuration without assuming an undocumented hierarchy. | `P1_B4002`, `P1_B4005`, `P1_B400B`, `P1_B4022`, `P1_TIT01`, `P1_FT02Z` | P1 thermal/temperature-control configuration | Temperature references/demands, PID output, heating-water flow and measured temperature must form a valid operating configuration. | normal-data-training | — |
| `D5-P1-TC-LOOP` | D5 | Monitor temperature-control cascade/feed-forward consistency. | `P1_B4002`, `P1_B4022`, `P1_B4005`, `P1_TIT01`, `P1_FCV01D`, `P1_FCV01Z`, `P1_FCV02D`, `P1_FCV02Z`, `P1_FT02`, `P1_FT02Z`, `P1_TIT02` | P1-TC | Temperature demand/error, cascade output, heating-water flow and FCV01/FCV02 actions must be causally consistent. | relationship-learning | `D5-X-P1-P4-STEAM` |
| `D4-P1-TC-DYNAMICS` | D4 | Monitor thermal inertia and cascade-control temporal response. | `P1_B4002`, `P1_B4022`, `P1_TIT01`, `P1_FCV01D`, `P1_FCV02D`, `P1_FT02Z`, `P1_TIT02` | P1-TC | Temperature must evolve with normal thermal lag and rate following reference, flow and valve changes. | normal-data-training | — |
| `D5-P1-CC-LOOP` | D5 | Monitor cooling-pump control consistency. | `P1_PP04SP`, `P1_PP04`, `P1_TIT03` | P1-CC | Cooling-pump output must be consistent with main-tank temperature and cooler setpoint/activation logic. | relationship-learning | `D5-P1-THERMAL-CONSISTENCY` |
| `D4-P1-CC-DYNAMICS` | D4 | Monitor main-tank temperature response to cooling-pump actuation. | `P1_PP04SP`, `P1_PP04`, `P1_TIT03` | P1-CC | Cooling activation and temperature response must exhibit plausible delay, direction and rate. | normal-data-training | — |
| `D5-P1-MASS-BALANCE` | D5 | Monitor hydraulic mass-balance consistency around the return-water tank. | `P1_FT01Z`, `P1_FT03Z`, `P1_LIT01`, `P1_LCV01D`, `P1_FCV03D`, `P1_SOL01D`, `P1_SOL03D` | P1 return-water hydraulic subsystem | Net inflow/outflow and valve states must be consistent with the direction and magnitude of level change. | relationship-learning | — |
| `D5-P1-THERMAL-CONSISTENCY` | D5 | Monitor cross-signal thermal consistency inside the boiler/heat-transfer process. | `P1_B400B`, `P1_FT02Z`, `P1_TIT01`, `P1_TIT02`, `P1_TIT03`, `P1_FCV01D`, `P1_FCV02D`, `P1_PP04` | P1 heat-transfer subsystem | Heating-water flow, valve action, temperatures and cooling action must remain physically coherent. | relationship-learning | `D5-P1-CC-LOOP` |
| `D2-P1-PIT02-STABILITY` | D2 | Monitor the heating-water pump supply pressure as a stable process-health signal conditional on pump state. | `P1_PIT02`, `P1_PP02D`, `P1_PP02R` | P1 heating-water pump | Within a given pump state, supply pressure should remain within its calibrated statistical operating envelope and not drift abruptly. | calibration | — |
| `D5-P1-PIT01HH-CONSISTENCY` | D5 | Validate the documented 'highest outlet pressure' signal against outlet pressure. | `P1_PIT01`, `P1_PIT01_HH` | P1 pressure instrumentation | The high/highest pressure representation must be consistent with PIT01 under its actual aggregation/monitor semantics. | relationship-learning | — |
| `D1-P2-ENG-RANGE` | D1 | Engineering-domain and discrete-domain validation for turbine-process tags. | `P2_24Vdc`, `P2_ATSW_Lamp`, `P2_AutoGo`, `P2_Emerg`, `P2_MASW`, `P2_MASW_Lamp`, `P2_ManualGO`, `P2_OnOff`, `P2_TripEx`, `P2_AutoSD`, `P2_ManualSD`, `P2_RTR`, `P2_SCO`, `P2_SCST`, `P2_SIT01`, `P2_VIBTR01`, `P2_VIBTR02`, `P2_VIBTR03`, `P2_VIBTR04`, `P2_VT01`, `P2_VTR01`, `P2_VTR02`, `P2_VTR03`, `P2_VTR04` | P2 turbine | Published engineering/representation ranges and Boolean domains must not be violated. | none | — |
| `D1-P2-MODE-LOGIC` | D1 | Validate manual/auto, start, on/off and lamp state logic. | `P2_ATSW_Lamp`, `P2_AutoGo`, `P2_MASW`, `P2_MASW_Lamp`, `P2_ManualGO`, `P2_OnOff`, `P2_Emerg`, `P2_TripEx` | P2 operating-mode logic | Mode selector, mode lamps, start controls, on/off state and trip-exit state must follow allowed combinations/transitions. | none | `D5-P2-SPEED-LOOP` |
| `D1-P2-TRIP-LOGIC` | D1 | Monitor overspeed/over-vibration protection consistency. | `P2_SIT01`, `P2_RTR`, `P2_VIBTR01`, `P2_VIBTR02`, `P2_VIBTR03`, `P2_VIBTR04`, `P2_VTR01`, `P2_VTR02`, `P2_VTR03`, `P2_VTR04`, `P2_Emerg`, `P2_TripEx`, `P2_OnOff` | P2 turbine trip protection | Speed/vibration threshold comparisons and emergency/trip state must satisfy the documented protection logic. | none | `D5-P2-SPEED-LOOP` |
| `D2-P2-24V-STABILITY` | D2 | Monitor DCS 24-V supply stability. | `P2_24Vdc` | P2 DCS power supply | Supply voltage should remain statistically stable around its normal operating level and avoid abrupt or drifting departures. | calibration | — |
| `D5-P2-SPEED-LOOP` | D5 | Monitor mode-dependent turbine speed-control consistency. | `P2_AutoSD`, `P2_ManualSD`, `P2_MASW`, `P2_AutoGo`, `P2_ManualGO`, `P2_OnOff`, `P2_SCO`, `P2_SIT01`, `P2_SCST` | P2-SC | The active speed demand, controller output and measured RPM must be mutually consistent in the selected operating mode. | relationship-learning | `D1-P2-MODE-LOGIC`, `D1-P2-TRIP-LOGIC` |
| `D4-P2-SPEED-DYNAMICS` | D4 | Monitor turbine run-up, engagement and speed-control temporal evolution. | `P2_AutoSD`, `P2_ManualSD`, `P2_MASW`, `P2_SCO`, `P2_SIT01`, `P2_OnOff` | P2-SC | RPM should ramp, engage and settle with the normal sequence, rate, delay and inertia rather than jump independently. | normal-data-training | — |
| `D3-P2-VIB-CONFIG` | D3 | Monitor the multivariate rotor vibration configuration conditional on speed. | `P2_SIT01`, `P2_VIBTR01`, `P2_VIBTR02`, `P2_VIBTR03`, `P2_VIBTR04`, `P2_VT01` | P2 rotor/shaft monitoring | The four orthogonal shaft-vibration channels and key-phasor signal must form a physically plausible configuration for the current speed regime. | normal-data-training | — |
| `D1-P3-ENG-RANGE` | D1 | Engineering-domain validation for water-treatment tags, including 0..27648 raw channels. | `P3_FIT01`, `P3_LCP01D`, `P3_LCV01D`, `P3_LH01`, `P3_LIT01`, `P3_LL01`, `P3_PIT01` | P3 water treatment | Published engineering/representation ranges must not be violated. | none | — |
| `D1-P3-LEVEL-LIMITS` | D1 | Validate high/low level setpoint ordering and level-state constraints. | `P3_LH01`, `P3_LL01`, `P3_LIT01` | P3-LC | Low/high level references must have a valid ordering and the measured level must be interpreted consistently with them and any hysteresis. | none | — |
| `D5-P3-LEVEL-CONTROL` | D5 | Monitor upper-reservoir level-control consistency. | `P3_LH01`, `P3_LL01`, `P3_LIT01`, `P3_LCP01D`, `P3_LCV01D`, `P4_HT_PS`, `P4_HT_LD`, `P4_HT_PO`, `P4_HT_FD` | P3-LC with P4-HTM demand | Pump/valve demands produced from the HIL hydropower module must be consistent with level thresholds, measured level and hydropower operating state. | relationship-learning | `D5-P4-HT-CONSISTENCY` |
| `D4-P3-LEVEL-DYNAMICS` | D4 | Monitor upper-reservoir level dynamics. | `P3_LIT01`, `P3_LCP01D`, `P3_LCV01D`, `P3_FIT01` | P3-LC | Reservoir level must change with physically plausible delay and slope following pump, valve and inflow changes. | normal-data-training | — |
| `D5-P3-HYDRAULIC-CONSISTENCY` | D5 | Monitor pump/valve/flow/pressure hydraulic consistency. | `P3_FIT01`, `P3_PIT01`, `P3_LCP01D`, `P3_LCV01D`, `P3_LIT01` | P3 hydraulic subsystem | Inlet flow and pressure must be physically consistent with pump command, valve command and reservoir level. | relationship-learning | `D5-X-P3-P4-HYDRO` |
| `D1-P4-ENG-RANGE` | D1 | Engineering-domain validation for HIL power-system tags. | `P4_HT_FD`, `P4_HT_LD`, `P4_HT_PO`, `P4_HT_PS`, `P4_LD`, `P4_ST_FD`, `P4_ST_GOV`, `P4_ST_LD`, `P4_ST_PO`, `P4_ST_PS`, `P4_ST_PT01`, `P4_ST_TT01` | P4 HIL simulation | Published engineering/representation ranges must not be violated. | none | — |
| `D5-P4-ST-CONSISTENCY` | D5 | Monitor steam-turbine model power/governor/process consistency. | `P4_ST_PS`, `P4_ST_LD`, `P4_ST_PO`, `P4_ST_FD`, `P4_ST_GOV`, `P4_ST_PT01`, `P4_ST_TT01` | P4-STM | Scheduled power, load demand, output power, frequency deviation, governor action and steam-state variables must remain causally consistent. | relationship-learning | `D5-P4-LOAD-BALANCE`, `D5-X-P2-P4-SYNC` |
| `D4-P4-ST-DYNAMICS` | D4 | Monitor steam-turbine-model temporal response. | `P4_ST_PS`, `P4_ST_LD`, `P4_ST_PO`, `P4_ST_FD`, `P4_ST_GOV` | P4-STM | Power, governor and frequency response must follow normal delay, ramp and settling behavior after schedule/load changes. | normal-data-training | — |
| `D5-P4-HT-CONSISTENCY` | D5 | Monitor pumped-storage hydropower model consistency. | `P4_HT_PS`, `P4_HT_LD`, `P4_HT_PO`, `P4_HT_FD` | P4-HTM | Scheduled power, load demand, output power and frequency deviation must remain mutually consistent. | relationship-learning | `D5-P3-LEVEL-CONTROL`, `D5-P4-LOAD-BALANCE` |
| `D4-P4-HT-DYNAMICS` | D4 | Monitor hydropower-model temporal response. | `P4_HT_PS`, `P4_HT_LD`, `P4_HT_PO`, `P4_HT_FD` | P4-HTM | Hydropower output/frequency response must follow normal delay, ramp and settling behavior after schedule/load changes. | normal-data-training | — |
| `D5-P4-LOAD-BALANCE` | D5 | Monitor system-level power/load configuration without assuming a closed balance equation not documented for the infinite-bus simulation. | `P4_LD`, `P4_ST_LD`, `P4_ST_PO`, `P4_ST_PS`, `P4_HT_LD`, `P4_HT_PO`, `P4_HT_PS` | P4 system-level power configuration | Total load and the two generation-model demand/output/schedule signals must occupy a valid joint operating configuration. | relationship-learning | `D5-P4-HT-CONSISTENCY`, `D5-P4-ST-CONSISTENCY` |
| `D5-X-P1-P4-STEAM` | D5 | Monitor boiler-to-steam-turbine-model coupling. | `P1_PIT01`, `P1_TIT01`, `P1_TIT02`, `P1_FT02Z`, `P4_ST_PT01`, `P4_ST_TT01`, `P4_ST_PO`, `P4_ST_FD` | P1 ↔ P4-STM | Boiler pressure/temperature/flow state must be consistent with the steam pressure/temperature and resulting steam-model behavior. | relationship-learning | `D5-P1-PC-LOOP`, `D5-P1-TC-LOOP` |
| `D5-X-P2-P4-SYNC` | D5 | Monitor real rotor and virtual steam-turbine synchronization. | `P2_SCST`, `P2_SIT01`, `P2_AutoSD`, `P2_SCO`, `P4_ST_FD`, `P4_ST_GOV`, `P4_ST_PO` | P2 ↔ P4-STM | Rotor-speed change and controller behavior must be consistent with STM frequency/power/governor state. | relationship-learning | `D5-P4-ST-CONSISTENCY` |
| `D5-X-P3-P4-HYDRO` | D5 | Monitor water-treatment and virtual hydropower coupling. | `P3_LCP01D`, `P3_LCV01D`, `P3_FIT01`, `P3_PIT01`, `P3_LIT01`, `P4_HT_PS`, `P4_HT_LD`, `P4_HT_PO`, `P4_HT_FD` | P3 ↔ P4-HTM | Hydropower operating demand/state must be consistent with the pump/valve commands and resulting hydraulic response. | relationship-learning | `D5-P3-HYDRAULIC-CONSISTENCY` |

# C. Routing map

The route below is **variable → detector instance(s)**. A variable is deliberately routed to more than one detector only when it participates in distinct invariants (for example, hard range + control residual + temporal dynamics).

## P1

- `P1_B2004` → `D1-P1-ENG-RANGE`, `D3-P1-PC-CONFIG`
- `P1_B2016` → `D1-P1-ENG-RANGE`, `D3-P1-PC-CONFIG`, `D5-P1-PC-LOOP`, `D4-P1-PC-DYNAMICS`
- `P1_B3004` → `D1-P1-ENG-RANGE`, `D5-P1-LC-LOOP`, `D4-P1-LC-DYNAMICS`
- `P1_B3005` → `D1-P1-ENG-RANGE`, `D5-P1-FC-LOOP`
- `P1_B4002` → `D1-P1-ENG-RANGE`, `D3-P1-TC-CONFIG`, `D5-P1-TC-LOOP`, `D4-P1-TC-DYNAMICS`
- `P1_B4005` → `D1-P1-ENG-RANGE`, `D3-P1-TC-CONFIG`, `D5-P1-TC-LOOP`
- `P1_B400B` → `D1-P1-ENG-RANGE`, `D3-P1-TC-CONFIG`, `D5-P1-THERMAL-CONSISTENCY`
- `P1_B4022` → `D1-P1-ENG-RANGE`, `D3-P1-TC-CONFIG`, `D5-P1-TC-LOOP`, `D4-P1-TC-DYNAMICS`
- `P1_FCV01D` → `D1-P1-ENG-RANGE`, `D5-P1-ACTUATOR-TRACK`, `D5-P1-TC-LOOP`, `D4-P1-TC-DYNAMICS`, `D5-P1-THERMAL-CONSISTENCY`
- `P1_FCV01Z` → `D1-P1-ENG-RANGE`, `D5-P1-ACTUATOR-TRACK`, `D5-P1-TC-LOOP`
- `P1_FCV02D` → `D1-P1-ENG-RANGE`, `D5-P1-ACTUATOR-TRACK`, `D5-P1-TC-LOOP`, `D4-P1-TC-DYNAMICS`, `D5-P1-THERMAL-CONSISTENCY`
- `P1_FCV02Z` → `D1-P1-ENG-RANGE`, `D5-P1-ACTUATOR-TRACK`, `D5-P1-TC-LOOP`
- `P1_FCV03D` → `D1-P1-ENG-RANGE`, `D5-P1-ACTUATOR-TRACK`, `D5-P1-FC-LOOP`, `D5-P1-LC-LOOP`, `D4-P1-LC-DYNAMICS`, `D5-P1-MASS-BALANCE`
- `P1_FCV03Z` → `D1-P1-ENG-RANGE`, `D5-P1-ACTUATOR-TRACK`, `D5-P1-FC-LOOP`
- `P1_FT01` → `D1-P1-ENG-RANGE`, `D5-P1-FLOW-CONVERSION`, `D5-P1-MASS-BALANCE`
- `P1_FT01Z` → `D1-P1-ENG-RANGE`, `D5-P1-FLOW-CONVERSION`, `D5-P1-MASS-BALANCE`
- `P1_FT02` → `D1-P1-ENG-RANGE`, `D5-P1-FLOW-CONVERSION`, `D5-P1-TC-LOOP`, `D4-P1-TC-DYNAMICS`, `D5-P1-THERMAL-CONSISTENCY`, `D5-X-P1-P4-STEAM`
- `P1_FT02Z` → `D1-P1-ENG-RANGE`, `D5-P1-FLOW-CONVERSION`, `D5-P1-TC-LOOP`, `D4-P1-TC-DYNAMICS`, `D5-P1-THERMAL-CONSISTENCY`, `D5-X-P1-P4-STEAM`
- `P1_FT03` → `D1-P1-ENG-RANGE`, `D5-P1-FLOW-CONVERSION`, `D5-P1-FC-LOOP`, `D5-P1-LC-LOOP`, `D4-P1-LC-DYNAMICS`, `D5-P1-MASS-BALANCE`
- `P1_FT03Z` → `D1-P1-ENG-RANGE`, `D5-P1-FLOW-CONVERSION`, `D5-P1-FC-LOOP`, `D5-P1-LC-LOOP`, `D4-P1-LC-DYNAMICS`, `D5-P1-MASS-BALANCE`
- `P1_LCV01D` → `D1-P1-ENG-RANGE`, `D5-P1-ACTUATOR-TRACK`, `D5-P1-LC-LOOP`, `D4-P1-LC-DYNAMICS`, `D5-P1-MASS-BALANCE`
- `P1_LCV01Z` → `D1-P1-ENG-RANGE`, `D5-P1-ACTUATOR-TRACK`, `D5-P1-LC-LOOP`
- `P1_LIT01` → `D1-P1-ENG-RANGE`, `D5-P1-LC-LOOP`, `D4-P1-LC-DYNAMICS`, `D5-P1-MASS-BALANCE`
- `P1_PCV01D` → `D1-P1-ENG-RANGE`, `D5-P1-ACTUATOR-TRACK`, `D5-P1-PC-LOOP`, `D4-P1-PC-DYNAMICS`
- `P1_PCV01Z` → `D1-P1-ENG-RANGE`, `D5-P1-ACTUATOR-TRACK`, `D5-P1-PC-LOOP`
- `P1_PCV02D` → `D1-P1-ENG-RANGE`, `D5-P1-ACTUATOR-TRACK`, `D5-P1-PC-LOOP`, `D4-P1-PC-DYNAMICS`
- `P1_PCV02Z` → `D1-P1-ENG-RANGE`, `D5-P1-ACTUATOR-TRACK`, `D5-P1-PC-LOOP`
- `P1_PIT01` → `D1-P1-ENG-RANGE`, `D3-P1-PC-CONFIG`, `D5-P1-PC-LOOP`, `D4-P1-PC-DYNAMICS`, `D5-P1-PIT01HH-CONSISTENCY`, `D5-X-P1-P4-STEAM`
- `P1_PIT01_HH` → `D1-P1-ENG-RANGE`, `D5-P1-PIT01HH-CONSISTENCY`
- `P1_PIT02` → `D1-P1-ENG-RANGE`, `D2-P1-PIT02-STABILITY`
- `P1_PP01AD` → `D1-P1-ENG-RANGE`, `D1-P1-PUMP-STATE`
- `P1_PP01AR` → `D1-P1-ENG-RANGE`, `D1-P1-PUMP-STATE`
- `P1_PP01BD` → `D1-P1-ENG-RANGE`, `D1-P1-PUMP-STATE`
- `P1_PP01BR` → `D1-P1-ENG-RANGE`, `D1-P1-PUMP-STATE`
- `P1_PP02D` → `D1-P1-ENG-RANGE`, `D1-P1-PUMP-STATE`, `D2-P1-PIT02-STABILITY`
- `P1_PP02R` → `D1-P1-ENG-RANGE`, `D1-P1-PUMP-STATE`, `D2-P1-PIT02-STABILITY`
- `P1_PP04` → `D1-P1-ENG-RANGE`, `D5-P1-CC-LOOP`, `D4-P1-CC-DYNAMICS`, `D5-P1-THERMAL-CONSISTENCY`
- `P1_PP04SP` → `D1-P1-ENG-RANGE`, `D5-P1-CC-LOOP`, `D4-P1-CC-DYNAMICS`
- `P1_SOL01D` → `D1-P1-ENG-RANGE`, `D1-P1-PLANT-STATE`, `D5-P1-MASS-BALANCE`
- `P1_SOL03D` → `D1-P1-ENG-RANGE`, `D1-P1-PLANT-STATE`, `D5-P1-MASS-BALANCE`
- `P1_STSP` → `D1-P1-ENG-RANGE`, `D1-P1-PLANT-STATE`, `D3-P1-PC-CONFIG`
- `P1_TIT01` → `D1-P1-ENG-RANGE`, `D3-P1-TC-CONFIG`, `D5-P1-TC-LOOP`, `D4-P1-TC-DYNAMICS`, `D5-P1-THERMAL-CONSISTENCY`, `D5-X-P1-P4-STEAM`
- `P1_TIT02` → `D1-P1-ENG-RANGE`, `D5-P1-TC-LOOP`, `D4-P1-TC-DYNAMICS`, `D5-P1-THERMAL-CONSISTENCY`, `D5-X-P1-P4-STEAM`
- `P1_TIT03` → `D1-P1-ENG-RANGE`, `D5-P1-CC-LOOP`, `D4-P1-CC-DYNAMICS`, `D5-P1-THERMAL-CONSISTENCY`

## P2

- `P2_24Vdc` → `D1-P2-ENG-RANGE`, `D2-P2-24V-STABILITY`
- `P2_ATSW_Lamp` → `D1-P2-ENG-RANGE`, `D1-P2-MODE-LOGIC`
- `P2_AutoGo` → `D1-P2-ENG-RANGE`, `D1-P2-MODE-LOGIC`
- `P2_Emerg` → `D1-P2-ENG-RANGE`, `D1-P2-MODE-LOGIC`, `D1-P2-TRIP-LOGIC`
- `P2_MASW` → `D1-P2-ENG-RANGE`, `D1-P2-MODE-LOGIC`
- `P2_MASW_Lamp` → `D1-P2-ENG-RANGE`, `D1-P2-MODE-LOGIC`
- `P2_ManualGO` → `D1-P2-ENG-RANGE`, `D1-P2-MODE-LOGIC`
- `P2_OnOff` → `D1-P2-ENG-RANGE`, `D1-P2-MODE-LOGIC`, `D1-P2-TRIP-LOGIC`
- `P2_TripEx` → `D1-P2-ENG-RANGE`, `D1-P2-MODE-LOGIC`, `D1-P2-TRIP-LOGIC`
- `P2_AutoSD` → `D1-P2-ENG-RANGE`, `D5-P2-SPEED-LOOP`, `D4-P2-SPEED-DYNAMICS`, `D5-X-P2-P4-SYNC`
- `P2_ManualSD` → `D1-P2-ENG-RANGE`, `D5-P2-SPEED-LOOP`, `D4-P2-SPEED-DYNAMICS`
- `P2_RTR` → `D1-P2-ENG-RANGE`, `D1-P2-TRIP-LOGIC`
- `P2_SCO` → `D1-P2-ENG-RANGE`, `D5-P2-SPEED-LOOP`, `D4-P2-SPEED-DYNAMICS`, `D5-X-P2-P4-SYNC`
- `P2_SCST` → `D1-P2-ENG-RANGE`, `D5-P2-SPEED-LOOP`, `D5-X-P2-P4-SYNC`
- `P2_SIT01` → `D1-P2-ENG-RANGE`, `D1-P2-TRIP-LOGIC`, `D5-P2-SPEED-LOOP`, `D4-P2-SPEED-DYNAMICS`, `D3-P2-VIB-CONFIG`, `D5-X-P2-P4-SYNC`
- `P2_VIBTR01` → `D1-P2-ENG-RANGE`, `D1-P2-TRIP-LOGIC`, `D3-P2-VIB-CONFIG`
- `P2_VIBTR02` → `D1-P2-ENG-RANGE`, `D1-P2-TRIP-LOGIC`, `D3-P2-VIB-CONFIG`
- `P2_VIBTR03` → `D1-P2-ENG-RANGE`, `D1-P2-TRIP-LOGIC`, `D3-P2-VIB-CONFIG`
- `P2_VIBTR04` → `D1-P2-ENG-RANGE`, `D1-P2-TRIP-LOGIC`, `D3-P2-VIB-CONFIG`
- `P2_VT01` → `D1-P2-ENG-RANGE`, `D3-P2-VIB-CONFIG`
- `P2_VTR01` → `D1-P2-ENG-RANGE`, `D1-P2-TRIP-LOGIC`
- `P2_VTR02` → `D1-P2-ENG-RANGE`, `D1-P2-TRIP-LOGIC`
- `P2_VTR03` → `D1-P2-ENG-RANGE`, `D1-P2-TRIP-LOGIC`
- `P2_VTR04` → `D1-P2-ENG-RANGE`, `D1-P2-TRIP-LOGIC`

## P3

- `P3_FIT01` → `D1-P3-ENG-RANGE`, `D4-P3-LEVEL-DYNAMICS`, `D5-P3-HYDRAULIC-CONSISTENCY`, `D5-X-P3-P4-HYDRO`
- `P3_LCP01D` → `D1-P3-ENG-RANGE`, `D5-P3-LEVEL-CONTROL`, `D4-P3-LEVEL-DYNAMICS`, `D5-P3-HYDRAULIC-CONSISTENCY`, `D5-X-P3-P4-HYDRO`
- `P3_LCV01D` → `D1-P3-ENG-RANGE`, `D5-P3-LEVEL-CONTROL`, `D4-P3-LEVEL-DYNAMICS`, `D5-P3-HYDRAULIC-CONSISTENCY`, `D5-X-P3-P4-HYDRO`
- `P3_LH01` → `D1-P3-ENG-RANGE`, `D1-P3-LEVEL-LIMITS`, `D5-P3-LEVEL-CONTROL`
- `P3_LIT01` → `D1-P3-ENG-RANGE`, `D1-P3-LEVEL-LIMITS`, `D5-P3-LEVEL-CONTROL`, `D4-P3-LEVEL-DYNAMICS`, `D5-P3-HYDRAULIC-CONSISTENCY`, `D5-X-P3-P4-HYDRO`
- `P3_LL01` → `D1-P3-ENG-RANGE`, `D1-P3-LEVEL-LIMITS`, `D5-P3-LEVEL-CONTROL`
- `P3_PIT01` → `D1-P3-ENG-RANGE`, `D5-P3-HYDRAULIC-CONSISTENCY`, `D5-X-P3-P4-HYDRO`

## P4

- `P4_HT_FD` → `D1-P4-ENG-RANGE`, `D5-P4-HT-CONSISTENCY`, `D4-P4-HT-DYNAMICS`, `D5-X-P3-P4-HYDRO`
- `P4_HT_LD` → `D1-P4-ENG-RANGE`, `D5-P4-HT-CONSISTENCY`, `D4-P4-HT-DYNAMICS`, `D5-P4-LOAD-BALANCE`, `D5-X-P3-P4-HYDRO`
- `P4_HT_PO` → `D1-P4-ENG-RANGE`, `D5-P4-HT-CONSISTENCY`, `D4-P4-HT-DYNAMICS`, `D5-P4-LOAD-BALANCE`, `D5-X-P3-P4-HYDRO`
- `P4_HT_PS` → `D1-P4-ENG-RANGE`, `D5-P4-HT-CONSISTENCY`, `D4-P4-HT-DYNAMICS`, `D5-P4-LOAD-BALANCE`, `D5-P3-LEVEL-CONTROL`, `D5-X-P3-P4-HYDRO`
- `P4_LD` → `D1-P4-ENG-RANGE`, `D5-P4-LOAD-BALANCE`
- `P4_ST_FD` → `D1-P4-ENG-RANGE`, `D5-P4-ST-CONSISTENCY`, `D4-P4-ST-DYNAMICS`, `D5-X-P2-P4-SYNC`
- `P4_ST_GOV` → `D1-P4-ENG-RANGE`, `D5-P4-ST-CONSISTENCY`, `D4-P4-ST-DYNAMICS`, `D5-X-P2-P4-SYNC`
- `P4_ST_LD` → `D1-P4-ENG-RANGE`, `D5-P4-ST-CONSISTENCY`, `D4-P4-ST-DYNAMICS`, `D5-P4-LOAD-BALANCE`
- `P4_ST_PO` → `D1-P4-ENG-RANGE`, `D5-P4-ST-CONSISTENCY`, `D4-P4-ST-DYNAMICS`, `D5-P4-LOAD-BALANCE`, `D5-X-P1-P4-STEAM`, `D5-X-P2-P4-SYNC`
- `P4_ST_PS` → `D1-P4-ENG-RANGE`, `D5-P4-ST-CONSISTENCY`, `D4-P4-ST-DYNAMICS`, `D5-P4-LOAD-BALANCE`
- `P4_ST_PT01` → `D1-P4-ENG-RANGE`, `D5-P4-ST-CONSISTENCY`, `D5-X-P1-P4-STEAM`
- `P4_ST_TT01` → `D1-P4-ENG-RANGE`, `D5-P4-ST-CONSISTENCY`, `D5-X-P1-P4-STEAM`

# D. Training/configuration plan

Only the **normal HAI 23.05 training files** should be used for calibration/training at this architectural stage. No attack label or attack identity is needed to configure these process detectors.

| detector_id | Historian variables to extract | Requirement | Inputs / expected outputs | Engineering rules / thresholds required? |
|---|---|---|---|---|
| `D1-P1-ENG-RANGE` | `P1_B2004`, `P1_B2016`, `P1_B3004`, `P1_B3005`, `P1_B4002`, `P1_B4005`, `P1_B400B`, `P1_B4022`, `P1_FCV01D`, `P1_FCV01Z`, `P1_FCV02D`, `P1_FCV02Z`, `P1_FCV03D`, `P1_FCV03Z`, `P1_FT01`, `P1_FT01Z`, `P1_FT02`, `P1_FT02Z`, `P1_FT03`, `P1_FT03Z`, `P1_LCV01D`, `P1_LCV01Z`, `P1_LIT01`, `P1_PCV01D`, `P1_PCV01Z`, `P1_PCV02D`, `P1_PCV02Z`, `P1_PIT01`, `P1_PIT01_HH`, `P1_PIT02`, `P1_PP01AD`, `P1_PP01AR`, `P1_PP01BD`, `P1_PP01BR`, `P1_PP02D`, `P1_PP02R`, `P1_PP04`, `P1_PP04SP`, `P1_SOL01D`, `P1_SOL03D`, `P1_STSP`, `P1_TIT01`, `P1_TIT02`, `P1_TIT03` | none | Inputs only; expected validity is defined by explicit domains/state/protection logic. | Yes — published ranges/Boolean domains plus controller/engineering logic; fill missing delays, hysteresis and mode rules with ICS-expert values. |
| `D1-P1-PUMP-STATE` | `P1_PP01AD`, `P1_PP01AR`, `P1_PP01BD`, `P1_PP01BR`, `P1_PP02D`, `P1_PP02R` | none | Inputs only; expected validity is defined by explicit domains/state/protection logic. | Yes — published ranges/Boolean domains plus controller/engineering logic; fill missing delays, hysteresis and mode rules with ICS-expert values. |
| `D1-P1-PLANT-STATE` | `P1_STSP`, `P1_SOL01D`, `P1_SOL03D` | none | Inputs only; expected validity is defined by explicit domains/state/protection logic. | Yes — published ranges/Boolean domains plus controller/engineering logic; fill missing delays, hysteresis and mode rules with ICS-expert values. |
| `D3-P1-PC-CONFIG` | `P1_B2004`, `P1_B2016`, `P1_PIT01`, `P1_STSP` | normal-data-training | All listed variables are joint inputs; expected output is membership in a valid normal operating configuration/manifold. | Use known mode constraints where available; otherwise learn valid configurations from normal data. |
| `D5-P1-ACTUATOR-TRACK` | `P1_FCV01D`, `P1_FCV01Z`, `P1_FCV02D`, `P1_FCV02Z`, `P1_FCV03D`, `P1_FCV03Z`, `P1_LCV01D`, `P1_LCV01Z`, `P1_PCV01D`, `P1_PCV01Z`, `P1_PCV02D`, `P1_PCV02Z` | relationship-learning | Causal/driver variables and response variables are jointly supplied; the detector learns or encodes the expected relationship/residual. | Use explicit equations/tolerances if available; otherwise learn the relationship from normal operation and validate it with an ICS expert. |
| `D5-P1-FLOW-CONVERSION` | `P1_FT01`, `P1_FT01Z`, `P1_FT02`, `P1_FT02Z`, `P1_FT03`, `P1_FT03Z` | relationship-learning | Causal/driver variables and response variables are jointly supplied; the detector learns or encodes the expected relationship/residual. | Use explicit equations/tolerances if available; otherwise learn the relationship from normal operation and validate it with an ICS expert. |
| `D5-P1-PC-LOOP` | `P1_B2016`, `P1_PIT01`, `P1_PCV01D`, `P1_PCV02D`, `P1_PCV01Z`, `P1_PCV02Z`, `P1_PP01AD`, `P1_PP01AR`, `P1_PP01BD`, `P1_PP01BR` | relationship-learning | Causal/driver variables and response variables are jointly supplied; the detector learns or encodes the expected relationship/residual. | Use explicit equations/tolerances if available; otherwise learn the relationship from normal operation and validate it with an ICS expert. |
| `D4-P1-PC-DYNAMICS` | `P1_B2016`, `P1_PIT01`, `P1_PCV01D`, `P1_PCV02D` | normal-data-training | Listed variables with time history; expected output is a normal temporal trajectory/transition envelope. | Engineering rate/lag limits should be added if available; otherwise derive timing envelope from normal operation. |
| `D5-P1-LC-LOOP` | `P1_B3004`, `P1_LIT01`, `P1_LCV01D`, `P1_LCV01Z`, `P1_FCV03D`, `P1_FT03`, `P1_FT03Z` | relationship-learning | Causal/driver variables and response variables are jointly supplied; the detector learns or encodes the expected relationship/residual. | Use explicit equations/tolerances if available; otherwise learn the relationship from normal operation and validate it with an ICS expert. |
| `D4-P1-LC-DYNAMICS` | `P1_B3004`, `P1_LIT01`, `P1_LCV01D`, `P1_FCV03D`, `P1_FT03Z` | normal-data-training | Listed variables with time history; expected output is a normal temporal trajectory/transition envelope. | Engineering rate/lag limits should be added if available; otherwise derive timing envelope from normal operation. |
| `D5-P1-FC-LOOP` | `P1_B3005`, `P1_FT03`, `P1_FT03Z`, `P1_FCV03D`, `P1_FCV03Z` | relationship-learning | Causal/driver variables and response variables are jointly supplied; the detector learns or encodes the expected relationship/residual. | Use explicit equations/tolerances if available; otherwise learn the relationship from normal operation and validate it with an ICS expert. |
| `D3-P1-TC-CONFIG` | `P1_B4002`, `P1_B4005`, `P1_B400B`, `P1_B4022`, `P1_TIT01`, `P1_FT02Z` | normal-data-training | All listed variables are joint inputs; expected output is membership in a valid normal operating configuration/manifold. | Use known mode constraints where available; otherwise learn valid configurations from normal data. |
| `D5-P1-TC-LOOP` | `P1_B4002`, `P1_B4022`, `P1_B4005`, `P1_TIT01`, `P1_FCV01D`, `P1_FCV01Z`, `P1_FCV02D`, `P1_FCV02Z`, `P1_FT02`, `P1_FT02Z`, `P1_TIT02` | relationship-learning | Causal/driver variables and response variables are jointly supplied; the detector learns or encodes the expected relationship/residual. | Use explicit equations/tolerances if available; otherwise learn the relationship from normal operation and validate it with an ICS expert. |
| `D4-P1-TC-DYNAMICS` | `P1_B4002`, `P1_B4022`, `P1_TIT01`, `P1_FCV01D`, `P1_FCV02D`, `P1_FT02Z`, `P1_TIT02` | normal-data-training | Listed variables with time history; expected output is a normal temporal trajectory/transition envelope. | Engineering rate/lag limits should be added if available; otherwise derive timing envelope from normal operation. |
| `D5-P1-CC-LOOP` | `P1_PP04SP`, `P1_PP04`, `P1_TIT03` | relationship-learning | Causal/driver variables and response variables are jointly supplied; the detector learns or encodes the expected relationship/residual. | Use explicit equations/tolerances if available; otherwise learn the relationship from normal operation and validate it with an ICS expert. |
| `D4-P1-CC-DYNAMICS` | `P1_PP04SP`, `P1_PP04`, `P1_TIT03` | normal-data-training | Listed variables with time history; expected output is a normal temporal trajectory/transition envelope. | Engineering rate/lag limits should be added if available; otherwise derive timing envelope from normal operation. |
| `D5-P1-MASS-BALANCE` | `P1_FT01Z`, `P1_FT03Z`, `P1_LIT01`, `P1_LCV01D`, `P1_FCV03D`, `P1_SOL01D`, `P1_SOL03D` | relationship-learning | Causal/driver variables and response variables are jointly supplied; the detector learns or encodes the expected relationship/residual. | Use explicit equations/tolerances if available; otherwise learn the relationship from normal operation and validate it with an ICS expert. |
| `D5-P1-THERMAL-CONSISTENCY` | `P1_B400B`, `P1_FT02Z`, `P1_TIT01`, `P1_TIT02`, `P1_TIT03`, `P1_FCV01D`, `P1_FCV02D`, `P1_PP04` | relationship-learning | Causal/driver variables and response variables are jointly supplied; the detector learns or encodes the expected relationship/residual. | Use explicit equations/tolerances if available; otherwise learn the relationship from normal operation and validate it with an ICS expert. |
| `D2-P1-PIT02-STABILITY` | `P1_PIT02`, `P1_PP02D`, `P1_PP02R` | calibration | Input signal(s) plus state-conditioning variables where listed; expected output is a calibrated normal statistical envelope. | Published engineering range is a hard guardrail; tighter normal envelope is calibrated from normal data. |
| `D5-P1-PIT01HH-CONSISTENCY` | `P1_PIT01`, `P1_PIT01_HH` | relationship-learning | Causal/driver variables and response variables are jointly supplied; the detector learns or encodes the expected relationship/residual. | Use explicit equations/tolerances if available; otherwise learn the relationship from normal operation and validate it with an ICS expert. |
| `D1-P2-ENG-RANGE` | `P2_24Vdc`, `P2_ATSW_Lamp`, `P2_AutoGo`, `P2_Emerg`, `P2_MASW`, `P2_MASW_Lamp`, `P2_ManualGO`, `P2_OnOff`, `P2_TripEx`, `P2_AutoSD`, `P2_ManualSD`, `P2_RTR`, `P2_SCO`, `P2_SCST`, `P2_SIT01`, `P2_VIBTR01`, `P2_VIBTR02`, `P2_VIBTR03`, `P2_VIBTR04`, `P2_VT01`, `P2_VTR01`, `P2_VTR02`, `P2_VTR03`, `P2_VTR04` | none | Inputs only; expected validity is defined by explicit domains/state/protection logic. | Yes — published ranges/Boolean domains plus controller/engineering logic; fill missing delays, hysteresis and mode rules with ICS-expert values. |
| `D1-P2-MODE-LOGIC` | `P2_ATSW_Lamp`, `P2_AutoGo`, `P2_MASW`, `P2_MASW_Lamp`, `P2_ManualGO`, `P2_OnOff`, `P2_Emerg`, `P2_TripEx` | none | Inputs only; expected validity is defined by explicit domains/state/protection logic. | Yes — published ranges/Boolean domains plus controller/engineering logic; fill missing delays, hysteresis and mode rules with ICS-expert values. |
| `D1-P2-TRIP-LOGIC` | `P2_SIT01`, `P2_RTR`, `P2_VIBTR01`, `P2_VIBTR02`, `P2_VIBTR03`, `P2_VIBTR04`, `P2_VTR01`, `P2_VTR02`, `P2_VTR03`, `P2_VTR04`, `P2_Emerg`, `P2_TripEx`, `P2_OnOff` | none | Inputs only; expected validity is defined by explicit domains/state/protection logic. | Yes — published ranges/Boolean domains plus controller/engineering logic; fill missing delays, hysteresis and mode rules with ICS-expert values. |
| `D2-P2-24V-STABILITY` | `P2_24Vdc` | calibration | Input signal(s) plus state-conditioning variables where listed; expected output is a calibrated normal statistical envelope. | Published engineering range is a hard guardrail; tighter normal envelope is calibrated from normal data. |
| `D5-P2-SPEED-LOOP` | `P2_AutoSD`, `P2_ManualSD`, `P2_MASW`, `P2_AutoGo`, `P2_ManualGO`, `P2_OnOff`, `P2_SCO`, `P2_SIT01`, `P2_SCST` | relationship-learning | Causal/driver variables and response variables are jointly supplied; the detector learns or encodes the expected relationship/residual. | Use explicit equations/tolerances if available; otherwise learn the relationship from normal operation and validate it with an ICS expert. |
| `D4-P2-SPEED-DYNAMICS` | `P2_AutoSD`, `P2_ManualSD`, `P2_MASW`, `P2_SCO`, `P2_SIT01`, `P2_OnOff` | normal-data-training | Listed variables with time history; expected output is a normal temporal trajectory/transition envelope. | Engineering rate/lag limits should be added if available; otherwise derive timing envelope from normal operation. |
| `D3-P2-VIB-CONFIG` | `P2_SIT01`, `P2_VIBTR01`, `P2_VIBTR02`, `P2_VIBTR03`, `P2_VIBTR04`, `P2_VT01` | normal-data-training | All listed variables are joint inputs; expected output is membership in a valid normal operating configuration/manifold. | Use known mode constraints where available; otherwise learn valid configurations from normal data. |
| `D1-P3-ENG-RANGE` | `P3_FIT01`, `P3_LCP01D`, `P3_LCV01D`, `P3_LH01`, `P3_LIT01`, `P3_LL01`, `P3_PIT01` | none | Inputs only; expected validity is defined by explicit domains/state/protection logic. | Yes — published ranges/Boolean domains plus controller/engineering logic; fill missing delays, hysteresis and mode rules with ICS-expert values. |
| `D1-P3-LEVEL-LIMITS` | `P3_LH01`, `P3_LL01`, `P3_LIT01` | none | Inputs only; expected validity is defined by explicit domains/state/protection logic. | Yes — published ranges/Boolean domains plus controller/engineering logic; fill missing delays, hysteresis and mode rules with ICS-expert values. |
| `D5-P3-LEVEL-CONTROL` | `P3_LH01`, `P3_LL01`, `P3_LIT01`, `P3_LCP01D`, `P3_LCV01D`, `P4_HT_PS`, `P4_HT_LD`, `P4_HT_PO`, `P4_HT_FD` | relationship-learning | Causal/driver variables and response variables are jointly supplied; the detector learns or encodes the expected relationship/residual. | Use explicit equations/tolerances if available; otherwise learn the relationship from normal operation and validate it with an ICS expert. |
| `D4-P3-LEVEL-DYNAMICS` | `P3_LIT01`, `P3_LCP01D`, `P3_LCV01D`, `P3_FIT01` | normal-data-training | Listed variables with time history; expected output is a normal temporal trajectory/transition envelope. | Engineering rate/lag limits should be added if available; otherwise derive timing envelope from normal operation. |
| `D5-P3-HYDRAULIC-CONSISTENCY` | `P3_FIT01`, `P3_PIT01`, `P3_LCP01D`, `P3_LCV01D`, `P3_LIT01` | relationship-learning | Causal/driver variables and response variables are jointly supplied; the detector learns or encodes the expected relationship/residual. | Use explicit equations/tolerances if available; otherwise learn the relationship from normal operation and validate it with an ICS expert. |
| `D1-P4-ENG-RANGE` | `P4_HT_FD`, `P4_HT_LD`, `P4_HT_PO`, `P4_HT_PS`, `P4_LD`, `P4_ST_FD`, `P4_ST_GOV`, `P4_ST_LD`, `P4_ST_PO`, `P4_ST_PS`, `P4_ST_PT01`, `P4_ST_TT01` | none | Inputs only; expected validity is defined by explicit domains/state/protection logic. | Yes — published ranges/Boolean domains plus controller/engineering logic; fill missing delays, hysteresis and mode rules with ICS-expert values. |
| `D5-P4-ST-CONSISTENCY` | `P4_ST_PS`, `P4_ST_LD`, `P4_ST_PO`, `P4_ST_FD`, `P4_ST_GOV`, `P4_ST_PT01`, `P4_ST_TT01` | relationship-learning | Causal/driver variables and response variables are jointly supplied; the detector learns or encodes the expected relationship/residual. | Use explicit equations/tolerances if available; otherwise learn the relationship from normal operation and validate it with an ICS expert. |
| `D4-P4-ST-DYNAMICS` | `P4_ST_PS`, `P4_ST_LD`, `P4_ST_PO`, `P4_ST_FD`, `P4_ST_GOV` | normal-data-training | Listed variables with time history; expected output is a normal temporal trajectory/transition envelope. | Engineering rate/lag limits should be added if available; otherwise derive timing envelope from normal operation. |
| `D5-P4-HT-CONSISTENCY` | `P4_HT_PS`, `P4_HT_LD`, `P4_HT_PO`, `P4_HT_FD` | relationship-learning | Causal/driver variables and response variables are jointly supplied; the detector learns or encodes the expected relationship/residual. | Use explicit equations/tolerances if available; otherwise learn the relationship from normal operation and validate it with an ICS expert. |
| `D4-P4-HT-DYNAMICS` | `P4_HT_PS`, `P4_HT_LD`, `P4_HT_PO`, `P4_HT_FD` | normal-data-training | Listed variables with time history; expected output is a normal temporal trajectory/transition envelope. | Engineering rate/lag limits should be added if available; otherwise derive timing envelope from normal operation. |
| `D5-P4-LOAD-BALANCE` | `P4_LD`, `P4_ST_LD`, `P4_ST_PO`, `P4_ST_PS`, `P4_HT_LD`, `P4_HT_PO`, `P4_HT_PS` | relationship-learning | Causal/driver variables and response variables are jointly supplied; the detector learns or encodes the expected relationship/residual. | Use explicit equations/tolerances if available; otherwise learn the relationship from normal operation and validate it with an ICS expert. |
| `D5-X-P1-P4-STEAM` | `P1_PIT01`, `P1_TIT01`, `P1_TIT02`, `P1_FT02Z`, `P4_ST_PT01`, `P4_ST_TT01`, `P4_ST_PO`, `P4_ST_FD` | relationship-learning | Causal/driver variables and response variables are jointly supplied; the detector learns or encodes the expected relationship/residual. | Use explicit equations/tolerances if available; otherwise learn the relationship from normal operation and validate it with an ICS expert. |
| `D5-X-P2-P4-SYNC` | `P2_SCST`, `P2_SIT01`, `P2_AutoSD`, `P2_SCO`, `P4_ST_FD`, `P4_ST_GOV`, `P4_ST_PO` | relationship-learning | Causal/driver variables and response variables are jointly supplied; the detector learns or encodes the expected relationship/residual. | Use explicit equations/tolerances if available; otherwise learn the relationship from normal operation and validate it with an ICS expert. |
| `D5-X-P3-P4-HYDRO` | `P3_LCP01D`, `P3_LCV01D`, `P3_FIT01`, `P3_PIT01`, `P3_LIT01`, `P4_HT_PS`, `P4_HT_LD`, `P4_HT_PO`, `P4_HT_FD` | relationship-learning | Causal/driver variables and response variables are jointly supplied; the detector learns or encodes the expected relationship/residual. | Use explicit equations/tolerances if available; otherwise learn the relationship from normal operation and validate it with an ICS expert. |

## Recommended calibration order

1. Configure D1 engineering-domain, state and protection rules first. 2. Calibrate command/feedback and raw/converted-signal D5 relationships. 3. Fit local control-loop D5 residual relationships. 4. Train D4 temporal models on normal transients and mode changes. 5. Train D3 configuration detectors only for the few cases where valid modes cannot be fully expressed as rules. 6. Add cross-zone D5 relationships last, after local detectors are stable; this prevents a local instrumentation problem from being mistaken for a cross-process residual.

## Deterministic orchestration dependencies

| Source | Target | Relationship useful for later orchestration |
|---|---|---|
| `D1-P1-PLANT-STATE` | `P1 loop detectors` | Boiler start/stop state should gate or condition interpretation of P1-PC/P1-LC/P1-FC/P1-TC/P1-CC residuals. |
| `D5-P1-FC-LOOP` | `D5-P1-LC-LOOP` | P1-LC explicitly uses FCV03/outflow information as feed-forward disturbance compensation. |
| `D5-P1-ACTUATOR-TRACK` | `P1 loop detectors` | Actuator command/position mismatch should be separated from higher-level loop residuals during orchestration. |
| `D5-P1-PC-LOOP` | `D5-X-P1-P4-STEAM` | Boiler pressure is an upstream state for steam-model pressure/power behavior. |
| `D5-P1-TC-LOOP` | `D5-X-P1-P4-STEAM` | Boiler thermal state is upstream of virtual steam temperature/power behavior. |
| `D5-P1-CC-LOOP` | `D5-P1-THERMAL-CONSISTENCY` | Cooling-pump action changes main-tank temperature and should explain part of the P1 thermal residual. |
| `D1-P2-MODE-LOGIC` | `D5-P2-SPEED-LOOP` | Manual/auto selection determines which speed-demand tag is active. |
| `D1-P2-TRIP-LOGIC` | `D5-P2-SPEED-LOOP` | Trip/emergency state changes the expected speed-control behavior and should gate normal closed-loop residual interpretation. |
| `D5-P4-ST-CONSISTENCY` | `D5-X-P2-P4-SYNC` | STM frequency/power/governor state is the virtual-side context for real rotor speed synchronization. |
| `D5-P4-HT-CONSISTENCY` | `D5-P3-LEVEL-CONTROL` | P4-HTM produces pumping/discharge demands that drive the real P3 water-treatment actuators. |
| `D5-P3-HYDRAULIC-CONSISTENCY` | `D5-X-P3-P4-HYDRO` | P3 hydraulic response provides physical evidence for the hydropower model operating state. |
| `D5-P4-ST-CONSISTENCY` | `D5-P4-LOAD-BALANCE` | Steam-model output/demand state contributes to valid system-level power/load configuration. |
| `D5-P4-HT-CONSISTENCY` | `D5-P4-LOAD-BALANCE` | Hydropower-model output/demand state contributes to valid system-level power/load configuration. |

# E. Unresolved configuration issues

1. Schema inconsistency in the published documentation: the official HAI repository reports 86 data points per second for HAI 23.05, while the technical manual's cross-version tag table is numbered 1..87. The GitHub HAI 23.05 CSV is stored as a 155 MB Git-LFS object and its header is not rendered by the web interface. Therefore this architecture characterizes all 87 names documented in the manual, but implementation MUST intersect the routing map with the actual hai-train*.csv header and remove the manual-only row. Do not guess which row is absent.
2. P1 pressure-reference semantics: P1_B2004 is documented as a heat-exchanger outlet pressure setpoint, whereas the explicit P1-PC loop diagram uses P1_B2016 as the operator setpoint/demand. The hierarchy/mode relationship between B2004 and B2016 is not documented sufficiently for a deterministic rule.
3. P1 temperature-reference hierarchy: P1_B4002 is documented as a heat-exchanger outlet temperature setpoint and appears as a P1-TC target in scenario tables, while the explicit P1-TC loop description uses P1_B4022 as the operator setpoint. B4005 is the temperature PID output and B400B is a heating-water outflow setpoint. The exact cascade/reference hierarchy must be validated from DCS logic or HAIEnd graph data.
4. P1_PIT01_HH is described as the 'highest outlet pressure', but the aggregation window, reset behavior, and whether it is a monitor/high-high representation are not specified. Its D5 rule must not be implemented until this semantics is confirmed.
5. Exact valve and pump command-to-feedback tolerances and start/stop delays are not published. D/Z and D/R consistency detectors require engineering tolerances or calibration from normal HAI 23.05 training data.
6. Exact P2 mode-lamp Boolean logic, TripEx reset semantics, trip hysteresis and latching behavior are not fully specified. The threshold comparisons are high-confidence; detailed state-machine rules require Mark VIe logic confirmation.
7. The manual describes P2_VTR04 as the preset vibration limit for P2_VIBTR03, which appears to be a documentation typo; verify that P2_VTR04 corresponds to P2_VIBTR04 before implementing channel-specific protection rules.
8. P3_FIT01, P3_PIT01, P3_LCP01D and P3_LCV01D use 0..27648 raw/scaled values without engineering units or conversion curves. Physical residuals should be learned/calibrated in raw space until scaling is supplied.
9. P3 LH01/LL01 hysteresis and the exact logic that maps the high/low thresholds to LCP01/LCV01 demand are not fully published; deterministic switching rules need PLC logic or engineering documentation.
10. P4_HT_FD is listed with unit mHz while P4_ST_FD is listed in Hz. Confirm scaling before a cross-zone frequency residual is interpreted quantitatively.
11. The HIL power system is connected to an infinite-bus/grid model. Do not assume P4_ST_PO + P4_HT_PO = P4_LD exactly. The system-level power-balance detector should learn/encode the actual HIL equations or valid operating manifold.
12. Sampling is documented as one data point per second, but any resampling, filtering, controller scan-time differences, transport delay or timestamp jitter relevant to local detectors should be verified in the actual CSV and controller documentation.

## Assumptions deliberately *not* made

- No anomaly is interpreted as a cyberattack.
- No attack labels are used to select detector classes.
- No specific ML algorithm is selected.
- Correlation alone is not used as justification for grouping variables.
- Published min/max ranges are treated as engineering/representation guardrails, not automatically as tight normal-operating thresholds.
- A closed power-balance equation is not assumed for P4 without the HIL model equations.
- The ambiguous B2004/B2016 and B4002/B4022 relationships are not converted into hard deterministic rules without further DCS logic evidence.

# F. Machine-readable configuration

Implementation note: apply the following routing only after intersecting tag names with the actual HAI 23.05 CSV header, because of the documented 86-vs-87 schema discrepancy.

```json
{
  "detectors": [
    {
      "detector_id": "D1-P1-ENG-RANGE",
      "detector_class": "D1",
      "purpose": "Engineering-domain and discrete-domain validation for boiler-process tags.",
      "inputs": [
        "P1_B2004",
        "P1_B2016",
        "P1_B3004",
        "P1_B3005",
        "P1_B4002",
        "P1_B4005",
        "P1_B400B",
        "P1_B4022",
        "P1_FCV01D",
        "P1_FCV01Z",
        "P1_FCV02D",
        "P1_FCV02Z",
        "P1_FCV03D",
        "P1_FCV03Z",
        "P1_FT01",
        "P1_FT01Z",
        "P1_FT02",
        "P1_FT02Z",
        "P1_FT03",
        "P1_FT03Z",
        "P1_LCV01D",
        "P1_LCV01Z",
        "P1_LIT01",
        "P1_PCV01D",
        "P1_PCV01Z",
        "P1_PCV02D",
        "P1_PCV02Z",
        "P1_PIT01",
        "P1_PIT01_HH",
        "P1_PIT02",
        "P1_PP01AD",
        "P1_PP01AR",
        "P1_PP01BD",
        "P1_PP01BR",
        "P1_PP02D",
        "P1_PP02R",
        "P1_PP04",
        "P1_PP04SP",
        "P1_SOL01D",
        "P1_SOL03D",
        "P1_STSP",
        "P1_TIT01",
        "P1_TIT02",
        "P1_TIT03"
      ],
      "monitored_invariant": "Published engineering/representation ranges and Boolean domains must not be violated.",
      "training_requirement": "none",
      "confidence": "high"
    },
    {
      "detector_id": "D1-P1-PUMP-STATE",
      "detector_class": "D1",
      "purpose": "Validate pump command/running-state logic for PP01A, PP01B and PP02.",
      "inputs": [
        "P1_PP01AD",
        "P1_PP01AR",
        "P1_PP01BD",
        "P1_PP01BR",
        "P1_PP02D",
        "P1_PP02R"
      ],
      "monitored_invariant": "Pump run feedback must be logically compatible with start commands, allowing an engineering-defined start/stop delay.",
      "training_requirement": "none",
      "confidence": "high"
    },
    {
      "detector_id": "D1-P1-PLANT-STATE",
      "detector_class": "D1",
      "purpose": "Validate boiler DCS and discrete supply/drain valve operating states.",
      "inputs": [
        "P1_STSP",
        "P1_SOL01D",
        "P1_SOL03D"
      ],
      "monitored_invariant": "Only valid Boolean states and expert-approved combinations/transitions are allowed.",
      "training_requirement": "none",
      "confidence": "medium"
    },
    {
      "detector_id": "D3-P1-PC-CONFIG",
      "detector_class": "D3",
      "purpose": "Check compatibility of the two documented pressure-reference tags and active pressure-control configuration.",
      "inputs": [
        "P1_B2004",
        "P1_B2016",
        "P1_PIT01",
        "P1_STSP"
      ],
      "monitored_invariant": "The simultaneous configuration of pressure references, measured pressure and plant state must match a valid operating mode.",
      "training_requirement": "normal-data-training",
      "confidence": "low"
    },
    {
      "detector_id": "D5-P1-ACTUATOR-TRACK",
      "detector_class": "D5",
      "purpose": "Check analog valve command-to-position consistency.",
      "inputs": [
        "P1_FCV01D",
        "P1_FCV01Z",
        "P1_FCV02D",
        "P1_FCV02Z",
        "P1_FCV03D",
        "P1_FCV03Z",
        "P1_LCV01D",
        "P1_LCV01Z",
        "P1_PCV01D",
        "P1_PCV01Z",
        "P1_PCV02D",
        "P1_PCV02Z"
      ],
      "monitored_invariant": "Measured/current valve position should track the corresponding position command within actuator lag and tolerance.",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D5-P1-FLOW-CONVERSION",
      "detector_class": "D5",
      "purpose": "Validate raw/transformed flow-signal conversion pairs.",
      "inputs": [
        "P1_FT01",
        "P1_FT01Z",
        "P1_FT02",
        "P1_FT02Z",
        "P1_FT03",
        "P1_FT03Z"
      ],
      "monitored_invariant": "Each Z flow value must remain consistent with the documented conversion of its paired raw FT signal.",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D5-P1-PC-LOOP",
      "detector_class": "D5",
      "purpose": "Monitor pressure-control loop consistency.",
      "inputs": [
        "P1_B2016",
        "P1_PIT01",
        "P1_PCV01D",
        "P1_PCV02D",
        "P1_PCV01Z",
        "P1_PCV02Z",
        "P1_PP01AD",
        "P1_PP01AR",
        "P1_PP01BD",
        "P1_PP01BR"
      ],
      "monitored_invariant": "Pressure error, pressure-valve commands/positions and pump availability must exhibit a physically and functionally consistent control response.",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D4-P1-PC-DYNAMICS",
      "detector_class": "D4",
      "purpose": "Monitor pressure-loop transient evolution after reference or actuator changes.",
      "inputs": [
        "P1_B2016",
        "P1_PIT01",
        "P1_PCV01D",
        "P1_PCV02D"
      ],
      "monitored_invariant": "Pressure response must have normal delay, rate, settling and temporal dependence for the pressure loop.",
      "training_requirement": "normal-data-training",
      "confidence": "high"
    },
    {
      "detector_id": "D5-P1-LC-LOOP",
      "detector_class": "D5",
      "purpose": "Monitor return-water-tank level-control consistency including documented feed-forward coupling.",
      "inputs": [
        "P1_B3004",
        "P1_LIT01",
        "P1_LCV01D",
        "P1_LCV01Z",
        "P1_FCV03D",
        "P1_FT03",
        "P1_FT03Z"
      ],
      "monitored_invariant": "Level error, LCV action and the FCV03/outflow disturbance must remain mutually consistent.",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D4-P1-LC-DYNAMICS",
      "detector_class": "D4",
      "purpose": "Monitor tank-level inertia and response to inflow/outflow actuator changes.",
      "inputs": [
        "P1_B3004",
        "P1_LIT01",
        "P1_LCV01D",
        "P1_FCV03D",
        "P1_FT03Z"
      ],
      "monitored_invariant": "Tank level must evolve with physically plausible delay and slope under valve/flow changes.",
      "training_requirement": "normal-data-training",
      "confidence": "high"
    },
    {
      "detector_id": "D5-P1-FC-LOOP",
      "detector_class": "D5",
      "purpose": "Monitor return-water-tank discharge flow control.",
      "inputs": [
        "P1_B3005",
        "P1_FT03",
        "P1_FT03Z",
        "P1_FCV03D",
        "P1_FCV03Z"
      ],
      "monitored_invariant": "Discharge-flow error and FCV03 command/position must be functionally consistent.",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D3-P1-TC-CONFIG",
      "detector_class": "D3",
      "purpose": "Validate the documented temperature/thermal-demand configuration without assuming an undocumented hierarchy.",
      "inputs": [
        "P1_B4002",
        "P1_B4005",
        "P1_B400B",
        "P1_B4022",
        "P1_TIT01",
        "P1_FT02Z"
      ],
      "monitored_invariant": "Temperature references/demands, PID output, heating-water flow and measured temperature must form a valid operating configuration.",
      "training_requirement": "normal-data-training",
      "confidence": "medium"
    },
    {
      "detector_id": "D5-P1-TC-LOOP",
      "detector_class": "D5",
      "purpose": "Monitor temperature-control cascade/feed-forward consistency.",
      "inputs": [
        "P1_B4002",
        "P1_B4022",
        "P1_B4005",
        "P1_TIT01",
        "P1_FCV01D",
        "P1_FCV01Z",
        "P1_FCV02D",
        "P1_FCV02Z",
        "P1_FT02",
        "P1_FT02Z",
        "P1_TIT02"
      ],
      "monitored_invariant": "Temperature demand/error, cascade output, heating-water flow and FCV01/FCV02 actions must be causally consistent.",
      "training_requirement": "relationship-learning",
      "confidence": "medium"
    },
    {
      "detector_id": "D4-P1-TC-DYNAMICS",
      "detector_class": "D4",
      "purpose": "Monitor thermal inertia and cascade-control temporal response.",
      "inputs": [
        "P1_B4002",
        "P1_B4022",
        "P1_TIT01",
        "P1_FCV01D",
        "P1_FCV02D",
        "P1_FT02Z",
        "P1_TIT02"
      ],
      "monitored_invariant": "Temperature must evolve with normal thermal lag and rate following reference, flow and valve changes.",
      "training_requirement": "normal-data-training",
      "confidence": "high"
    },
    {
      "detector_id": "D5-P1-CC-LOOP",
      "detector_class": "D5",
      "purpose": "Monitor cooling-pump control consistency.",
      "inputs": [
        "P1_PP04SP",
        "P1_PP04",
        "P1_TIT03"
      ],
      "monitored_invariant": "Cooling-pump output must be consistent with main-tank temperature and cooler setpoint/activation logic.",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D4-P1-CC-DYNAMICS",
      "detector_class": "D4",
      "purpose": "Monitor main-tank temperature response to cooling-pump actuation.",
      "inputs": [
        "P1_PP04SP",
        "P1_PP04",
        "P1_TIT03"
      ],
      "monitored_invariant": "Cooling activation and temperature response must exhibit plausible delay, direction and rate.",
      "training_requirement": "normal-data-training",
      "confidence": "high"
    },
    {
      "detector_id": "D5-P1-MASS-BALANCE",
      "detector_class": "D5",
      "purpose": "Monitor hydraulic mass-balance consistency around the return-water tank.",
      "inputs": [
        "P1_FT01Z",
        "P1_FT03Z",
        "P1_LIT01",
        "P1_LCV01D",
        "P1_FCV03D",
        "P1_SOL01D",
        "P1_SOL03D"
      ],
      "monitored_invariant": "Net inflow/outflow and valve states must be consistent with the direction and magnitude of level change.",
      "training_requirement": "relationship-learning",
      "confidence": "medium"
    },
    {
      "detector_id": "D5-P1-THERMAL-CONSISTENCY",
      "detector_class": "D5",
      "purpose": "Monitor cross-signal thermal consistency inside the boiler/heat-transfer process.",
      "inputs": [
        "P1_B400B",
        "P1_FT02Z",
        "P1_TIT01",
        "P1_TIT02",
        "P1_TIT03",
        "P1_FCV01D",
        "P1_FCV02D",
        "P1_PP04"
      ],
      "monitored_invariant": "Heating-water flow, valve action, temperatures and cooling action must remain physically coherent.",
      "training_requirement": "relationship-learning",
      "confidence": "medium"
    },
    {
      "detector_id": "D2-P1-PIT02-STABILITY",
      "detector_class": "D2",
      "purpose": "Monitor the heating-water pump supply pressure as a stable process-health signal conditional on pump state.",
      "inputs": [
        "P1_PIT02",
        "P1_PP02D",
        "P1_PP02R"
      ],
      "monitored_invariant": "Within a given pump state, supply pressure should remain within its calibrated statistical operating envelope and not drift abruptly.",
      "training_requirement": "calibration",
      "confidence": "medium"
    },
    {
      "detector_id": "D5-P1-PIT01HH-CONSISTENCY",
      "detector_class": "D5",
      "purpose": "Validate the documented 'highest outlet pressure' signal against outlet pressure.",
      "inputs": [
        "P1_PIT01",
        "P1_PIT01_HH"
      ],
      "monitored_invariant": "The high/highest pressure representation must be consistent with PIT01 under its actual aggregation/monitor semantics.",
      "training_requirement": "relationship-learning",
      "confidence": "low"
    },
    {
      "detector_id": "D1-P2-ENG-RANGE",
      "detector_class": "D1",
      "purpose": "Engineering-domain and discrete-domain validation for turbine-process tags.",
      "inputs": [
        "P2_24Vdc",
        "P2_ATSW_Lamp",
        "P2_AutoGo",
        "P2_Emerg",
        "P2_MASW",
        "P2_MASW_Lamp",
        "P2_ManualGO",
        "P2_OnOff",
        "P2_TripEx",
        "P2_AutoSD",
        "P2_ManualSD",
        "P2_RTR",
        "P2_SCO",
        "P2_SCST",
        "P2_SIT01",
        "P2_VIBTR01",
        "P2_VIBTR02",
        "P2_VIBTR03",
        "P2_VIBTR04",
        "P2_VT01",
        "P2_VTR01",
        "P2_VTR02",
        "P2_VTR03",
        "P2_VTR04"
      ],
      "monitored_invariant": "Published engineering/representation ranges and Boolean domains must not be violated.",
      "training_requirement": "none",
      "confidence": "high"
    },
    {
      "detector_id": "D1-P2-MODE-LOGIC",
      "detector_class": "D1",
      "purpose": "Validate manual/auto, start, on/off and lamp state logic.",
      "inputs": [
        "P2_ATSW_Lamp",
        "P2_AutoGo",
        "P2_MASW",
        "P2_MASW_Lamp",
        "P2_ManualGO",
        "P2_OnOff",
        "P2_Emerg",
        "P2_TripEx"
      ],
      "monitored_invariant": "Mode selector, mode lamps, start controls, on/off state and trip-exit state must follow allowed combinations/transitions.",
      "training_requirement": "none",
      "confidence": "medium"
    },
    {
      "detector_id": "D1-P2-TRIP-LOGIC",
      "detector_class": "D1",
      "purpose": "Monitor overspeed/over-vibration protection consistency.",
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
        "P2_TripEx",
        "P2_OnOff"
      ],
      "monitored_invariant": "Speed/vibration threshold comparisons and emergency/trip state must satisfy the documented protection logic.",
      "training_requirement": "none",
      "confidence": "high"
    },
    {
      "detector_id": "D2-P2-24V-STABILITY",
      "detector_class": "D2",
      "purpose": "Monitor DCS 24-V supply stability.",
      "inputs": [
        "P2_24Vdc"
      ],
      "monitored_invariant": "Supply voltage should remain statistically stable around its normal operating level and avoid abrupt or drifting departures.",
      "training_requirement": "calibration",
      "confidence": "high"
    },
    {
      "detector_id": "D5-P2-SPEED-LOOP",
      "detector_class": "D5",
      "purpose": "Monitor mode-dependent turbine speed-control consistency.",
      "inputs": [
        "P2_AutoSD",
        "P2_ManualSD",
        "P2_MASW",
        "P2_AutoGo",
        "P2_ManualGO",
        "P2_OnOff",
        "P2_SCO",
        "P2_SIT01",
        "P2_SCST"
      ],
      "monitored_invariant": "The active speed demand, controller output and measured RPM must be mutually consistent in the selected operating mode.",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D4-P2-SPEED-DYNAMICS",
      "detector_class": "D4",
      "purpose": "Monitor turbine run-up, engagement and speed-control temporal evolution.",
      "inputs": [
        "P2_AutoSD",
        "P2_ManualSD",
        "P2_MASW",
        "P2_SCO",
        "P2_SIT01",
        "P2_OnOff"
      ],
      "monitored_invariant": "RPM should ramp, engage and settle with the normal sequence, rate, delay and inertia rather than jump independently.",
      "training_requirement": "normal-data-training",
      "confidence": "high"
    },
    {
      "detector_id": "D3-P2-VIB-CONFIG",
      "detector_class": "D3",
      "purpose": "Monitor the multivariate rotor vibration configuration conditional on speed.",
      "inputs": [
        "P2_SIT01",
        "P2_VIBTR01",
        "P2_VIBTR02",
        "P2_VIBTR03",
        "P2_VIBTR04",
        "P2_VT01"
      ],
      "monitored_invariant": "The four orthogonal shaft-vibration channels and key-phasor signal must form a physically plausible configuration for the current speed regime.",
      "training_requirement": "normal-data-training",
      "confidence": "medium"
    },
    {
      "detector_id": "D1-P3-ENG-RANGE",
      "detector_class": "D1",
      "purpose": "Engineering-domain validation for water-treatment tags, including 0..27648 raw channels.",
      "inputs": [
        "P3_FIT01",
        "P3_LCP01D",
        "P3_LCV01D",
        "P3_LH01",
        "P3_LIT01",
        "P3_LL01",
        "P3_PIT01"
      ],
      "monitored_invariant": "Published engineering/representation ranges must not be violated.",
      "training_requirement": "none",
      "confidence": "high"
    },
    {
      "detector_id": "D1-P3-LEVEL-LIMITS",
      "detector_class": "D1",
      "purpose": "Validate high/low level setpoint ordering and level-state constraints.",
      "inputs": [
        "P3_LH01",
        "P3_LL01",
        "P3_LIT01"
      ],
      "monitored_invariant": "Low/high level references must have a valid ordering and the measured level must be interpreted consistently with them and any hysteresis.",
      "training_requirement": "none",
      "confidence": "medium"
    },
    {
      "detector_id": "D5-P3-LEVEL-CONTROL",
      "detector_class": "D5",
      "purpose": "Monitor upper-reservoir level-control consistency.",
      "inputs": [
        "P3_LH01",
        "P3_LL01",
        "P3_LIT01",
        "P3_LCP01D",
        "P3_LCV01D",
        "P4_HT_PS",
        "P4_HT_LD",
        "P4_HT_PO",
        "P4_HT_FD"
      ],
      "monitored_invariant": "Pump/valve demands produced from the HIL hydropower module must be consistent with level thresholds, measured level and hydropower operating state.",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D4-P3-LEVEL-DYNAMICS",
      "detector_class": "D4",
      "purpose": "Monitor upper-reservoir level dynamics.",
      "inputs": [
        "P3_LIT01",
        "P3_LCP01D",
        "P3_LCV01D",
        "P3_FIT01"
      ],
      "monitored_invariant": "Reservoir level must change with physically plausible delay and slope following pump, valve and inflow changes.",
      "training_requirement": "normal-data-training",
      "confidence": "high"
    },
    {
      "detector_id": "D5-P3-HYDRAULIC-CONSISTENCY",
      "detector_class": "D5",
      "purpose": "Monitor pump/valve/flow/pressure hydraulic consistency.",
      "inputs": [
        "P3_FIT01",
        "P3_PIT01",
        "P3_LCP01D",
        "P3_LCV01D",
        "P3_LIT01"
      ],
      "monitored_invariant": "Inlet flow and pressure must be physically consistent with pump command, valve command and reservoir level.",
      "training_requirement": "relationship-learning",
      "confidence": "medium"
    },
    {
      "detector_id": "D1-P4-ENG-RANGE",
      "detector_class": "D1",
      "purpose": "Engineering-domain validation for HIL power-system tags.",
      "inputs": [
        "P4_HT_FD",
        "P4_HT_LD",
        "P4_HT_PO",
        "P4_HT_PS",
        "P4_LD",
        "P4_ST_FD",
        "P4_ST_GOV",
        "P4_ST_LD",
        "P4_ST_PO",
        "P4_ST_PS",
        "P4_ST_PT01",
        "P4_ST_TT01"
      ],
      "monitored_invariant": "Published engineering/representation ranges must not be violated.",
      "training_requirement": "none",
      "confidence": "high"
    },
    {
      "detector_id": "D5-P4-ST-CONSISTENCY",
      "detector_class": "D5",
      "purpose": "Monitor steam-turbine model power/governor/process consistency.",
      "inputs": [
        "P4_ST_PS",
        "P4_ST_LD",
        "P4_ST_PO",
        "P4_ST_FD",
        "P4_ST_GOV",
        "P4_ST_PT01",
        "P4_ST_TT01"
      ],
      "monitored_invariant": "Scheduled power, load demand, output power, frequency deviation, governor action and steam-state variables must remain causally consistent.",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D4-P4-ST-DYNAMICS",
      "detector_class": "D4",
      "purpose": "Monitor steam-turbine-model temporal response.",
      "inputs": [
        "P4_ST_PS",
        "P4_ST_LD",
        "P4_ST_PO",
        "P4_ST_FD",
        "P4_ST_GOV"
      ],
      "monitored_invariant": "Power, governor and frequency response must follow normal delay, ramp and settling behavior after schedule/load changes.",
      "training_requirement": "normal-data-training",
      "confidence": "high"
    },
    {
      "detector_id": "D5-P4-HT-CONSISTENCY",
      "detector_class": "D5",
      "purpose": "Monitor pumped-storage hydropower model consistency.",
      "inputs": [
        "P4_HT_PS",
        "P4_HT_LD",
        "P4_HT_PO",
        "P4_HT_FD"
      ],
      "monitored_invariant": "Scheduled power, load demand, output power and frequency deviation must remain mutually consistent.",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D4-P4-HT-DYNAMICS",
      "detector_class": "D4",
      "purpose": "Monitor hydropower-model temporal response.",
      "inputs": [
        "P4_HT_PS",
        "P4_HT_LD",
        "P4_HT_PO",
        "P4_HT_FD"
      ],
      "monitored_invariant": "Hydropower output/frequency response must follow normal delay, ramp and settling behavior after schedule/load changes.",
      "training_requirement": "normal-data-training",
      "confidence": "high"
    },
    {
      "detector_id": "D5-P4-LOAD-BALANCE",
      "detector_class": "D5",
      "purpose": "Monitor system-level power/load configuration without assuming a closed balance equation not documented for the infinite-bus simulation.",
      "inputs": [
        "P4_LD",
        "P4_ST_LD",
        "P4_ST_PO",
        "P4_ST_PS",
        "P4_HT_LD",
        "P4_HT_PO",
        "P4_HT_PS"
      ],
      "monitored_invariant": "Total load and the two generation-model demand/output/schedule signals must occupy a valid joint operating configuration.",
      "training_requirement": "relationship-learning",
      "confidence": "medium"
    },
    {
      "detector_id": "D5-X-P1-P4-STEAM",
      "detector_class": "D5",
      "purpose": "Monitor boiler-to-steam-turbine-model coupling.",
      "inputs": [
        "P1_PIT01",
        "P1_TIT01",
        "P1_TIT02",
        "P1_FT02Z",
        "P4_ST_PT01",
        "P4_ST_TT01",
        "P4_ST_PO",
        "P4_ST_FD"
      ],
      "monitored_invariant": "Boiler pressure/temperature/flow state must be consistent with the steam pressure/temperature and resulting steam-model behavior.",
      "training_requirement": "relationship-learning",
      "confidence": "medium"
    },
    {
      "detector_id": "D5-X-P2-P4-SYNC",
      "detector_class": "D5",
      "purpose": "Monitor real rotor and virtual steam-turbine synchronization.",
      "inputs": [
        "P2_SCST",
        "P2_SIT01",
        "P2_AutoSD",
        "P2_SCO",
        "P4_ST_FD",
        "P4_ST_GOV",
        "P4_ST_PO"
      ],
      "monitored_invariant": "Rotor-speed change and controller behavior must be consistent with STM frequency/power/governor state.",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D5-X-P3-P4-HYDRO",
      "detector_class": "D5",
      "purpose": "Monitor water-treatment and virtual hydropower coupling.",
      "inputs": [
        "P3_LCP01D",
        "P3_LCV01D",
        "P3_FIT01",
        "P3_PIT01",
        "P3_LIT01",
        "P4_HT_PS",
        "P4_HT_LD",
        "P4_HT_PO",
        "P4_HT_FD"
      ],
      "monitored_invariant": "Hydropower operating demand/state must be consistent with the pump/valve commands and resulting hydraulic response.",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    }
  ],
  "routing": {
    "P1_B2004": [
      "D1-P1-ENG-RANGE",
      "D3-P1-PC-CONFIG"
    ],
    "P1_B2016": [
      "D1-P1-ENG-RANGE",
      "D3-P1-PC-CONFIG",
      "D5-P1-PC-LOOP",
      "D4-P1-PC-DYNAMICS"
    ],
    "P1_B3004": [
      "D1-P1-ENG-RANGE",
      "D5-P1-LC-LOOP",
      "D4-P1-LC-DYNAMICS"
    ],
    "P1_B3005": [
      "D1-P1-ENG-RANGE",
      "D5-P1-FC-LOOP"
    ],
    "P1_B4002": [
      "D1-P1-ENG-RANGE",
      "D3-P1-TC-CONFIG",
      "D5-P1-TC-LOOP",
      "D4-P1-TC-DYNAMICS"
    ],
    "P1_B4005": [
      "D1-P1-ENG-RANGE",
      "D3-P1-TC-CONFIG",
      "D5-P1-TC-LOOP"
    ],
    "P1_B400B": [
      "D1-P1-ENG-RANGE",
      "D3-P1-TC-CONFIG",
      "D5-P1-THERMAL-CONSISTENCY"
    ],
    "P1_B4022": [
      "D1-P1-ENG-RANGE",
      "D3-P1-TC-CONFIG",
      "D5-P1-TC-LOOP",
      "D4-P1-TC-DYNAMICS"
    ],
    "P1_FCV01D": [
      "D1-P1-ENG-RANGE",
      "D5-P1-ACTUATOR-TRACK",
      "D5-P1-TC-LOOP",
      "D4-P1-TC-DYNAMICS",
      "D5-P1-THERMAL-CONSISTENCY"
    ],
    "P1_FCV01Z": [
      "D1-P1-ENG-RANGE",
      "D5-P1-ACTUATOR-TRACK",
      "D5-P1-TC-LOOP"
    ],
    "P1_FCV02D": [
      "D1-P1-ENG-RANGE",
      "D5-P1-ACTUATOR-TRACK",
      "D5-P1-TC-LOOP",
      "D4-P1-TC-DYNAMICS",
      "D5-P1-THERMAL-CONSISTENCY"
    ],
    "P1_FCV02Z": [
      "D1-P1-ENG-RANGE",
      "D5-P1-ACTUATOR-TRACK",
      "D5-P1-TC-LOOP"
    ],
    "P1_FCV03D": [
      "D1-P1-ENG-RANGE",
      "D5-P1-ACTUATOR-TRACK",
      "D5-P1-FC-LOOP",
      "D5-P1-LC-LOOP",
      "D4-P1-LC-DYNAMICS",
      "D5-P1-MASS-BALANCE"
    ],
    "P1_FCV03Z": [
      "D1-P1-ENG-RANGE",
      "D5-P1-ACTUATOR-TRACK",
      "D5-P1-FC-LOOP"
    ],
    "P1_FT01": [
      "D1-P1-ENG-RANGE",
      "D5-P1-FLOW-CONVERSION",
      "D5-P1-MASS-BALANCE"
    ],
    "P1_FT01Z": [
      "D1-P1-ENG-RANGE",
      "D5-P1-FLOW-CONVERSION",
      "D5-P1-MASS-BALANCE"
    ],
    "P1_FT02": [
      "D1-P1-ENG-RANGE",
      "D5-P1-FLOW-CONVERSION",
      "D5-P1-TC-LOOP",
      "D4-P1-TC-DYNAMICS",
      "D5-P1-THERMAL-CONSISTENCY",
      "D5-X-P1-P4-STEAM"
    ],
    "P1_FT02Z": [
      "D1-P1-ENG-RANGE",
      "D5-P1-FLOW-CONVERSION",
      "D5-P1-TC-LOOP",
      "D4-P1-TC-DYNAMICS",
      "D5-P1-THERMAL-CONSISTENCY",
      "D5-X-P1-P4-STEAM"
    ],
    "P1_FT03": [
      "D1-P1-ENG-RANGE",
      "D5-P1-FLOW-CONVERSION",
      "D5-P1-FC-LOOP",
      "D5-P1-LC-LOOP",
      "D4-P1-LC-DYNAMICS",
      "D5-P1-MASS-BALANCE"
    ],
    "P1_FT03Z": [
      "D1-P1-ENG-RANGE",
      "D5-P1-FLOW-CONVERSION",
      "D5-P1-FC-LOOP",
      "D5-P1-LC-LOOP",
      "D4-P1-LC-DYNAMICS",
      "D5-P1-MASS-BALANCE"
    ],
    "P1_LCV01D": [
      "D1-P1-ENG-RANGE",
      "D5-P1-ACTUATOR-TRACK",
      "D5-P1-LC-LOOP",
      "D4-P1-LC-DYNAMICS",
      "D5-P1-MASS-BALANCE"
    ],
    "P1_LCV01Z": [
      "D1-P1-ENG-RANGE",
      "D5-P1-ACTUATOR-TRACK",
      "D5-P1-LC-LOOP"
    ],
    "P1_LIT01": [
      "D1-P1-ENG-RANGE",
      "D5-P1-LC-LOOP",
      "D4-P1-LC-DYNAMICS",
      "D5-P1-MASS-BALANCE"
    ],
    "P1_PCV01D": [
      "D1-P1-ENG-RANGE",
      "D5-P1-ACTUATOR-TRACK",
      "D5-P1-PC-LOOP",
      "D4-P1-PC-DYNAMICS"
    ],
    "P1_PCV01Z": [
      "D1-P1-ENG-RANGE",
      "D5-P1-ACTUATOR-TRACK",
      "D5-P1-PC-LOOP"
    ],
    "P1_PCV02D": [
      "D1-P1-ENG-RANGE",
      "D5-P1-ACTUATOR-TRACK",
      "D5-P1-PC-LOOP",
      "D4-P1-PC-DYNAMICS"
    ],
    "P1_PCV02Z": [
      "D1-P1-ENG-RANGE",
      "D5-P1-ACTUATOR-TRACK",
      "D5-P1-PC-LOOP"
    ],
    "P1_PIT01": [
      "D1-P1-ENG-RANGE",
      "D3-P1-PC-CONFIG",
      "D5-P1-PC-LOOP",
      "D4-P1-PC-DYNAMICS",
      "D5-P1-PIT01HH-CONSISTENCY",
      "D5-X-P1-P4-STEAM"
    ],
    "P1_PIT01_HH": [
      "D1-P1-ENG-RANGE",
      "D5-P1-PIT01HH-CONSISTENCY"
    ],
    "P1_PIT02": [
      "D1-P1-ENG-RANGE",
      "D2-P1-PIT02-STABILITY"
    ],
    "P1_PP01AD": [
      "D1-P1-ENG-RANGE",
      "D1-P1-PUMP-STATE"
    ],
    "P1_PP01AR": [
      "D1-P1-ENG-RANGE",
      "D1-P1-PUMP-STATE"
    ],
    "P1_PP01BD": [
      "D1-P1-ENG-RANGE",
      "D1-P1-PUMP-STATE"
    ],
    "P1_PP01BR": [
      "D1-P1-ENG-RANGE",
      "D1-P1-PUMP-STATE"
    ],
    "P1_PP02D": [
      "D1-P1-ENG-RANGE",
      "D1-P1-PUMP-STATE",
      "D2-P1-PIT02-STABILITY"
    ],
    "P1_PP02R": [
      "D1-P1-ENG-RANGE",
      "D1-P1-PUMP-STATE",
      "D2-P1-PIT02-STABILITY"
    ],
    "P1_PP04": [
      "D1-P1-ENG-RANGE",
      "D5-P1-CC-LOOP",
      "D4-P1-CC-DYNAMICS",
      "D5-P1-THERMAL-CONSISTENCY"
    ],
    "P1_PP04SP": [
      "D1-P1-ENG-RANGE",
      "D5-P1-CC-LOOP",
      "D4-P1-CC-DYNAMICS"
    ],
    "P1_SOL01D": [
      "D1-P1-ENG-RANGE",
      "D1-P1-PLANT-STATE",
      "D5-P1-MASS-BALANCE"
    ],
    "P1_SOL03D": [
      "D1-P1-ENG-RANGE",
      "D1-P1-PLANT-STATE",
      "D5-P1-MASS-BALANCE"
    ],
    "P1_STSP": [
      "D1-P1-ENG-RANGE",
      "D1-P1-PLANT-STATE",
      "D3-P1-PC-CONFIG"
    ],
    "P1_TIT01": [
      "D1-P1-ENG-RANGE",
      "D3-P1-TC-CONFIG",
      "D5-P1-TC-LOOP",
      "D4-P1-TC-DYNAMICS",
      "D5-P1-THERMAL-CONSISTENCY",
      "D5-X-P1-P4-STEAM"
    ],
    "P1_TIT02": [
      "D1-P1-ENG-RANGE",
      "D5-P1-TC-LOOP",
      "D4-P1-TC-DYNAMICS",
      "D5-P1-THERMAL-CONSISTENCY",
      "D5-X-P1-P4-STEAM"
    ],
    "P1_TIT03": [
      "D1-P1-ENG-RANGE",
      "D5-P1-CC-LOOP",
      "D4-P1-CC-DYNAMICS",
      "D5-P1-THERMAL-CONSISTENCY"
    ],
    "P2_24Vdc": [
      "D1-P2-ENG-RANGE",
      "D2-P2-24V-STABILITY"
    ],
    "P2_ATSW_Lamp": [
      "D1-P2-ENG-RANGE",
      "D1-P2-MODE-LOGIC"
    ],
    "P2_AutoGo": [
      "D1-P2-ENG-RANGE",
      "D1-P2-MODE-LOGIC"
    ],
    "P2_Emerg": [
      "D1-P2-ENG-RANGE",
      "D1-P2-MODE-LOGIC",
      "D1-P2-TRIP-LOGIC"
    ],
    "P2_MASW": [
      "D1-P2-ENG-RANGE",
      "D1-P2-MODE-LOGIC"
    ],
    "P2_MASW_Lamp": [
      "D1-P2-ENG-RANGE",
      "D1-P2-MODE-LOGIC"
    ],
    "P2_ManualGO": [
      "D1-P2-ENG-RANGE",
      "D1-P2-MODE-LOGIC"
    ],
    "P2_OnOff": [
      "D1-P2-ENG-RANGE",
      "D1-P2-MODE-LOGIC",
      "D1-P2-TRIP-LOGIC"
    ],
    "P2_TripEx": [
      "D1-P2-ENG-RANGE",
      "D1-P2-MODE-LOGIC",
      "D1-P2-TRIP-LOGIC"
    ],
    "P2_AutoSD": [
      "D1-P2-ENG-RANGE",
      "D5-P2-SPEED-LOOP",
      "D4-P2-SPEED-DYNAMICS",
      "D5-X-P2-P4-SYNC"
    ],
    "P2_ManualSD": [
      "D1-P2-ENG-RANGE",
      "D5-P2-SPEED-LOOP",
      "D4-P2-SPEED-DYNAMICS"
    ],
    "P2_RTR": [
      "D1-P2-ENG-RANGE",
      "D1-P2-TRIP-LOGIC"
    ],
    "P2_SCO": [
      "D1-P2-ENG-RANGE",
      "D5-P2-SPEED-LOOP",
      "D4-P2-SPEED-DYNAMICS",
      "D5-X-P2-P4-SYNC"
    ],
    "P2_SCST": [
      "D1-P2-ENG-RANGE",
      "D5-P2-SPEED-LOOP",
      "D5-X-P2-P4-SYNC"
    ],
    "P2_SIT01": [
      "D1-P2-ENG-RANGE",
      "D1-P2-TRIP-LOGIC",
      "D5-P2-SPEED-LOOP",
      "D4-P2-SPEED-DYNAMICS",
      "D3-P2-VIB-CONFIG",
      "D5-X-P2-P4-SYNC"
    ],
    "P2_VIBTR01": [
      "D1-P2-ENG-RANGE",
      "D1-P2-TRIP-LOGIC",
      "D3-P2-VIB-CONFIG"
    ],
    "P2_VIBTR02": [
      "D1-P2-ENG-RANGE",
      "D1-P2-TRIP-LOGIC",
      "D3-P2-VIB-CONFIG"
    ],
    "P2_VIBTR03": [
      "D1-P2-ENG-RANGE",
      "D1-P2-TRIP-LOGIC",
      "D3-P2-VIB-CONFIG"
    ],
    "P2_VIBTR04": [
      "D1-P2-ENG-RANGE",
      "D1-P2-TRIP-LOGIC",
      "D3-P2-VIB-CONFIG"
    ],
    "P2_VT01": [
      "D1-P2-ENG-RANGE",
      "D3-P2-VIB-CONFIG"
    ],
    "P2_VTR01": [
      "D1-P2-ENG-RANGE",
      "D1-P2-TRIP-LOGIC"
    ],
    "P2_VTR02": [
      "D1-P2-ENG-RANGE",
      "D1-P2-TRIP-LOGIC"
    ],
    "P2_VTR03": [
      "D1-P2-ENG-RANGE",
      "D1-P2-TRIP-LOGIC"
    ],
    "P2_VTR04": [
      "D1-P2-ENG-RANGE",
      "D1-P2-TRIP-LOGIC"
    ],
    "P3_FIT01": [
      "D1-P3-ENG-RANGE",
      "D4-P3-LEVEL-DYNAMICS",
      "D5-P3-HYDRAULIC-CONSISTENCY",
      "D5-X-P3-P4-HYDRO"
    ],
    "P3_LCP01D": [
      "D1-P3-ENG-RANGE",
      "D5-P3-LEVEL-CONTROL",
      "D4-P3-LEVEL-DYNAMICS",
      "D5-P3-HYDRAULIC-CONSISTENCY",
      "D5-X-P3-P4-HYDRO"
    ],
    "P3_LCV01D": [
      "D1-P3-ENG-RANGE",
      "D5-P3-LEVEL-CONTROL",
      "D4-P3-LEVEL-DYNAMICS",
      "D5-P3-HYDRAULIC-CONSISTENCY",
      "D5-X-P3-P4-HYDRO"
    ],
    "P3_LH01": [
      "D1-P3-ENG-RANGE",
      "D1-P3-LEVEL-LIMITS",
      "D5-P3-LEVEL-CONTROL"
    ],
    "P3_LIT01": [
      "D1-P3-ENG-RANGE",
      "D1-P3-LEVEL-LIMITS",
      "D5-P3-LEVEL-CONTROL",
      "D4-P3-LEVEL-DYNAMICS",
      "D5-P3-HYDRAULIC-CONSISTENCY",
      "D5-X-P3-P4-HYDRO"
    ],
    "P3_LL01": [
      "D1-P3-ENG-RANGE",
      "D1-P3-LEVEL-LIMITS",
      "D5-P3-LEVEL-CONTROL"
    ],
    "P3_PIT01": [
      "D1-P3-ENG-RANGE",
      "D5-P3-HYDRAULIC-CONSISTENCY",
      "D5-X-P3-P4-HYDRO"
    ],
    "P4_HT_FD": [
      "D1-P4-ENG-RANGE",
      "D5-P4-HT-CONSISTENCY",
      "D4-P4-HT-DYNAMICS",
      "D5-X-P3-P4-HYDRO"
    ],
    "P4_HT_LD": [
      "D1-P4-ENG-RANGE",
      "D5-P4-HT-CONSISTENCY",
      "D4-P4-HT-DYNAMICS",
      "D5-P4-LOAD-BALANCE",
      "D5-X-P3-P4-HYDRO"
    ],
    "P4_HT_PO": [
      "D1-P4-ENG-RANGE",
      "D5-P4-HT-CONSISTENCY",
      "D4-P4-HT-DYNAMICS",
      "D5-P4-LOAD-BALANCE",
      "D5-X-P3-P4-HYDRO"
    ],
    "P4_HT_PS": [
      "D1-P4-ENG-RANGE",
      "D5-P4-HT-CONSISTENCY",
      "D4-P4-HT-DYNAMICS",
      "D5-P4-LOAD-BALANCE",
      "D5-P3-LEVEL-CONTROL",
      "D5-X-P3-P4-HYDRO"
    ],
    "P4_LD": [
      "D1-P4-ENG-RANGE",
      "D5-P4-LOAD-BALANCE"
    ],
    "P4_ST_FD": [
      "D1-P4-ENG-RANGE",
      "D5-P4-ST-CONSISTENCY",
      "D4-P4-ST-DYNAMICS",
      "D5-X-P2-P4-SYNC"
    ],
    "P4_ST_GOV": [
      "D1-P4-ENG-RANGE",
      "D5-P4-ST-CONSISTENCY",
      "D4-P4-ST-DYNAMICS",
      "D5-X-P2-P4-SYNC"
    ],
    "P4_ST_LD": [
      "D1-P4-ENG-RANGE",
      "D5-P4-ST-CONSISTENCY",
      "D4-P4-ST-DYNAMICS",
      "D5-P4-LOAD-BALANCE"
    ],
    "P4_ST_PO": [
      "D1-P4-ENG-RANGE",
      "D5-P4-ST-CONSISTENCY",
      "D4-P4-ST-DYNAMICS",
      "D5-P4-LOAD-BALANCE",
      "D5-X-P1-P4-STEAM",
      "D5-X-P2-P4-SYNC"
    ],
    "P4_ST_PS": [
      "D1-P4-ENG-RANGE",
      "D5-P4-ST-CONSISTENCY",
      "D4-P4-ST-DYNAMICS",
      "D5-P4-LOAD-BALANCE"
    ],
    "P4_ST_PT01": [
      "D1-P4-ENG-RANGE",
      "D5-P4-ST-CONSISTENCY",
      "D5-X-P1-P4-STEAM"
    ],
    "P4_ST_TT01": [
      "D1-P4-ENG-RANGE",
      "D5-P4-ST-CONSISTENCY",
      "D5-X-P1-P4-STEAM"
    ]
  },
  "dependencies": [
    {
      "source": "D1-P1-PLANT-STATE",
      "target": "P1 loop detectors",
      "relationship": "Boiler start/stop state should gate or condition interpretation of P1-PC/P1-LC/P1-FC/P1-TC/P1-CC residuals."
    },
    {
      "source": "D5-P1-FC-LOOP",
      "target": "D5-P1-LC-LOOP",
      "relationship": "P1-LC explicitly uses FCV03/outflow information as feed-forward disturbance compensation."
    },
    {
      "source": "D5-P1-ACTUATOR-TRACK",
      "target": "P1 loop detectors",
      "relationship": "Actuator command/position mismatch should be separated from higher-level loop residuals during orchestration."
    },
    {
      "source": "D5-P1-PC-LOOP",
      "target": "D5-X-P1-P4-STEAM",
      "relationship": "Boiler pressure is an upstream state for steam-model pressure/power behavior."
    },
    {
      "source": "D5-P1-TC-LOOP",
      "target": "D5-X-P1-P4-STEAM",
      "relationship": "Boiler thermal state is upstream of virtual steam temperature/power behavior."
    },
    {
      "source": "D5-P1-CC-LOOP",
      "target": "D5-P1-THERMAL-CONSISTENCY",
      "relationship": "Cooling-pump action changes main-tank temperature and should explain part of the P1 thermal residual."
    },
    {
      "source": "D1-P2-MODE-LOGIC",
      "target": "D5-P2-SPEED-LOOP",
      "relationship": "Manual/auto selection determines which speed-demand tag is active."
    },
    {
      "source": "D1-P2-TRIP-LOGIC",
      "target": "D5-P2-SPEED-LOOP",
      "relationship": "Trip/emergency state changes the expected speed-control behavior and should gate normal closed-loop residual interpretation."
    },
    {
      "source": "D5-P4-ST-CONSISTENCY",
      "target": "D5-X-P2-P4-SYNC",
      "relationship": "STM frequency/power/governor state is the virtual-side context for real rotor speed synchronization."
    },
    {
      "source": "D5-P4-HT-CONSISTENCY",
      "target": "D5-P3-LEVEL-CONTROL",
      "relationship": "P4-HTM produces pumping/discharge demands that drive the real P3 water-treatment actuators."
    },
    {
      "source": "D5-P3-HYDRAULIC-CONSISTENCY",
      "target": "D5-X-P3-P4-HYDRO",
      "relationship": "P3 hydraulic response provides physical evidence for the hydropower model operating state."
    },
    {
      "source": "D5-P4-ST-CONSISTENCY",
      "target": "D5-P4-LOAD-BALANCE",
      "relationship": "Steam-model output/demand state contributes to valid system-level power/load configuration."
    },
    {
      "source": "D5-P4-HT-CONSISTENCY",
      "target": "D5-P4-LOAD-BALANCE",
      "relationship": "Hydropower-model output/demand state contributes to valid system-level power/load configuration."
    }
  ],
  "unresolved": [
    "Schema inconsistency in the published documentation: the official HAI repository reports 86 data points per second for HAI 23.05, while the technical manual's cross-version tag table is numbered 1..87. The GitHub HAI 23.05 CSV is stored as a 155 MB Git-LFS object and its header is not rendered by the web interface. Therefore this architecture characterizes all 87 names documented in the manual, but implementation MUST intersect the routing map with the actual hai-train*.csv header and remove the manual-only row. Do not guess which row is absent.",
    "P1 pressure-reference semantics: P1_B2004 is documented as a heat-exchanger outlet pressure setpoint, whereas the explicit P1-PC loop diagram uses P1_B2016 as the operator setpoint/demand. The hierarchy/mode relationship between B2004 and B2016 is not documented sufficiently for a deterministic rule.",
    "P1 temperature-reference hierarchy: P1_B4002 is documented as a heat-exchanger outlet temperature setpoint and appears as a P1-TC target in scenario tables, while the explicit P1-TC loop description uses P1_B4022 as the operator setpoint. B4005 is the temperature PID output and B400B is a heating-water outflow setpoint. The exact cascade/reference hierarchy must be validated from DCS logic or HAIEnd graph data.",
    "P1_PIT01_HH is described as the 'highest outlet pressure', but the aggregation window, reset behavior, and whether it is a monitor/high-high representation are not specified. Its D5 rule must not be implemented until this semantics is confirmed.",
    "Exact valve and pump command-to-feedback tolerances and start/stop delays are not published. D/Z and D/R consistency detectors require engineering tolerances or calibration from normal HAI 23.05 training data.",
    "Exact P2 mode-lamp Boolean logic, TripEx reset semantics, trip hysteresis and latching behavior are not fully specified. The threshold comparisons are high-confidence; detailed state-machine rules require Mark VIe logic confirmation.",
    "The manual describes P2_VTR04 as the preset vibration limit for P2_VIBTR03, which appears to be a documentation typo; verify that P2_VTR04 corresponds to P2_VIBTR04 before implementing channel-specific protection rules.",
    "P3_FIT01, P3_PIT01, P3_LCP01D and P3_LCV01D use 0..27648 raw/scaled values without engineering units or conversion curves. Physical residuals should be learned/calibrated in raw space until scaling is supplied.",
    "P3 LH01/LL01 hysteresis and the exact logic that maps the high/low thresholds to LCP01/LCV01 demand are not fully published; deterministic switching rules need PLC logic or engineering documentation.",
    "P4_HT_FD is listed with unit mHz while P4_ST_FD is listed in Hz. Confirm scaling before a cross-zone frequency residual is interpreted quantitatively.",
    "The HIL power system is connected to an infinite-bus/grid model. Do not assume P4_ST_PO + P4_HT_PO = P4_LD exactly. The system-level power-balance detector should learn/encode the actual HIL equations or valid operating manifold.",
    "Sampling is documented as one data point per second, but any resampling, filtering, controller scan-time differences, transport delay or timestamp jitter relevant to local detectors should be verified in the actual CSV and controller documentation."
  ]
}
```

# Sources used for architectural interpretation

1. Official HAI repository — dataset versions, process/testbed description, file layout, point count and license: `https://github.com/icsdataset/hai`
2. Official HAI technical manual in the repository — process-control diagrams, tag descriptions/ranges, HAI 23.05 collection description: `https://github.com/icsdataset/hai/blob/master/hai_dataset_technical_details.pdf`
3. Official HAI 23.05 Git-LFS training file page (used to confirm the concrete release/file and that the file is too large for GitHub rendering): `https://github.com/icsdataset/hai/blob/master/hai-23.05/hai-train1.csv`

## Review checklist for an ICS expert

- Confirm the exact HAI 23.05 CSV header and remove the single manual-only candidate tag if necessary.
- Confirm P1 setpoint hierarchy: B2004↔B2016 and B4002↔B4022/B4005/B400B.
- Supply command/feedback delays and tolerances for valve and pump consistency.
- Confirm P2 trip latching/reset and mode-lamp logic.
- Supply P3 raw-channel scaling and threshold hysteresis.
- Confirm P4 frequency units and actual power-balance equations.
- Approve or simplify cross-zone residual groups after local detectors are validated.