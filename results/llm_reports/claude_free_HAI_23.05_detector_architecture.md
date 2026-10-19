# Process-Oriented Anomaly Detector Architecture — HAI 23.05 (HIL-based Augmented ICS Dataset)

**Scope note:** This configuration is built from the publicly documented HAI SCADA point list (the 59-point core tag set: `P1.*`, `P2.*`, `P3.*`, `P4.*`), the associated control-loop documentation (P1‑PC, P1‑LC, P1‑FC, P1‑TC, P2‑SC, P3‑LC), and the testbed process architecture (Boiler P1, Turbine P2, Water Treatment P3, HIL Simulation P4) as published by the HAI dataset authors (icsdataset/hai, HAI 1.0 technical manual). HAI 23.05 / HAIEnd 23.05 extend this core set to 86 and 225 points/second respectively, adding further internal DCS logic points for the boiler; the additional tag names, descriptions, and units for those extended points were not resolvable from available public metadata and are listed under **Section E (Unresolved Configuration Issues)**. The architecture below is therefore complete and directly usable for the 59-point core (present in all HAI versions including 23.05) and structurally extensible once the additional tag schema is supplied.

No anomaly detection, classification, or attack inference is performed here. This is a **detector-class routing configuration** only.

---

## A. Variable Characterization Table

Legend — Signal type: `SP`=setpoint, `PV`=process variable (sensor), `CV`=control output (actuator command), `FB`=actuator position feedback, `TH`=protection threshold, `ST`=discrete state, `PROT`=protection/interlock input.

### A.1 Boiler Process (P1) — Pressure Control loop (P1-PC)

| Tag | Functional role | Signal type | Dominant invariant | Detector class(es) | Related variables | Reasoning | Confidence |
|---|---|---|---|---|---|---|---|
| P1.B2004 | Operator pressure setpoint source | SP | Explicit bounded range, operator-issued step changes | D1 | P1.B2016 | Value must remain within engineering-defined safe pressure range; changes are discrete operator actions, not continuous drift | High |
| P1.B2016 | Working pressure setpoint fed to P1-PC (derived from B2004 + steam-turbine electrical load) | SP | Causal relationship to B2004 and P4 load signals | D1, D5 | P1.B2004, P4.ST_LD, P1.PIT01 | Its value is not free — it is a function of B2004 and turbine load; consistency detector needed to confirm this causal link holds | High |
| P1.PIT01 | Pressure control loop process variable | PV | Temporal dependence on setpoint via feedback loop; causal consistency with CV | D4, D5 | P1.B2016, P1.PCV01D/Z, P1.PCV02D/Z | Sensor reading must track setpoint with characteristic lag/inertia and be causally explained by valve position | High |
| P1.PCV01D | Pressure control valve 1 — position command | CV | Bounded 0–100%, functional consistency with loop error | D1, D5 | P1.PIT01, P1.B2016, P1.PCV01Z | Command must respond to loop error (PV vs SP) and stay in physical actuator range | High |
| P1.PCV01Z | Pressure control valve 1 — feedback position | FB | Actuator response consistency with command | D5, D4 | P1.PCV01D | Feedback should track command with bounded delay (actuator dynamics); mismatch = actuator/sensor inconsistency | High |
| P1.PCV02D | Pressure control valve 2 — position command | CV | Same as PCV01D (dual-valve pressure actuation) | D1, D5 | P1.PIT01, P1.B2016, P1.PCV02Z | Same reasoning as PCV01D; two valves jointly regulate pressure | High |
| P1.PCV02Z | Pressure control valve 2 — feedback position | FB | Actuator response consistency | D5, D4 | P1.PCV02D | Same reasoning as PCV01Z | High |

### A.2 Boiler Process (P1) — Level Control loop (P1-LC)

| Tag | Functional role | Signal type | Dominant invariant | Detector class(es) | Related variables | Reasoning | Confidence |
|---|---|---|---|---|---|---|---|
| P1.B3004 | Operator level setpoint, return water tank | SP | Explicit bounded range, discrete operator changes | D1 | P1.LIT01 | Engineering range constraint (0–720 mm); no continuous physical drift expected | High |
| P1.LIT01 | Return water tank level (loop PV) | PV | Temporal/inertial response to SP via CV; feedforward-compensated | D4, D5 | P1.B3004, P1.LCV01D/Z, P1.FCV03D (feedforward) | Level responds with tank-capacitance-driven inertia; feedforward from outflow (FCV03D) is a documented causal path that must also hold | High |
| P1.LCV01D | Level control valve — position command | CV | Bounded range, functional response to loop error | D1, D5 | P1.LIT01, P1.B3004, P1.LCV01Z | Command must be explainable by level error and outflow disturbance | High |
| P1.LCV01Z | Level control valve — feedback position | FB | Actuator response consistency | D5, D4 | P1.LCV01D | Standard command/feedback consistency pair | High |

### A.3 Boiler Process (P1) — Flow Control loop (P1-FC)

| Tag | Functional role | Signal type | Dominant invariant | Detector class(es) | Related variables | Reasoning | Confidence |
|---|---|---|---|---|---|---|---|
| P1.B3005 | Operator outflow-rate setpoint, return tank | SP | Explicit bounded range | D1 | P1.FT03/Z | Engineering range constraint (0–2500 L/H) | High |
| P1.FT03 | Raw flow transmitter digital signal (outflow) | PV | Statistical stability / sensor-level signal | D2 | P1.FT03Z | Raw transmitter signal; primarily a stable, calibratable statistical signal feeding the derived flow value | Medium |
| P1.FT03Z | Converted outflow rate, return water tank (loop PV) | PV | Temporal response to SP via CV | D4, D5 | P1.B3005, P1.FCV03D/Z, P1.LIT01 | Engineering-unit flow that closes P1-FC and feeds P1-LC as feedforward — dual functional role | High |
| P1.FCV03D | Flow/level control valve — position command | CV | Bounded range, dual-loop functional response (P1-FC direct, P1-LC feedforward) | D1, D5 | P1.FT03Z, P1.B3005, P1.LIT01, P1.FCV03Z | Shared actuator across two control loops — consistency detector must reconcile both influences | High |
| P1.FCV03Z | Flow/level control valve — feedback position | FB | Actuator response consistency | D5, D4 | P1.FCV03D | Standard command/feedback pair | High |

### A.4 Boiler Process (P1) — Temperature Control loop (P1-TC, cascade + feedforward)

