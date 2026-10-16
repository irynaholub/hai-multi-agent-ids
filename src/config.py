from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT_DIR / "data"
RESULTS_DIR = ROOT_DIR / "results"
FIGURES_DIR = ROOT_DIR / "figures"
MODELS_DIR = ROOT_DIR / "models"

# Files for a quick run on a single train/test pair
TRAIN_FILE = DATA_DIR / "hai-train1.csv"
TEST_FILE = DATA_DIR / "hai-test2.csv"
LABEL_FILE = DATA_DIR / "label-test2.csv"

# Full run: all train files and both test files
# If USE_MULTIPLE_FILES is False, the scripts use the single files above
TRAIN_FILES = [
    DATA_DIR / "hai-train1.csv",
    DATA_DIR / "hai-train2.csv",
    DATA_DIR / "hai-train3.csv",
    DATA_DIR / "hai-train4.csv",
]

TEST_FILES = [
    DATA_DIR / "hai-test1.csv",
    DATA_DIR / "hai-test2.csv",
]

LABEL_FILES = [
    DATA_DIR / "label-test1.csv",
    DATA_DIR / "label-test2.csv",
]

USE_MULTIPLE_FILES = True

RANDOM_STATE = 42

# P2 variables (speed control and protection of the turbine)

P2_SPEED_CONTROL_VARS = [
    "P2_AutoSD",   # speed setpoint, attacked in A224/A232
    "P2_SIT01",    # actual turbine speed, attacked in A228/A232
    "P2_SCO",      # speed controller output, attacked in A228
    "P2_SCST",     # speed change relative to the STM frequency change
]

P2_PROTECTION_VARS = [
    "P2_RTR",      # RPM trip rate
    "P2_VTR01",
    "P2_VTR02",    # vibration trip limits, attacked in A225/A233
    "P2_VTR03",
    "P2_VTR04",
    "P2_VIBTR01",
    "P2_VIBTR02",
    "P2_VIBTR03",
    "P2_VIBTR04",
    "P2_Emerg",
    "P2_TripEx",
]

# P4 variables (steam turbine model)

P4_STEAM_TURBINE_VARS = [
    "P4_ST_PS",     # scheduled power demand
    "P4_ST_GOV",    # governor (gate) opening rate
    "P4_ST_PT01",   # steam pressure
    "P4_ST_TT01",   # steam temperature
]

# P1 variables (boiler side) tied to the target attacks

P1_PROCESS_VARS = [
    # level control: A224, A225, A233
    "P1_LCV01D",
    "P1_LCV01Z",
    "P1_LIT01",

    # pressure control: A228
    "P1_PCV01D",
    "P1_PCV01Z",
    "P1_PIT01",

    # temperature control: A232
    "P1_TIT01",
    "P1_TIT02",
    "P1_TIT03",
    "P1_FCV01D",
    "P1_FCV01Z",
    "P1_FCV02D",
    "P1_FCV02Z",
    "P1_FT02",
]

# Internal P1 controller signals. They are used only if the column exists in the CSV
P1_INTERNAL_OPTIONAL_VARS = [
    "x1002_07_SETPOINT_OUT",
    "x1002_08_SETPOINT_OUT",
    "x1003_10_SETPOINT_OUT",
    "x1003_18_SETPOINT_OUT",
    "x1003_24_SUM_OUT",
]

# Variables for each agent
# SetpointAgent (rules) and ControlOutputAgent (Isolation Forest) share the
# four P2 speed-loop variables, so they vote as one group (see VOTE_AGENT_GROUPS)

SETPOINT_AGENT_VARS = [
    "P2_AutoSD",
    "P2_SIT01",
    "P2_SCO",
    "P2_SCST",
    "P2_VIBTR01",
    "P2_VIBTR02",
    "P2_VIBTR03",
    "P2_VIBTR04",
    "P4_ST_PS",
]

CONTROL_OUTPUT_AGENT_VARS = P2_SPEED_CONTROL_VARS

PROTECTION_AGENT_VARS = P2_PROTECTION_VARS

CONSISTENCY_AGENT_VARS = (
    P1_PROCESS_VARS
    + P1_INTERNAL_OPTIONAL_VARS
    + P4_STEAM_TURBINE_VARS
    + [
        "P2_AutoSD",
        "P2_SIT01",
        "P2_SCO",
        "P2_SCST",
    ]
)

# The sentinel watches P1 and P4 on their own
P1P4_SENTINEL_AGENT_VARS = (
    P1_PROCESS_VARS
    + P4_STEAM_TURBINE_VARS
)
P1P4_SENTINEL_WINDOW_SECONDS = 600
P1P4_SENTINEL_LONG_WINDOW_SECONDS = 3600

