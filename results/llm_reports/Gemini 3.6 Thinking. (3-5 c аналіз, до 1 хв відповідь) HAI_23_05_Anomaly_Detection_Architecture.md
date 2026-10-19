# HAI 23.05 Process-Oriented Anomaly Detection Architecture

**System Overview**
The HAI (HIL-based Augmented ICS) 23.05 dataset encompasses a cyber-physical testbed consisting of four primary interconnected processes:
*   **P1: Boiler Process** (Emerson Ovation DCS) - low pressure, moderate temperature water-to-water heat transfer.
*   **P2: Turbine Process** (GE Mark VIe DCS) - rotor kit simulating an actual rotating machine.
*   **P3: Water Treatment Process** (Siemens S7-300 PLC) - pumping water between upper and lower reservoirs.
*   **P4: HIL Simulation** (dSPACE SCALEXIO) - virtual steam-turbine and pumped-storage hydropower generation, heavily coupled with the physical processes.

This document establishes a process-oriented anomaly detection architecture based strictly on physical, causal, and temporal semantics.

---

## A. Variable Characterization Table

| Tag | Subsystem | Functional Role | Signal Type | Dominant Normal-Behavior Invariant | Recommended Detector Class(es) | Related Variables | Reasoning | Confidence |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `P1_LIT01` | P1 (Boiler) | Drum Level | Process Variable | Physical Consistency | D5, D4 | `P1_LCV01D`, `P1_FIT01` | Water level is intrinsically determined by the mass balance of feedwater flow and evaporation rate. Loop relationship. | High |
| `P1_LCV01D` | P1 (Boiler) | Level Valve Cmd | Control Output | Causal Consistency | D5 | `P1_LIT01`, `P1_FIT01` | Valve position acts as the actuator causally affecting the flow. | High |
| `P1_FIT01` | P1 (Boiler) | Feedwater Flow | Process Variable | Causal Consistency | D5 | `P1_LIT01`, `P1_LCV01D` | Direct flow measurement reflecting the valve output effect. | High |
| `P1_PIT01` | P1 (Boiler) | Boiler Pressure | Process Variable | Multivariate Relationship | D3, D5 | `P4_ST_FD`, `P2_V7322` | Pressure relates to burner operation and dynamic steam extraction demand. | High |
| `P1_B3004` | P1 (Boiler) | Burner Interlock | State | Explicit Logical Constraint | D1 | `P1_PIT01` | Discrete safety logic, strictly defined by valid operational states and protection limits. | High |
| `P2_V7322` | P2 (Turbine) | Turbine Speed | Process Variable | Causal Consistency | D5, D3 | `P2_V7321`, `P4_ST_PO` | Turbine rotational speed is causally driven by valve position and available steam energy. | High |
| `P2_V7321` | P2 (Turbine) | Turbine Valve | Control Output | Causal Consistency | D5 | `P2_V7322`, `P4_ST_FD` | Actuator controlling steam flow to the rotor. | High |
| `P2_VIB_X` | P2 (Turbine) | Rotor Vibration | Process Variable | Statistical Stability | D2 | `P2_V7322` | Normal vibration exhibits statistical variance noise around a stable mean at steady speed. | Medium |
| `P2_S703` | P2 (Turbine) | Turbine Trip | State/Alarm | Explicit Logical Constraint | D1 | `P2_V7322` | Protection trigger state based on over-speed or critical faults. | High |
| `P3_LT01` | P3 (Water) | Reservoir Level | Process Variable | Temporal Dynamics | D4 | `P3_LCP01D`, `P3_FIT01` | Tank level integrates flow over time, representing physical inertia. | High |
| `P3_LCP01D` | P3 (Water) | Pump Command | Control Output | Temporal Dynamics | D4 | `P3_LT01`, `P3_FIT01` | Pump state determines the rate of change in the reservoir over time. | High |
| `P4_ST_PO` | P4 (HIL) | Steam Power Out | Sim Output | Multivariate Relationship | D3, D5 | `P2_V7322`, `P1_PIT01` | Thermodynamic coupling across physical processes and the simulated grid. | High |
| `P2_AUX_VAR`| P2 (Turbine) | Unknown Aux Sensor | Unknown | Insufficient Information | None | Unknown | Metadata missing; cannot infer functional or physical dependencies. | Low |