| Tag | Functional role | Signal type | Dominant invariant | Detector class(es) | Related variables | Reasoning | Confidence |
|---|---|---|---|---|---|---|---|
| P1.B4002 | Operator temperature setpoint, heat-exchanger outlet | SP | Explicit bounded range | D1 | P1.TIT01 | Engineering range constraint (0–100 °C) | High |
| P1.B4005 | Temperature cascade control on/off | ST | Discrete state, valid values {0,1} | D1 | P1.B4022, P1.TIT01 | Binary control-mode flag; forbidden values/unexpected toggling pattern is a rule violation, not a statistical one | High |
| P1.B400B | Outflow-rate setpoint, heating water tank | SP | Explicit bounded range | D1 | P1.FT02/Z | Engineering range constraint (0–2500 L/H) | High |
| P1.B4022 | Temperature demand fed to P1-TC (derived from B4005 + steam-turbine load) | SP | Causal derivation from B4005 and P4 load | D1, D5 | P1.B4002, P1.B4005, P4.ST_LD, P1.TIT01 | Not independently free — must be consistent with cascade-mode flag and turbine load, mirroring the B2016/pressure pattern | High |
| P1.TIT01 | Heat-exchanger outlet temperature (loop PV, main vessel) | PV | Temporal dependence with cascade + feedforward structure | D4, D5 | P1.B4022, P1.FCV01D/Z, P1.FCV02D/Z, P1.FT01/Z | Governed by cascade control with feedforward compensation from water flow — response shape is a joint function of multiple inputs | High |
| P1.FCV01D | Heat-transfer flow valve 1 — position command | CV | Bounded range, cascade-loop functional response | D1, D5 | P1.TIT01, P1.FT01/Z, P1.FCV01Z | Inner-loop actuator of the temperature cascade | High |
| P1.FCV01Z | Heat-transfer flow valve 1 — feedback position | FB | Actuator response consistency | D5, D4 | P1.FCV01D | Standard command/feedback pair | High |
| P1.FCV02D | Heat-transfer flow valve 2 — position command | CV | Bounded range, cascade-loop functional response | D1, D5 | P1.TIT01, P1.FT02/Z, P1.FCV02Z | Same role as FCV01D on the second flow path | High |
| P1.FCV02Z | Heat-transfer flow valve 2 — feedback position | FB | Actuator response consistency | D5, D4 | P1.FCV02D | Standard command/feedback pair | High |
| P1.FT01 | Raw flow transmitter digital signal (inner loop) | PV | Statistical stability | D2 | P1.FT01Z | Raw transmitter signal underlying the converted inflow rate | Medium |
| P1.FT01Z | Converted inflow rate into return water tank | PV | Multivariate consistency with cascade inner loop | D3, D5 | P1.TIT01, P1.FCV01D/Z | Feedforward variable to the inner flow loop of the temperature cascade | High |
| P1.FT02 | Raw flow transmitter digital signal (heating tank outlet) | PV | Statistical stability | D2 | P1.FT02Z | Raw transmitter signal | Medium |
| P1.FT02Z | Converted outflow rate at heating water tank | PV | Multivariate consistency with cascade | D3, D5 | P1.TIT01, P1.FCV02D/Z, P1.B400B | Feeds both the cascade and the heating-tank outflow setpoint relationship | High |

### A.5 Boiler Process (P1) — Auxiliary heating subsystem (insufficient loop documentation)

| Tag | Functional role | Signal type | Dominant invariant | Detector class(es) | Related variables | Reasoning | Confidence |
|---|---|---|---|---|---|---|---|
| P1.PIT02 | Water supply pressure, heating water pump | PV | Statistical stability (no documented closed loop) | D2 | P1.TIT02 | No explicit controller documented for this signal; treat as monitored auxiliary sensor until loop context is confirmed | Low — **insufficient information**: no control-loop documentation available for the heating-water-pump subsystem |
| P1.TIT02 | Temperature of heating water tank | PV | Statistical stability | D2 | P1.PIT02, P1.B400B | Same — likely related to the heating tank outflow setpoint (B400B) but explicit control relationship not documented | Low — **insufficient information** |

### A.6 Turbine Process (P2) — Speed Control loop (P2-SC)

| Tag | Functional role | Signal type | Dominant invariant | Detector class(es) | Related variables | Reasoning | Confidence |
|---|---|---|---|---|---|---|---|
| P2.SD01 | Operator/HIL speed setpoint | SP | Explicit bounded range, ramp-limited transitions | D1, D4 | P2.SIT01 | Range-bounded (0–3600 RPM); the loop uses a documented ramp-and-engage sequence, so setpoint-following has a defined temporal shape | High |
| P2.SIT01 | Motor speed (loop PV) | PV | Temporal dependence on SP through PI control with ramp/engage sequence | D4, D5 | P2.SD01 | Rotating-machine inertia produces a characteristic speed-ramp/settle pattern; deviation from expected trajectory is a temporal-dynamics invariant | High |

### A.7 Turbine Process (P2) — Vibration / rotor-condition monitoring

| Tag | Functional role | Signal type | Dominant invariant | Detector class(es) | Related variables | Reasoning | Confidence |
|---|---|---|---|---|---|---|---|
| P2.VT01 | Key-phasor phase-lag signal near motor | PV | Statistical stability tied to rotational speed | D2, D5 | P2.SIT01 | Phase reference signal whose stability is speed-dependent | Medium |
| P2.VYT02 | Y-axis vibration displacement, first mass wheel | PV | Multivariate (orbit shape), speed-dependent | D3, D5 | P2.VXT02, P2.SIT01 | Individual displacement may be within range, but the X/Y pair defines a shaft-orbit shape whose normality is a joint (multivariate) property | High |
| P2.VXT02 | X-axis vibration displacement, first mass wheel | PV | Multivariate (orbit shape) | D3, D5 | P2.VYT02, P2.SIT01 | Same reasoning — orbit-pair partner | High |
| P2.VYT03 | Y-axis vibration displacement, second mass wheel | PV | Multivariate (orbit shape) | D3, D5 | P2.VXT03, P2.SIT01 | Same pattern at the second bearing location | High |
| P2.VXT03 | X-axis vibration displacement, second mass wheel | PV | Multivariate (orbit shape) | D3, D5 | P2.VYT03, P2.SIT01 | Same pattern at the second bearing location | High |

### A.8 Turbine Process (P2) — Protection / discrete-state group