# The baseline gets all variables the agents use, so the comparison is fair
FINAL_SELECTED_VARS = sorted(set(
    SETPOINT_AGENT_VARS
    + CONTROL_OUTPUT_AGENT_VARS
    + PROTECTION_AGENT_VARS
    + CONSISTENCY_AGENT_VARS
    + P1P4_SENTINEL_AGENT_VARS
))

# Model parameters

BASELINE_IF_N_ESTIMATORS = 200
BASELINE_IF_CONTAMINATION = 0.05

CONTROL_AGENT_IF_N_ESTIMATORS = 150
CONTROL_AGENT_IF_CONTAMINATION = 0.01

SETPOINT_Z_THRESHOLD = 4.0
SETPOINT_RESIDUAL_QUANTILE = 0.9995

# Drift check: compare the last 30 s with the last 10 min
# Catches slow level shifts like A228 (speed drops from 901 to 839 RPM)
SETPOINT_DRIFT_SHORT_WINDOW = 30   # seconds
SETPOINT_DRIFT_LONG_WINDOW = 600   # seconds

CONSISTENCY_RESIDUAL_QUANTILE = 0.9995

# Thresholds come from the score tail on attack-free train data (EVT/POT)
# Smaller EVT_TAIL_PROB = fewer false alarms, but less of each attack is covered
USE_EVT_THRESHOLD = True
EVT_INIT_LEVEL = 0.99
EVT_TAIL_PROB = 1e-3
EVT_MIN_EXCEEDANCES = 50
EVT_FALLBACK_QUANTILE = 0.9999

# Orchestrator

ORCHESTRATOR_MIN_VOTES = 2

# Protection only confirms an alarm, it does not count as a vote
VOTE_EXCLUDE_AGENTS = ["ProtectionAgent"]

# Agents that look at the same thing vote as one group
USE_VOTE_AGENT_GROUPS = True
VOTE_AGENT_GROUPS = {
    "p2_loop": ["SetpointAgent", "ControlOutputAgent"],
    "temporal": ["LSTMAutoencoderAgent"],
    "consistency": ["ConsistencyAgent", "P1P4SentinelAgent"],
    "protection": ["ProtectionAgent"],
}

# Physics-based paths (see src/orchestrator_physics.py)
EVIDENCE_CHAIN_LAG_SECONDS = 60
EVIDENCE_LSTM_MIN_RUN_SECONDS = 30
EVIDENCE_LSTM_NORM_THRESHOLD = 3.0
EVIDENCE_PO_RESIDUAL_QUANTILE = 0.99

# Hysteresis: stretch a predicted interval while the LSTM score stays above
# a low threshold (1.0 = train 99th percentile). Helps cover long attacks
HYSTERESIS_ANCHOR_AGENT = "LSTMAutoencoderAgent"
HYSTERESIS_LOW_THRESHOLD = 0.5

# Final step (apply_orchestrator_final.py): extend intervals to the left by up
# to 30 s. Helps A225, where the LSTM reacts about 24 s before the other agents
USE_FINAL_ORCHESTRATOR_HYSTERESIS = True
FINAL_HYSTERESIS_MAX_EXTEND = 30
FINAL_HYSTERESIS_EXTEND_RIGHT = False

# LSTM autoencoder agent

USE_LSTM_AGENT = True

LSTM_AGENT_VARS = [
    # P2 speed loop
    "P2_AutoSD",
    "P2_SIT01",
    "P2_SCO",
    "P2_SCST",
    # steam turbine model (A228, A232)
    "P4_ST_PS",
    "P4_ST_GOV",
    "P4_ST_PT01",
    "P4_ST_TT01",
    # boiler side signals (A224, A225, A233)
    "P1_LCV01D",
    "P1_LIT01",
    "P1_PIT01",
    "P1_PCV01D",
    "P1_TIT01",
]

LSTM_WINDOW_SIZE = 90
LSTM_TRAIN_STRIDE = 5
LSTM_PREDICTION_STRIDE = 3
LSTM_HIDDEN_DIM = 64
LSTM_EPOCHS = 15
LSTM_BATCH_SIZE = 128
LSTM_LEARNING_RATE = 1e-3
LSTM_THRESHOLD_QUANTILE = 0.999
LSTM_MAX_TRAIN_WINDOWS = 50000

# eTaPR metric
# THETA_P = 0.5 is the default of the official tool. THETA_P_ALT = 0.1 is a
# softer setting: a predicted interval counts if 10% of it (not 50%) is inside an attack
ETAPR_THETA_P = 0.5
ETAPR_THETA_P_ALT = 0.1
ETAPR_THETA_R = 0.1
ETAPR_DELTA = 0.0