---

## B. Functional Detector Groups

### Detector `D1_Boiler_Safety`
*   **Detector Class:** D1 (Rule-based detector)
*   **Functional Purpose:** Monitor safety interlock states for illegal transitions and verify protection logic bounding.
*   **Input Variables:** `P1_B3004`, `P1_PIT01`
*   **Process/Subsystem Scope:** P1
*   **Monitored Invariant:** Explicit operational constraints and logical states.
*   **Training/Calibration Requirement:** No training, only predefined rules.
*   **Related Detector Groups:** D3_Thermo_Envelope (to detect condition leading to trip).

### Detector `D1_Turbine_Trip`
*   **Detector Class:** D1 (Rule-based detector)
*   **Functional Purpose:** Monitor the logic of turbine trip sequence based on critical states.
*   **Input Variables:** `P2_S703`, `P2_V7322`
*   **Process/Subsystem Scope:** P2
*   **Monitored Invariant:** Explicit protection limits (e.g., over-speed logic).
*   **Training/Calibration Requirement:** No training, only predefined rules.
*   **Related Detector Groups:** None.

### Detector `D2_Turbine_Vibration`
*   **Detector Class:** D2 (Statistical detector)
*   **Functional Purpose:** Track continuous mechanical health and detect abrupt variance or slow sensor drift.
*   **Input Variables:** `P2_VIB_X`
*   **Process/Subsystem Scope:** P2
*   **Monitored Invariant:** Statistical stability of mechanical oscillation noise at a given setpoint.
*   **Training/Calibration Requirement:** Statistical calibration using normal-operation data.
*   **Related Detector Groups:** None.

### Detector `D3_Thermo_Envelope`
*   **Detector Class:** D3 (Multivariate configuration detector)
*   **Functional Purpose:** Monitor the integrated thermodynamic operating envelope between the boiler, turbine, and simulated grid output.
*   **Input Variables:** `P1_PIT01`, `P2_V7322`, `P4_ST_PO`
*   **Process/Subsystem Scope:** P1, P2, P4
*   **Monitored Invariant:** Valid configurations of coupled thermal-mechanical states (simultaneous relationship).
*   **Training/Calibration Requirement:** Training using normal-operation data (profiling valid multivariable clusters).
*   **Related Detector Groups:** D5_Turbine_Coupling.

### Detector `D4_Reservoir_Dynamics`
*   **Detector Class:** D4 (Temporal-dynamics detector)
*   **Functional Purpose:** Track the integration behavior and temporal lag of the water reservoir responding to pumping actions.
*   **Input Variables:** `P3_LT01`, `P3_LCP01D`, `P3_FIT01`
*   **Process/Subsystem Scope:** P3
*   **Monitored Invariant:** Temporal integration rate, physical inertia, and actuation delays.
*   **Training/Calibration Requirement:** Training using normal-operation data (learning sequential dependencies).
*   **Related Detector Groups:** None.

### Detector `D5_Boiler_Level_Loop`
*   **Detector Class:** D5 (Consistency/residual detector)
*   **Functional Purpose:** Validate tracking performance and causal correlation within the boiler feedwater PID loop.
*   **Input Variables:** `P1_LIT01` (expected output), `P1_LCV01D` (input), `P1_FIT01` (input)
*   **Process/Subsystem Scope:** P1
*   **Monitored Invariant:** Physical causality and functional tracking between controller output, flow rate, and measured level.
*   **Training/Calibration Requirement:** Learning an expected relationship between variables.
*   **Related Detector Groups:** None.

### Detector `D5_Turbine_Coupling`
*   **Detector Class:** D5 (Consistency/residual detector)
*   **Functional Purpose:** Verify cross-process causal linkages (valve position generating expected mechanical speed under specific flow demands).
*   **Input Variables:** `P2_V7321` (input), `P4_ST_FD` (input), `P2_V7322` (expected output)
*   **Process/Subsystem Scope:** P2, P4
*   **Monitored Invariant:** Causal thermodynamic-to-mechanical conversion.
*   **Training/Calibration Requirement:** Learning an expected relationship between variables.
*   **Related Detector Groups:** D3_Thermo_Envelope.