| Tag | Functional role | Signal type | Dominant invariant | Detector class(es) | Related variables | Reasoning | Confidence |
|---|---|---|---|---|---|---|---|
| P2.24VDC | DCS power supply voltage | PV | Explicit operating-range constraint | D1, D2 | — | Power-rail health signal; primarily a threshold/range check, secondarily statistically stable | Medium |
| P2.Auto | System auto/manual mode | ST | Discrete valid-state constraint | D1 | P2.On, P2.SD01 | Mode flag; forbidden-transition logic (e.g., unexpected mode flips during active control) is rule-based | High |
| P2.Emgy | Emergency-stop input | PROT | Discrete/protection logic, forbidden-state combinations | D1 | P2.On, P2.TripEx | Safety-interlock signal; normal behavior is defined purely by protection logic, not statistics | High |
| P2.On | System on/off input | ST | Discrete valid-state constraint | D1 | P2.Auto, P2.Emgy, P2.SIT01 | State must be consistent with whether the turbine is actually rotating (SIT01) | High |
| P2.TripEx | Trip exit input | PROT | Discrete/protection logic | D1 | P2.Emgy, P2.On | Protection/interlock signal — rule-based by definition | High |

### A.9 Water Treatment Process (P3) — Level Control loop (P3-LC)

| Tag | Functional role | Signal type | Dominant invariant | Detector class(es) | Related variables | Reasoning | Confidence |
|---|---|---|---|---|---|---|---|
| P3.LT01 | Upper tank water level (loop PV) | PV | Temporal dependence on pump/valve commands; causal link to HIL hydro model | D4, D5 | P3.LCP01D, P3.LCV01D, P4.HT_PO | Tank-capacitance dynamics respond to pump/valve commands and jointly determine hydro-power output in the HIL model | High |
| P3.LH01 | High water-level setpoint / protection threshold | TH | Explicit protection constraint relative to LT01 | D1 | P3.LT01 | Defines a forbidden-region boundary for the level PV — classic rule-based protection invariant | High |
| P3.LL01 | Low water-level setpoint / protection threshold | TH | Explicit protection constraint relative to LT01 | D1 | P3.LT01 | Same reasoning as LH01, lower bound | High |
| P3.LCP01D | Feed-water pump speed command | CV | Bounded range, functional response to level error and HIL discharge demand | D1, D5 | P3.LT01, P4.HT_PO, P3.LCV01D | Command should be explainable by level error and by the hydro-model's pumping/discharge demand | High |
| P3.LCV01D | Level control valve — position command | CV | Bounded range, functional response | D1, D5 | P3.LT01, P4.HT_PO, P3.LCP01D | Same reasoning as LCP01D; valve and pump act jointly per the documented P3-LC architecture | High |

### A.10 HIL Simulation (P4) — Steam-turbine / power-grid model (couples P1 + P2)

| Tag | Functional role | Signal type | Dominant invariant | Detector class(es) | Related variables | Reasoning | Confidence |
|---|---|---|---|---|---|---|---|
| P4.LD | Total electrical load demand (grid-level) | SP/external | Statistical stability / bounded operating range | D1, D2 | P4.ST_LD, P4.HT_LD | External load-demand signal driving both generator models; not itself derived from other listed tags | Medium |
| P4.ST_FD | Frequency deviation, steam-turbine model | PV | Explicit small-band constraint (grid synchronization) | D1, D5 | P4.HT_FD | Must stay within a narrow band around zero (60 Hz sync); also must be consistent with the hydro model's frequency deviation (shared grid) | High |
| P4.ST_PO | Output power, steam-turbine model | PV | Causal consistency with boiler/turbine physical state | D5, D4 | P1.PIT01, P1.TIT01, P2.SIT01, P4.ST_PS | This is the simulated electrical output driven by real boiler pressure/temperature and turbine speed — the core cross-subsystem causal invariant of the testbed | High |
| P4.ST_PT01 | Digital steam pressure value in steam-turbine model | PV | Causal/physical consistency with P1.PIT01 | D5 | P1.PIT01 | Documented as being derived from the real boiler pressure signal transmitted to the HIL simulator | High |
| P4.ST_TT01 | Digital steam temperature value in steam-turbine model | PV | Causal/physical consistency with P1.TIT01 | D5 | P1.TIT01 | Documented as being derived from the real boiler temperature signal | High |
| P4.ST_LD | Electrical load demand for steam-turbine model | SP | Causal derivation from P4.LD | D1, D5 | P4.LD, P1.B2016, P1.B4022 | Feeds back into P1 as the load term in B2016/B4022 — closes the cyber-physical loop | High |
| P4.ST_PS | Scheduled power demand, steam-turbine model | PV | Causal consistency with ST_PO/ST_LD | D5 | P4.ST_PO, P4.ST_LD | Internal model consistency variable | Medium |

### A.11 HIL Simulation (P4) — Hydro-turbine model (couples P3)

| Tag | Functional role | Signal type | Dominant invariant | Detector class(es) | Related variables | Reasoning | Confidence |
|---|---|---|---|---|---|---|---|
| P4.HT_FD | Frequency deviation, hydro-turbine model | PV | Explicit small-band constraint (grid sync) | D1, D5 | P4.ST_FD | Same shared-grid reasoning as ST_FD | High |
| P4.HT_PO | Output power, hydro-turbine model | PV | Causal consistency with water-treatment physical state | D5, D4 | P3.LT01, P3.LCP01D, P3.LCV01D, P4.HT_PS | Simulated output driven by real discharge/level behavior of P3 — mirrors the ST_PO relationship for the hydro side | High |
| P4.HT_LD | Electrical load demand for hydro-turbine model | SP | Causal derivation from P4.LD | D1, D5 | P4.LD, P3.LCP01D, P3.LCV01D | Feeds back into P3 pump/valve demand — closes the cyber-physical loop on the water-treatment side | High |
| P4.HT_PS | Scheduled power demand, hydro-turbine model | PV | Causal consistency with HT_PO/HT_LD | D5 | P4.HT_PO, P4.HT_LD | Internal model consistency variable | Medium |

---

## B. Functional Detector Groups

