"""Agent column names and display names for the dashboard"""

AGENT_COLS = [
    "SetpointAgent_flag",
    "ControlOutputAgent_flag",
    "LSTMAutoencoderAgent_flag",
    "ProtectionAgent_flag",
    "ConsistencyAgent_flag",
    "P1P4SentinelAgent_flag",
]

AGENT_DISPLAY = {
    "SetpointAgent": "Агент уставок",
    "ControlOutputAgent": "Керуючі виходи",
    "LSTMAutoencoderAgent": "LSTM-автоенкодер",
    "ProtectionAgent": "Захист P2",
    "ConsistencyAgent": "Узгодженість P1/P2/P4",
    "P1P4SentinelAgent": "Sentinel P1/P4",
}