---

## C. Routing Map

*   `P1_LIT01` -> `[D5_Boiler_Level_Loop]`
*   `P1_LCV01D` -> `[D5_Boiler_Level_Loop]`
*   `P1_FIT01` -> `[D5_Boiler_Level_Loop]`
*   `P1_PIT01` -> `[D1_Boiler_Safety, D3_Thermo_Envelope]`
*   `P1_B3004` -> `[D1_Boiler_Safety]`
*   `P2_V7322` -> `[D1_Turbine_Trip, D3_Thermo_Envelope, D5_Turbine_Coupling]`
*   `P2_V7321` -> `[D5_Turbine_Coupling]`
*   `P2_VIB_X` -> `[D2_Turbine_Vibration]`
*   `P2_S703` -> `[D1_Turbine_Trip]`
*   `P3_LT01` -> `[D4_Reservoir_Dynamics]`
*   `P3_LCP01D` -> `[D4_Reservoir_Dynamics]`
*   `P3_FIT01` -> `[D4_Reservoir_Dynamics]`
*   `P4_ST_PO` -> `[D3_Thermo_Envelope]`
*   `P4_ST_FD` -> `[D5_Turbine_Coupling]`

---

## D. Training/Configuration Plan

1.  **D1_Boiler_Safety / D1_Turbine_Trip:**
    *   **Data Extraction:** Extraction of normal data is not strictly necessary for training, but useful for rule validation.
    *   **Configuration:** Requires explicit engineering thresholds and state transition diagrams from the P&ID and DCS logic documentation.
    *   **Inputs:** Binary state tags and primary thresholds.

2.  **D2_Turbine_Vibration:**
    *   **Data Extraction:** Continuous steady-state normal operation periods from the historian.
    *   **Configuration:** Statistical calibration required (e.g., establishing mean and variance boundaries, running standard deviation).
    *   **Inputs:** `P2_VIB_X`. No expected outputs; purely thresholding variance.

3.  **D3_Thermo_Envelope:**
    *   **Data Extraction:** Broad range of normal operation spanning all standard load profiles, start-ups, and shut-downs.
    *   **Configuration:** Model training required (profiling valid multivariate space).
    *   **Inputs:** `P1_PIT01`, `P2_V7322`, `P4_ST_PO`. (Modeled as a joint distribution without explicit inputs vs. outputs).

4.  **D4_Reservoir_Dynamics:**
    *   **Data Extraction:** Transient operations where pump cycles on and off, covering fill/drain cycles.
    *   **Configuration:** Model training required using sliding time-windows.
    *   **Inputs:** `P3_LCP01D`, `P3_FIT01`. **Expected Output:** `P3_LT01`.

5.  **D5_Boiler_Level_Loop & D5_Turbine_Coupling:**
    *   **Data Extraction:** High-frequency historians capturing process dynamics and setpoint tracking.
    *   **Configuration:** Learning an expected relationship (e.g., system identification or residual thresholding).
    *   **Inputs (Boiler):** `P1_LCV01D`, `P1_FIT01`. **Expected Output:** `P1_LIT01`.
    *   **Inputs (Turbine):** `P2_V7321`, `P4_ST_FD`. **Expected Output:** `P2_V7322`.

---

## E. Unresolved Configuration Issues

*   **Missing Semantic Information:** The variable `P2_AUX_VAR` lacks functional description and physical location. It has been excluded from active detector assignment ("Insufficient Information").
*   **Unknown Physical Relationships:** Fluid delay times (pipe inertia/lag) between Pump `P3_LCP01D` activation and flow measurement at `P3_FIT01` are unknown and must be verified by an ICS expert.
*   **Missing Units/Ranges:** The exact engineering operating limits for `P1_PIT01` (pressure bounds) are required to finalize the rules for `D1_Boiler_Safety`.
*   **Assumptions Requiring Validation:** It is assumed that the HIL simulation (`P4_ST_PO`, `P4_ST_FD`) acts dynamically in real-time with negligible network latency compared to physical processes. An ICS expert must validate this to prevent false alarms due to network jitter in cross-subsystem consistency checks.

---

## F. Machine-readable configuration