| detector_id | detector_class | Functional purpose | input_variables | Process/subsystem scope | Monitored invariant | Training/calibration requirement | Related detector groups |
|---|---|---|---|---|---|---|---|
| D-P1-PC-RULE | D1 | Range/logic check on pressure-loop setpoints and valve commands | P1.B2004, P1.B2016, P1.PCV01D, P1.PCV02D | P1 pressure loop | Explicit engineering bounds | none (predefined rules) | D-P1-PC-CONS |
| D-P1-PC-CONS | D5 | Consistency between pressure setpoint, PV and dual-valve actuation | P1.B2016, P1.PIT01, P1.PCV01D/Z, P1.PCV02D/Z | P1 pressure loop | Expected closed-loop relationship SP↔PV↔CV | relationship-learning (or calibrated physical model) | D-P1-PC-RULE, D-P4-STM-CONS |
| D-P1-LC-CONS | D5 | Consistency of level loop incl. feedforward from outflow | P1.B3004, P1.LIT01, P1.LCV01D/Z, P1.FCV03D | P1 level loop | SP↔PV↔CV + feedforward from outflow disturbance | relationship-learning | D-P1-FC-CONS |
| D-P1-FC-CONS | D5 | Consistency of flow loop, dual role as P1-LC feedforward source | P1.B3005, P1.FT03Z, P1.FCV03D/Z | P1 flow loop | SP↔PV↔CV | relationship-learning | D-P1-LC-CONS |
| D-P1-TEMP-CASCADE | D5 | Consistency of cascade+feedforward temperature control (outer TIT01 loop, inner flow loop) | P1.B4002, P1.B4005, P1.B4022, P1.B400B, P1.TIT01, P1.FCV01D/Z, P1.FCV02D/Z, P1.FT01Z, P1.FT02Z | P1 temperature loop | Cascade/feedforward causal structure | relationship-learning | D-P1-TEMP-RULE, D-P1-ACT-CONS |
| D-P1-TEMP-RULE | D1 | Range/state checks on temperature setpoints and cascade mode flag | P1.B4002, P1.B4005, P1.B400B, P1.B4022 | P1 temperature loop | Explicit bounds and valid discrete states | none (predefined rules) | D-P1-TEMP-CASCADE |
| D-P1-SENSORS-STAT | D2 | Statistical stability/drift monitoring of raw transmitter signals | P1.FT01, P1.FT02, P1.FT03, P1.PIT02, P1.TIT02 | P1 sensor layer | Stable statistical distribution during steady operation | statistical calibration using normal-operation data | D-P1-TEMP-CASCADE, D-P1-FC-CONS |
| D-P1-ACT-CONS | D5 | Command/feedback consistency across all P1 valve pairs | P1.FCV01D/Z, P1.FCV02D/Z, P1.FCV03D/Z, P1.LCV01D/Z, P1.PCV01D/Z, P1.PCV02D/Z | P1 actuator layer | Feedback tracks command within actuator dynamics | statistical calibration (response-time/lag characterization) | All P1 loop detectors |
| D-P2-SC-CONS | D5 | Speed-loop setpoint/PV consistency incl. ramp-and-engage sequence | P2.SD01, P2.SIT01 | P2 speed loop | Documented ramp/PI-tracking behavior | relationship-learning | D-P2-SC-TEMP, D-P4-STM-CONS |
| D-P2-SC-TEMP | D4 | Temporal-shape monitoring of the ramp/engage speed trajectory | P2.SD01, P2.SIT01 | P2 speed loop | Sequence structure, inertia of speed ramp | training using normal-operation data | D-P2-SC-CONS |
| D-P2-VIB-ORBIT | D3 | Multivariate rotor-orbit configuration monitoring | P2.VYT02, P2.VXT02, P2.VYT03, P2.VXT03, P2.VT01 | P2 vibration/rotor monitoring | Joint orbit shape at each bearing, speed-dependent | training using normal-operation data (speed-conditioned) | D-P2-SC-CONS |
| D-P2-PROT-RULE | D1 | Discrete protection/interlock logic | P2.Auto, P2.Emgy, P2.On, P2.TripEx, P2.24VDC | P2 protection layer | Valid states, forbidden transitions | none (predefined rules) | D-P2-SC-CONS |
| D-P3-LC-CONS | D5 | Level-loop consistency incl. joint pump+valve actuation and HIL discharge demand | P3.LT01, P3.LCP01D, P3.LCV01D, P4.HT_PO | P3 level loop, coupling to P4-HTM | Expected closed-loop and cross-subsystem causal relationship | relationship-learning | D-P3-PROT-RULE, D-P4-HTM-CONS |
| D-P3-PROT-RULE | D1 | High/low level protection threshold checks | P3.LH01, P3.LL01, P3.LT01 | P3 level loop | Forbidden-region boundaries | none (predefined rules) | D-P3-LC-CONS |
| D-P4-STM-CONS | D5 | Cross-subsystem causal consistency: boiler/turbine physical state → steam-turbine model output | P1.PIT01, P1.TIT01, P2.SIT01, P4.ST_PT01, P4.ST_TT01, P4.ST_PO, P4.ST_PS | P1+P2+P4 (steam side) | Physical-to-virtual causal mapping | relationship-learning | D-P1-PC-CONS, D-P2-SC-CONS |
| D-P4-HTM-CONS | D5 | Cross-subsystem causal consistency: water-treatment physical state → hydro-turbine model output | P3.LT01, P3.LCP01D, P3.LCV01D, P4.HT_PO, P4.HT_PS | P3+P4 (hydro side) | Physical-to-virtual causal mapping | relationship-learning | D-P3-LC-CONS |
| D-P4-GRID-BALANCE | D5 | Grid-level load/frequency balance across both generator models | P4.LD, P4.ST_LD, P4.HT_LD, P4.ST_FD, P4.HT_FD | P4 (whole HIL layer) | Load-demand allocation and shared 60 Hz synchronization consistency | relationship-learning | D-P4-STM-CONS, D-P4-HTM-CONS |
| D-P4-LOOPBACK-RULE | D1 | Range check on frequency-deviation band and load-demand bounds | P4.ST_FD, P4.HT_FD, P4.LD, P4.ST_LD, P4.HT_LD | P4 (whole HIL layer) | Explicit narrow-band and range constraints | none (predefined rules) | D-P4-GRID-BALANCE |

---

## C. Routing Map (process variable → detector instance(s))

