import numpy as np
import pandas as pd

from sklearn.preprocessing import StandardScaler

from src.thresholding import EVTThresholdResult, apply_threshold, fit_evt_threshold

from .base_agent import AgentOutput, BaseAgent


try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset
except ImportError as exc:
    torch = None
    nn = None
    DataLoader = None
    TensorDataset = None
    TORCH_IMPORT_ERROR = exc
else:
    TORCH_IMPORT_ERROR = None


class _LSTMAutoencoderModel(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int = 32):
        super().__init__()

        self.encoder = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            batch_first=True,
        )

        self.decoder = nn.LSTM(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            batch_first=True,
        )

        self.output_layer = nn.Linear(hidden_dim, input_dim)

    def forward(self, x):
        _, (h, _) = self.encoder(x)

        seq_len = x.shape[1]
        repeated = h[-1].unsqueeze(1).repeat(1, seq_len, 1)

        decoded, _ = self.decoder(repeated)
        reconstructed = self.output_layer(decoded)

        return reconstructed


class LSTMAutoencoderAgent(BaseAgent):
    """LSTM autoencoder: the reconstruction error on sliding windows is the anomaly score"""

    def __init__(
        self,
        variables: list[str],
        window_size: int = 30,
        train_stride: int = 5,
        prediction_stride: int = 3,
        hidden_dim: int = 32,
        epochs: int = 5,
        batch_size: int = 128,
        learning_rate: float = 1e-3,
        threshold_quantile: float = 0.999,
        max_train_windows: int = 30000,
        random_state: int = 42,
        use_evt_threshold: bool = True,
        evt_init_level: float = 0.99,
        evt_tail_prob: float = 1e-4,
        evt_min_exceedances: int = 50,
        evt_fallback_quantile: float = 0.9999,
    ):
        super().__init__("LSTMAutoencoderAgent", variables)

        if torch is None:
            raise ImportError(
                "PyTorch is not installed. Install it with: pip install torch"
            ) from TORCH_IMPORT_ERROR

        self.window_size = window_size
        self.train_stride = train_stride
        self.prediction_stride = prediction_stride
        self.hidden_dim = hidden_dim
        self.epochs = epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.threshold_quantile = threshold_quantile
        self.max_train_windows = max_train_windows
        self.random_state = random_state
        self.use_evt_threshold = use_evt_threshold
        self.evt_init_level = evt_init_level
        self.evt_tail_prob = evt_tail_prob
        self.evt_min_exceedances = evt_min_exceedances
        self.evt_fallback_quantile = evt_fallback_quantile

        self.scaler = StandardScaler()
        self.model = None
        self.threshold_ = None
        self.evt_info_: EVTThresholdResult | None = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def _set_random_seed(self) -> None:
        torch.manual_seed(self.random_state)
        np.random.seed(self.random_state)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.random_state)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False

    def _make_windows(self, arr: np.ndarray, stride: int) -> tuple[np.ndarray, np.ndarray]:
        n = len(arr)

        if n < self.window_size:
            raise ValueError(
                f"{self.name}: data length {n} is smaller than window_size={self.window_size}"
            )

        starts = np.arange(0, n - self.window_size + 1, stride)

        windows = np.empty(
            (len(starts), self.window_size, arr.shape[1]),
            dtype=np.float32,
        )

        for i, start in enumerate(starts):
            windows[i] = arr[start:start + self.window_size]

        return windows, starts

    def _compute_window_errors(self, windows: np.ndarray) -> np.ndarray:
        self.model.eval()

        dataset = TensorDataset(torch.tensor(windows, dtype=torch.float32))
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=False)

        errors = []

        with torch.no_grad():
            for (batch,) in loader:
                batch = batch.to(self.device)
                reconstructed = self.model(batch)

                err = torch.mean((batch - reconstructed) ** 2, dim=(1, 2))
                errors.append(err.detach().cpu().numpy())

        return np.concatenate(errors)

    def fit(self, train: pd.DataFrame) -> "LSTMAutoencoderAgent":
        self._set_random_seed()

        x = self._select_data(train)
        x_scaled = self.scaler.fit_transform(x).astype(np.float32)

        windows, _ = self._make_windows(x_scaled, stride=self.train_stride)

        if len(windows) > self.max_train_windows:
            rng = np.random.default_rng(self.random_state)
            idx = rng.choice(len(windows), size=self.max_train_windows, replace=False)
            windows = windows[idx]

        input_dim = windows.shape[2]

        self.model = _LSTMAutoencoderModel(
            input_dim=input_dim,
            hidden_dim=self.hidden_dim,
        ).to(self.device)

        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.learning_rate)
        criterion = nn.MSELoss()

        dataset = TensorDataset(torch.tensor(windows, dtype=torch.float32))
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

        print(
            f"  LSTM-AE training: windows={len(windows)}, "
            f"window_size={self.window_size}, input_dim={input_dim}, device={self.device}"
        )

        self.model.train()

        for epoch in range(1, self.epochs + 1):
            losses = []

            for (batch,) in loader:
                batch = batch.to(self.device)

                optimizer.zero_grad()
                reconstructed = self.model(batch)
                loss = criterion(reconstructed, batch)
                loss.backward()
                optimizer.step()

                losses.append(float(loss.detach().cpu()))

            print(f"    epoch {epoch}/{self.epochs}, loss={np.mean(losses):.6f}")

        train_errors = self._compute_window_errors(windows)

        if self.use_evt_threshold:
            self.evt_info_ = fit_evt_threshold(
                train_errors,
                init_level=self.evt_init_level,
                tail_prob=self.evt_tail_prob,
                min_exceedances=self.evt_min_exceedances,
                fallback_quantile=self.evt_fallback_quantile,
            )
            self.threshold_ = self.evt_info_.threshold
            print(
                f"  LSTM-AE EVT threshold={self.threshold_:.8f} "
                f"({self.evt_info_.method}, exceedances={self.evt_info_.n_exceedances})"
            )
        else:
            self.threshold_ = float(np.quantile(train_errors, self.threshold_quantile))
            self.threshold_ = max(self.threshold_, 1e-12)
            print(f"  LSTM-AE quantile threshold: {self.threshold_:.8f}")

        return self

    def predict(self, test: pd.DataFrame) -> AgentOutput:
        x = self._select_data(test)
        x_scaled = self.scaler.transform(x).astype(np.float32)

        windows, starts = self._make_windows(x_scaled, stride=self.prediction_stride)
        window_errors = self._compute_window_errors(windows)

        n = len(x)
        sample_scores = np.zeros(n, dtype=float)

        for start, score in zip(starts, window_errors):
            end = start + self.window_size
            sample_scores[start:end] = np.maximum(sample_scores[start:end], score)

        flags = apply_threshold(sample_scores, self.threshold_)

        return AgentOutput(
            name=self.name,
            flags=flags,
            scores=sample_scores,
            variables=self.available_vars,
        )