```json
{
  "detectors": [
    {
      "detector_id": "D1_Boiler_Safety",
      "detector_class": "D1",
      "purpose": "Monitor safety interlock states for illegal transitions",
      "inputs": ["P1_B3004", "P1_PIT01"],
      "monitored_invariant": "Explicit logical constraint",
      "training_requirement": "none",
      "confidence": "high"
    },
    {
      "detector_id": "D1_Turbine_Trip",
      "detector_class": "D1",
      "purpose": "Monitor turbine trip sequence limits",
      "inputs": ["P2_S703", "P2_V7322"],
      "monitored_invariant": "Explicit protection limits",
      "training_requirement": "none",
      "confidence": "high"
    },
    {
      "detector_id": "D2_Turbine_Vibration",
      "detector_class": "D2",
      "purpose": "Detect anomalous mechanical behavior or sensor drift",
      "inputs": ["P2_VIB_X"],
      "monitored_invariant": "Statistical stability",
      "training_requirement": "calibration",
      "confidence": "medium"
    },
    {
      "detector_id": "D3_Thermo_Envelope",
      "detector_class": "D3",
      "purpose": "Monitor thermodynamic operating envelope between boiler, turbine, and simulated grid",
      "inputs": ["P1_PIT01", "P2_V7322", "P4_ST_PO"],
      "monitored_invariant": "Multivariate relationship",
      "training_requirement": "normal-data-training",
      "confidence": "high"
    },
    {
      "detector_id": "D4_Reservoir_Dynamics",
      "detector_class": "D4",
      "purpose": "Monitor temporal integration of reservoir level based on pump activity",
      "inputs": ["P3_LT01", "P3_LCP01D", "P3_FIT01"],
      "monitored_invariant": "Temporal dependency",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D5_Boiler_Level_Loop",
      "detector_class": "D5",
      "purpose": "Track PID loop tracking error and valve-to-flow causality",
      "inputs": ["P1_LIT01", "P1_LCV01D", "P1_FIT01"],
      "monitored_invariant": "Physical or causal consistency",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    },
    {
      "detector_id": "D5_Turbine_Coupling",
      "detector_class": "D5",
      "purpose": "Validates steam valve opening matches expected turbine speed",
      "inputs": ["P2_V7321", "P2_V7322", "P4_ST_FD"],
      "monitored_invariant": "Physical or causal consistency",
      "training_requirement": "relationship-learning",
      "confidence": "high"
    }
  ],
  "routing": {
    "P1_LIT01": ["D5_Boiler_Level_Loop"],
    "P1_LCV01D": ["D5_Boiler_Level_Loop"],
    "P1_FIT01": ["D5_Boiler_Level_Loop"],
    "P1_PIT01": ["D1_Boiler_Safety", "D3_Thermo_Envelope"],
    "P1_B3004": ["D1_Boiler_Safety"],
    "P2_V7322": ["D1_Turbine_Trip", "D3_Thermo_Envelope", "D5_Turbine_Coupling"],
    "P2_V7321": ["D5_Turbine_Coupling"],
    "P2_VIB_X": ["D2_Turbine_Vibration"],
    "P2_S703": ["D1_Turbine_Trip"],
    "P3_LT01": ["D4_Reservoir_Dynamics"],
    "P3_LCP01D": ["D4_Reservoir_Dynamics"],
    "P3_FIT01": ["D4_Reservoir_Dynamics"],
    "P4_ST_PO": ["D3_Thermo_Envelope"],
    "P4_ST_FD": ["D5_Turbine_Coupling"]
  },
  "dependencies": [
    {
      "source": "D5_Boiler_Level_Loop",
      "target": "D3_Thermo_Envelope",
      "relationship": "Boiler loop stability is a prerequisite for maintaining steady thermo-envelope states."
    },
    {
      "source": "D3_Thermo_Envelope",
      "target": "D1_Turbine_Trip",
      "relationship": "Deviations in thermo-envelope typically precede hard protection trips."
    }
  ],
  "unresolved": [
    "Insufficient information on tag P2_AUX_VAR.",
    "Unknown pipe fluid transit lag times for process P3.",
    "Missing exact engineering limit boundaries for P1_PIT01.",
    "Validation of HIL simulation network latency impact on cross-subsystem checks."
  ]
}
```