```
P1.B2004    -> [D-P1-PC-RULE]
P1.B2016    -> [D-P1-PC-RULE, D-P1-PC-CONS]
P1.PIT01    -> [D-P1-PC-CONS, D-P4-STM-CONS]
P1.PCV01D   -> [D-P1-PC-RULE, D-P1-PC-CONS, D-P1-ACT-CONS]
P1.PCV01Z   -> [D-P1-PC-CONS, D-P1-ACT-CONS]
P1.PCV02D   -> [D-P1-PC-RULE, D-P1-PC-CONS, D-P1-ACT-CONS]
P1.PCV02Z   -> [D-P1-PC-CONS, D-P1-ACT-CONS]
P1.B3004    -> [D-P1-LC-CONS]
P1.LIT01    -> [D-P1-LC-CONS]
P1.LCV01D   -> [D-P1-LC-CONS, D-P1-ACT-CONS]
P1.LCV01Z   -> [D-P1-LC-CONS, D-P1-ACT-CONS]
P1.B3005    -> [D-P1-FC-CONS]
P1.FT03     -> [D-P1-SENSORS-STAT]
P1.FT03Z    -> [D-P1-FC-CONS, D-P1-LC-CONS]
P1.FCV03D   -> [D-P1-FC-CONS, D-P1-LC-CONS, D-P1-ACT-CONS]
P1.FCV03Z   -> [D-P1-FC-CONS, D-P1-ACT-CONS]
P1.B4002    -> [D-P1-TEMP-RULE]
P1.B4005    -> [D-P1-TEMP-RULE, D-P1-TEMP-CASCADE]
P1.B400B    -> [D-P1-TEMP-RULE, D-P1-TEMP-CASCADE]
P1.B4022    -> [D-P1-TEMP-RULE, D-P1-TEMP-CASCADE]
P1.TIT01    -> [D-P1-TEMP-CASCADE, D-P4-STM-CONS]
P1.FCV01D   -> [D-P1-TEMP-CASCADE, D-P1-ACT-CONS]
P1.FCV01Z   -> [D-P1-TEMP-CASCADE, D-P1-ACT-CONS]
P1.FCV02D   -> [D-P1-TEMP-CASCADE, D-P1-ACT-CONS]
P1.FCV02Z   -> [D-P1-TEMP-CASCADE, D-P1-ACT-CONS]
P1.FT01     -> [D-P1-SENSORS-STAT]
P1.FT01Z    -> [D-P1-TEMP-CASCADE]
P1.FT02     -> [D-P1-SENSORS-STAT]
P1.FT02Z    -> [D-P1-TEMP-CASCADE]
P1.PIT02    -> [D-P1-SENSORS-STAT]
P1.TIT02    -> [D-P1-SENSORS-STAT]
P2.SD01     -> [D-P2-SC-CONS, D-P2-SC-TEMP]
P2.SIT01    -> [D-P2-SC-CONS, D-P2-SC-TEMP, D-P4-STM-CONS]
P2.VT01     -> [D-P2-VIB-ORBIT]
P2.VYT02    -> [D-P2-VIB-ORBIT]
P2.VXT02    -> [D-P2-VIB-ORBIT]
P2.VYT03    -> [D-P2-VIB-ORBIT]
P2.VXT03    -> [D-P2-VIB-ORBIT]
P2.24VDC    -> [D-P2-PROT-RULE]
P2.Auto     -> [D-P2-PROT-RULE]
P2.Emgy     -> [D-P2-PROT-RULE]
P2.On       -> [D-P2-PROT-RULE]
P2.TripEx   -> [D-P2-PROT-RULE]
P3.LT01     -> [D-P3-LC-CONS, D-P3-PROT-RULE, D-P4-HTM-CONS]
P3.LH01     -> [D-P3-PROT-RULE]
P3.LL01     -> [D-P3-PROT-RULE]
P3.LCP01D   -> [D-P3-LC-CONS, D-P4-HTM-CONS]
P3.LCV01D   -> [D-P3-LC-CONS, D-P4-HTM-CONS]
P4.LD       -> [D-P4-GRID-BALANCE, D-P4-LOOPBACK-RULE]
P4.ST_FD    -> [D-P4-GRID-BALANCE, D-P4-LOOPBACK-RULE]
P4.ST_PO    -> [D-P4-STM-CONS]
P4.ST_PT01  -> [D-P4-STM-CONS]
P4.ST_TT01  -> [D-P4-STM-CONS]
P4.ST_LD    -> [D-P4-GRID-BALANCE, D-P4-LOOPBACK-RULE, D-P4-STM-CONS]
P4.ST_PS    -> [D-P4-STM-CONS]
P4.HT_FD    -> [D-P4-GRID-BALANCE, D-P4-LOOPBACK-RULE]
P4.HT_PO    -> [D-P4-HTM-CONS, D-P3-LC-CONS]
P4.HT_LD    -> [D-P4-GRID-BALANCE, D-P4-LOOPBACK-RULE, D-P4-HTM-CONS]
P4.HT_PS    -> [D-P4-HTM-CONS]
```

---

## D. Training / Configuration Plan

| Detector | Historian extraction (normal-operation variables) | Training or calibration | Inputs / expected outputs | Explicit rules or thresholds required |
|---|---|---|---|---|
| D-P1-PC-RULE | not required (design-basis ranges only) | none | inputs: B2004, B2016, PCV01D, PCV02D | Yes — engineering range limits per point table (e.g. B2004 0–10 bar) |
| D-P1-PC-CONS | B2016, PIT01, PCV01D/Z, PCV02D/Z over full normal operating envelope | relationship-learning | input: B2016, PCV01D/Z, PCV02D/Z; expected output: PIT01 | No (learned relationship); range guard as backstop |
| D-P1-LC-CONS | B3004, LIT01, LCV01D/Z, FCV03D over normal envelope incl. outflow disturbances | relationship-learning | input: B3004, FCV03D (disturbance); expected output: LIT01, LCV01D | No |
| D-P1-FC-CONS | B3005, FT03Z, FCV03D/Z | relationship-learning | input: B3005; expected output: FT03Z, FCV03D | No |
| D-P1-TEMP-CASCADE | B4002, B4005, B4022, B400B, TIT01, FCV01D/Z, FCV02D/Z, FT01Z, FT02Z across both cascade modes (on/off) | relationship-learning | input: B4022, FT01Z, FT02Z; expected output: TIT01, FCV01D/Z, FCV02D/Z | No; cascade-mode flag itself rule-checked separately |
| D-P1-TEMP-RULE | not required | none | inputs: B4002, B4005, B400B, B4022 | Yes — ranges + valid {0,1} states for B4005 |
| D-P1-SENSORS-STAT | FT01, FT02, FT03, PIT02, TIT02 over representative steady-state windows | statistical calibration | inputs only (univariate/small-group) | No explicit rules; calibrated statistical bounds |
| D-P1-ACT-CONS | all D/Z pairs over full range of commanded moves | statistical calibration (lag/response-time characterization) | input: *D; expected output: *Z | Optional bounded max-lag threshold |
| D-P2-SC-CONS | SD01, SIT01 across the documented ramp/engage sequence | relationship-learning | input: SD01; expected output: SIT01 | No |
| D-P2-SC-TEMP | SD01, SIT01 time series | training using normal-operation data | sequence input: SD01, SIT01 | No |
| D-P2-VIB-ORBIT | VYT02, VXT02, VYT03, VXT03, VT01 conditioned on SIT01 (speed bins) | training using normal-operation data | inputs: all five, conditioned on speed | No |
| D-P2-PROT-RULE | not required | none | inputs: Auto, Emgy, On, TripEx, 24VDC | Yes — valid states and forbidden combinations (e.g. On=1 while Emgy active) |
| D-P3-LC-CONS | LT01, LCP01D, LCV01D, HT_PO over normal envelope | relationship-learning | input: HT_PO (discharge demand); expected output: LT01, LCP01D, LCV01D | No |
| D-P3-PROT-RULE | not required | none | inputs: LH01, LL01, LT01 | Yes — LT01 must remain within [LL01, LH01] |
| D-P4-STM-CONS | PIT01, TIT01, SIT01, ST_PT01, ST_TT01, ST_PO, ST_PS | relationship-learning | input: PIT01, TIT01, SIT01; expected output: ST_PT01, ST_TT01, ST_PO | No |
| D-P4-HTM-CONS | LT01, LCP01D, LCV01D, HT_PO, HT_PS | relationship-learning | input: LT01, LCP01D, LCV01D; expected output: HT_PO | No |
| D-P4-GRID-BALANCE | LD, ST_LD, HT_LD, ST_FD, HT_FD | relationship-learning | input: LD; expected output: ST_LD, HT_LD, and their consistency with ST_FD/HT_FD | Narrow-band guard on frequency deviation as backstop |
| D-P4-LOOPBACK-RULE | not required | none | inputs: ST_FD, HT_FD, LD, ST_LD, HT_LD | Yes — narrow frequency-deviation band, load-demand ranges |

