"""Check that every agent uses only variables that exist in the loaded HAI tables"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import config
from src.data_loader import load_hai_data

AGENT_SETS = {
    "SetpointAgent": set(config.SETPOINT_AGENT_VARS),
    "ControlOutputAgent": set(config.CONTROL_OUTPUT_AGENT_VARS),
    "ProtectionAgent": set(config.PROTECTION_AGENT_VARS),
    "ConsistencyAgent": set(config.CONSISTENCY_AGENT_VARS),
    "P1P4SentinelAgent": set(config.P1P4_SENTINEL_AGENT_VARS),
    "LSTMAutoencoderAgent": set(config.LSTM_AGENT_VARS),
}
FINAL = set(config.FINAL_SELECTED_VARS)
RULE_AGENTS_UNION = set().union(*[v for k, v in AGENT_SETS.items() if k != "LSTMAutoencoderAgent"])


def main() -> None:
    data = load_hai_data(
        config.TRAIN_FILES,
        config.TEST_FILES,
        config.LABEL_FILES,
        config.FINAL_SELECTED_VARS,
    )
    available = set(data.available_vars)

    print(f"train rows: {len(data.train):,}, test rows: {len(data.test):,}")
    print(f"train columns == test columns: {set(data.train.columns) == set(data.test.columns)}")
    print(f"FINAL_SELECTED_VARS: {len(FINAL)} configured, {len(available)} found in CSV")
    print(f"missing from CSV: {data.missing_vars or 'none'}")

    print("\nVariables per agent:")
    all_ok = True
    for name, wanted in AGENT_SETS.items():
        missing = sorted(wanted - available)
        all_ok &= not missing
        status = "OK" if not missing else "FAIL"
        print(f"  [{status}] {name:22} config={len(wanted):2}  found={len(wanted & available):2}  missing={missing or '-'}")

    lstm_extra = sorted(AGENT_SETS["LSTMAutoencoderAgent"] - FINAL)
    print(f"\nFINAL_SELECTED_VARS == union of rule agents: {FINAL == RULE_AGENTS_UNION}")
    print(f"LSTM variables outside FINAL_SELECTED_VARS: {lstm_extra or 'none'}")

    print("\nShared P2 variables (by design):")
    p2 = set(config.P2_SPEED_CONTROL_VARS)
    for name in ["SetpointAgent", "ControlOutputAgent", "ConsistencyAgent", "LSTMAutoencoderAgent"]:
        print(f"  {name}: {sorted(p2 & AGENT_SETS[name])}")

    if not (all_ok and not lstm_extra):
        raise SystemExit("\nFix the missing variables first")
    print("\nAll agents use columns from the same loaded tables")


if __name__ == "__main__":
    main()