---

## E. Unresolved Configuration Issues

1. **Extended HAI 23.05 / HAIEnd 23.05 tag set not resolved.** HAI 23.05 reportedly carries 86 points/second and HAIEnd 23.05 carries 225 points/second, versus the 59-point core documented here. The names, descriptions, units, and ranges of the additional ~27 (HAI) and ~166 (HAIEnd, internal boiler-DCS logic) points were not available from accessible public documentation at the time of this analysis. **Required:** the HAI 23.05 technical manual / column header list (or direct CSV header extraction) to extend Sections A–C to the full tag set.
2. **P1 heating-subsystem control loop (PIT02, TIT02) is undocumented.** No controller diagram was found linking these two sensors into a named feedback loop analogous to P1-PC/LC/FC/TC. **Required:** P&ID or controller documentation for the heating-water-pump subsystem; until then these tags are conservatively routed to a statistical-only detector (D-P1-SENSORS-STAT).
3. **P4.LD origin is ambiguous.** It is treated as an external/scheduling input to the grid model rather than a variable derived from other listed tags, but the exact source (operator schedule vs. HIL scenario script) is not documented. **Required:** confirmation of whether P4.LD should be treated as an exogenous input (as assumed) or as a variable with its own upstream causal dependency.
4. **Sampling frequency and per-tag statistical ranges were not available in machine-readable form** for the 23.05 release; ranges shown in Section A are taken from the HAI 1.0 technical manual and should be re-validated against 23.05, since equipment recalibration or testbed changes between versions may have shifted normal operating bands.
5. **Exact actuator response-time bounds** (used for calibrating D-P1-ACT-CONS and D5 command/feedback detectors generally) require representative normal-operation data extraction; no such data was provided as input to this analysis, only descriptive process documentation.
6. **HAIEnd internal DCS logic points** are explicitly described as covering "internal control logic of the boiler's DCS" — this likely introduces additional D1 (rule-based, internal PLC/DCS logic-state) and D5 (internal signal vs. external point consistency) detector candidates that cannot be specified without the actual tag list.
7. **Assumption requiring ICS-expert validation:** the causal-derivation relationships assumed for B2016 (= f(B2004, turbine load)) and B4022 (= f(B4005, B4002, turbine load)) are inferred from the technical manual's prose description ("Pressure/temperature demand to follow B2004/B4005 and electrical load from steam-turbine model") rather than an explicit block diagram equation. The functional form of this dependency should be confirmed before calibrating D-P1-PC-CONS / D-P1-TEMP-CASCADE.

---

## F. Machine-Readable Configuration

```json
{
  "detectors": [
    {"detector_id": "D-P1-PC-RULE", "detector_class": "D1", "purpose": "Range/logic check on pressure-loop setpoints and valve commands", "inputs": ["P1.B2004", "P1.B2016", "P1.PCV01D", "P1.PCV02D"], "monitored_invariant": "explicit engineering bounds", "training_requirement": "none", "confidence": "high"},
    {"detector_id": "D-P1-PC-CONS", "detector_class": "D5", "purpose": "Consistency between pressure setpoint, PV and dual-valve actuation", "inputs": ["P1.B2016", "P1.PIT01", "P1.PCV01D", "P1.PCV01Z", "P1.PCV02D", "P1.PCV02Z"], "monitored_invariant": "closed-loop SP-PV-CV relationship", "training_requirement": "relationship-learning", "confidence": "high"},
    {"detector_id": "D-P1-LC-CONS", "detector_class": "D5", "purpose": "Consistency of level loop incl. feedforward from outflow", "inputs": ["P1.B3004", "P1.LIT01", "P1.LCV01D", "P1.LCV01Z", "P1.FCV03D"], "monitored_invariant": "closed-loop + feedforward relationship", "training_requirement": "relationship-learning", "confidence": "high"},
    {"detector_id": "D-P1-FC-CONS", "detector_class": "D5", "purpose": "Consistency of flow loop, dual role as feedforward source to level loop", "inputs": ["P1.B3005", "P1.FT03Z", "P1.FCV03D", "P1.FCV03Z"], "monitored_invariant": "closed-loop SP-PV-CV relationship", "training_requirement": "relationship-learning", "confidence": "high"},
    {"detector_id": "D-P1-TEMP-CASCADE", "detector_class": "D5", "purpose": "Consistency of cascade+feedforward temperature control", "inputs": ["P1.B4002", "P1.B4005", "P1.B4022", "P1.B400B", "P1.TIT01", "P1.FCV01D", "P1.FCV01Z", "P1.FCV02D", "P1.FCV02Z", "P1.FT01Z", "P1.FT02Z"], "monitored_invariant": "cascade/feedforward causal structure", "training_requirement": "relationship-learning", "confidence": "high"},
    {"detector_id": "D-P1-TEMP-RULE", "detector_class": "D1", "purpose": "Range/state checks on temperature setpoints and cascade mode flag", "inputs": ["P1.B4002", "P1.B4005", "P1.B400B", "P1.B4022"], "monitored_invariant": "explicit bounds and valid discrete states", "training_requirement": "none", "confidence": "high"},
    {"detector_id": "D-P1-SENSORS-STAT", "detector_class": "D2", "purpose": "Statistical stability/drift monitoring of raw transmitter signals", "inputs": ["P1.FT01", "P1.FT02", "P1.FT03", "P1.PIT02", "P1.TIT02"], "monitored_invariant": "stable statistical distribution during steady operation", "training_requirement": "calibration", "confidence": "medium"},
    {"detector_id": "D-P1-ACT-CONS", "detector_class": "D5", "purpose": "Command/feedback consistency across all P1 valve pairs", "inputs": ["P1.FCV01D", "P1.FCV01Z", "P1.FCV02D", "P1.FCV02Z", "P1.FCV03D", "P1.FCV03Z", "P1.LCV01D", "P1.LCV01Z", "P1.PCV01D", "P1.PCV01Z", "P1.PCV02D", "P1.PCV02Z"], "monitored_invariant": "feedback tracks command within actuator dynamics", "training_requirement": "calibration", "confidence": "high"},
    {"detector_id": "D-P2-SC-CONS", "detector_class": "D5", "purpose": "Speed-loop setpoint/PV consistency incl. ramp-and-engage sequence", "inputs": ["P2.SD01", "P2.SIT01"], "monitored_invariant": "documented ramp/PI tracking behavior", "training_requirement": "relationship-learning", "confidence": "high"},
    {"detector_id": "D-P2-SC-TEMP", "detector_class": "D4", "purpose": "Temporal-shape monitoring of the ramp/engage speed trajectory", "inputs": ["P2.SD01", "P2.SIT01"], "monitored_invariant": "sequence structure, inertia of speed ramp", "training_requirement": "normal-data-training", "confidence": "high"},
    {"detector_id": "D-P2-VIB-ORBIT", "detector_class": "D3", "purpose": "Multivariate rotor-orbit configuration monitoring", "inputs": ["P2.VYT02", "P2.VXT02", "P2.VYT03", "P2.VXT03", "P2.VT01"], "monitored_invariant": "joint orbit shape at each bearing, speed-dependent", "training_requirement": "normal-data-training", "confidence": "high"},
    {"detector_id": "D-P2-PROT-RULE", "detector_class": "D1", "purpose": "Discrete protection/interlock logic", "inputs": ["P2.Auto", "P2.Emgy", "P2.On", "P2.TripEx", "P2.24VDC"], "monitored_invariant": "valid states, forbidden transitions", "training_requirement": "none", "confidence": "high"},
    {"detector_id": "D-P3-LC-CONS", "detector_class": "D5", "purpose": "Level-loop consistency incl. joint pump+valve actuation and HIL discharge demand", "inputs": ["P3.LT01", "P3.LCP01D", "P3.LCV01D", "P4.HT_PO"], "monitored_invariant": "closed-loop + cross-subsystem causal relationship", "training_requirement": "relationship-learning", "confidence": "high"},
    {"detector_id": "D-P3-PROT-RULE", "detector_class": "D1", "purpose": "High/low level protection threshold checks", "inputs": ["P3.LH01", "P3.LL01", "P3.LT01"], "monitored_invariant": "forbidden-region boundaries", "training_requirement": "none", "confidence": "high"},
    {"detector_id": "D-P4-STM-CONS", "detector_class": "D5", "purpose": "Cross-subsystem causal consistency: boiler/turbine physical state to steam-turbine model output", "inputs": ["P1.PIT01", "P1.TIT01", "P2.SIT01", "P4.ST_PT01", "P4.ST_TT01", "P4.ST_PO", "P4.ST_PS"], "monitored_invariant": "physical-to-virtual causal mapping", "training_requirement": "relationship-learning", "confidence": "high"},
    {"detector_id": "D-P4-HTM-CONS", "detector_class": "D5", "purpose": "Cross-subsystem causal consistency: water-treatment physical state to hydro-turbine model output", "inputs": ["P3.LT01", "P3.LCP01D", "P3.LCV01D", "P4.HT_PO", "P4.HT_PS"], "monitored_invariant": "physical-to-virtual causal mapping", "training_requirement": "relationship-learning", "confidence": "high"},
    {"detector_id": "D-P4-GRID-BALANCE", "detector_class": "D5", "purpose": "Grid-level load/frequency balance across both generator models", "inputs": ["P4.LD", "P4.ST_LD", "P4.HT_LD", "P4.ST_FD", "P4.HT_FD"], "monitored_invariant": "load-demand allocation and shared 60Hz synchronization consistency", "training_requirement": "relationship-learning", "confidence": "medium"},
    {"detector_id": "D-P4-LOOPBACK-RULE", "detector_class": "D1", "purpose": "Range check on frequency-deviation band and load-demand bounds", "inputs": ["P4.ST_FD", "P4.HT_FD", "P4.LD", "P4.ST_LD", "P4.HT_LD"], "monitored_invariant": "explicit narrow-band and range constraints", "training_requirement": "none", "confidence": "high"}
  ],
  "routing": {
    "P1.B2004": ["D-P1-PC-RULE"],
    "P1.B2016": ["D-P1-PC-RULE", "D-P1-PC-CONS"],
    "P1.PIT01": ["D-P1-PC-CONS", "D-P4-STM-CONS"],
    "P1.PCV01D": ["D-P1-PC-RULE", "D-P1-PC-CONS", "D-P1-ACT-CONS"],
    "P1.PCV01Z": ["D-P1-PC-CONS", "D-P1-ACT-CONS"],
    "P1.PCV02D": ["D-P1-PC-RULE", "D-P1-PC-CONS", "D-P1-ACT-CONS"],
    "P1.PCV02Z": ["D-P1-PC-CONS", "D-P1-ACT-CONS"],
    "P1.B3004": ["D-P1-LC-CONS"],
    "P1.LIT01": ["D-P1-LC-CONS"],
    "P1.LCV01D": ["D-P1-LC-CONS", "D-P1-ACT-CONS"],
    "P1.LCV01Z": ["D-P1-LC-CONS", "D-P1-ACT-CONS"],
    "P1.B3005": ["D-P1-FC-CONS"],
    "P1.FT03": ["D-P1-SENSORS-STAT"],
    "P1.FT03Z": ["D-P1-FC-CONS", "D-P1-LC-CONS"],
    "P1.FCV03D": ["D-P1-FC-CONS", "D-P1-LC-CONS", "D-P1-ACT-CONS"],
    "P1.FCV03Z": ["D-P1-FC-CONS", "D-P1-ACT-CONS"],
    "P1.B4002": ["D-P1-TEMP-RULE"],
    "P1.B4005": ["D-P1-TEMP-RULE", "D-P1-TEMP-CASCADE"],
    "P1.B400B": ["D-P1-TEMP-RULE", "D-P1-TEMP-CASCADE"],
    "P1.B4022": ["D-P1-TEMP-RULE", "D-P1-TEMP-CASCADE"],
    "P1.TIT01": ["D-P1-TEMP-CASCADE", "D-P4-STM-CONS"],
    "P1.FCV01D": ["D-P1-TEMP-CASCADE", "D-P1-ACT-CONS"],
    "P1.FCV01Z": ["D-P1-TEMP-CASCADE", "D-P1-ACT-CONS"],
    "P1.FCV02D": ["D-P1-TEMP-CASCADE", "D-P1-ACT-CONS"],
    "P1.FCV02Z": ["D-P1-TEMP-CASCADE", "D-P1-ACT-CONS"],
    "P1.FT01": ["D-P1-SENSORS-STAT"],
    "P1.FT01Z": ["D-P1-TEMP-CASCADE"],
    "P1.FT02": ["D-P1-SENSORS-STAT"],
    "P1.FT02Z": ["D-P1-TEMP-CASCADE"],
    "P1.PIT02": ["D-P1-SENSORS-STAT"],
    "P1.TIT02": ["D-P1-SENSORS-STAT"],
    "P2.SD01": ["D-P2-SC-CONS", "D-P2-SC-TEMP"],
    "P2.SIT01": ["D-P2-SC-CONS", "D-P2-SC-TEMP", "D-P4-STM-CONS"],
    "P2.VT01": ["D-P2-VIB-ORBIT"],
    "P2.VYT02": ["D-P2-VIB-ORBIT"],
    "P2.VXT02": ["D-P2-VIB-ORBIT"],
    "P2.VYT03": ["D-P2-VIB-ORBIT"],
    "P2.VXT03": ["D-P2-VIB-ORBIT"],
    "P2.24VDC": ["D-P2-PROT-RULE"],
    "P2.Auto": ["D-P2-PROT-RULE"],
    "P2.Emgy": ["D-P2-PROT-RULE"],
    "P2.On": ["D-P2-PROT-RULE"],
    "P2.TripEx": ["D-P2-PROT-RULE"],
    "P3.LT01": ["D-P3-LC-CONS", "D-P3-PROT-RULE", "D-P4-HTM-CONS"],
    "P3.LH01": ["D-P3-PROT-RULE"],
    "P3.LL01": ["D-P3-PROT-RULE"],
    "P3.LCP01D": ["D-P3-LC-CONS", "D-P4-HTM-CONS"],
    "P3.LCV01D": ["D-P3-LC-CONS", "D-P4-HTM-CONS"],
    "P4.LD": ["D-P4-GRID-BALANCE", "D-P4-LOOPBACK-RULE"],
    "P4.ST_FD": ["D-P4-GRID-BALANCE", "D-P4-LOOPBACK-RULE"],
    "P4.ST_PO": ["D-P4-STM-CONS"],
    "P4.ST_PT01": ["D-P4-STM-CONS"],
    "P4.ST_TT01": ["D-P4-STM-CONS"],
    "P4.ST_LD": ["D-P4-GRID-BALANCE", "D-P4-LOOPBACK-RULE", "D-P4-STM-CONS"],
    "P4.ST_PS": ["D-P4-STM-CONS"],
    "P4.HT_FD": ["D-P4-GRID-BALANCE", "D-P4-LOOPBACK-RULE"],
    "P4.HT_PO": ["D-P4-HTM-CONS", "D-P3-LC-CONS"],
    "P4.HT_LD": ["D-P4-GRID-BALANCE", "D-P4-LOOPBACK-RULE", "D-P4-HTM-CONS"],
    "P4.HT_PS": ["D-P4-HTM-CONS"]
  },
  "dependencies": [
    {"source": "D-P1-PC-CONS", "target": "D-P4-STM-CONS", "relationship": "P1 boiler pressure state feeds the steam-turbine model's causal-consistency check"},
    {"source": "D-P1-TEMP-CASCADE", "target": "D-P4-STM-CONS", "relationship": "P1 boiler temperature state feeds the steam-turbine model's causal-consistency check"},
    {"source": "D-P2-SC-CONS", "target": "D-P4-STM-CONS", "relationship": "P2 turbine speed feeds the steam-turbine model's causal-consistency check"},
    {"source": "D-P3-LC-CONS", "target": "D-P4-HTM-CONS", "relationship": "P3 water-treatment level/pump/valve state feeds the hydro-turbine model's causal-consistency check"},
    {"source": "D-P4-STM-CONS", "target": "D-P4-GRID-BALANCE", "relationship": "Steam-side model output participates in overall grid load/frequency balance"},
    {"source": "D-P4-HTM-CONS", "target": "D-P4-GRID-BALANCE", "relationship": "Hydro-side model output participates in overall grid load/frequency balance"},
    {"source": "D-P4-GRID-BALANCE", "target": "D-P1-PC-CONS", "relationship": "P4.ST_LD (derived from grid balance) is a causal input to P1.B2016 setpoint derivation"},
    {"source": "D-P4-GRID-BALANCE", "target": "D-P1-TEMP-CASCADE", "relationship": "P4.ST_LD is a causal input to P1.B4022 setpoint derivation"},
    {"source": "D-P4-GRID-BALANCE", "target": "D-P3-LC-CONS", "relationship": "P4.HT_LD is a causal input to P3 pump/valve demand"},
    {"source": "D-P1-FC-CONS", "target": "D-P1-LC-CONS", "relationship": "Shared actuator (FCV03D) and feedforward signal (FT03Z) couple the flow and level loops"},
    {"source": "D-P2-SC-CONS", "target": "D-P2-VIB-ORBIT", "relationship": "Rotor speed conditions the expected vibration-orbit shape"}
  ],
  "unresolved": [
    "Extended HAI 23.05 / HAIEnd 23.05 tag set (additional ~27 and ~166 points respectively) not available from accessible public metadata.",
    "P1 heating subsystem (PIT02, TIT02) has no documented explicit control loop.",
    "Origin and derivation of P4.LD (exogenous vs. derived) not documented.",
    "Per-tag sampling frequency and statistical ranges not confirmed for the 23.05 release specifically (ranges taken from HAI 1.0 manual).",
    "Actuator response-time bounds for D5 command/feedback detectors require normal-operation data extraction, not provided as input.",
    "HAIEnd internal DCS logic points likely require additional D1/D5 detectors not specifiable without the actual tag list.",
    "Functional form of B2016 = f(B2004, turbine load) and B4022 = f(B4005, B4002, turbine load) is inferred from prose description and requires ICS-expert confirmation before calibration."
  ]
}
```
