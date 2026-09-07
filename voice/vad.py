"""Voice Activity Detection local do STAR Voice V0.1.

O runtime recebe apenas um caminho local para o modelo ONNX. Download e
verificação do modelo pertencem exclusivamente a ``voice.install_models``.
"""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

import numpy as np

from config import VAD_CONFIG, VAD_MODEL_PATH

ROOT = Path(__file__).resolve().parent.parent
CONTEXT_SAMPLES_16K = 64
STATE_SHAPE = (2, 1, 128)


class VADError(RuntimeError):
    """Erro base do subsistema de VAD."""


class VADModelNotFoundError(VADError):
    """Modelo local não encontrado."""


class VADLoadError(VADError):
    """Falha ao carregar o runtime/modelo ONNX."""


class VADInferenceError(VADError):
    """Falha durante inferência do VAD."""


def default_model_path() -> Path:
    """Retorna o caminho local canônico do modelo Silero VAD."""
    return (ROOT / VAD_MODEL_PATH).resolve()


class SileroVAD:
    """Wrapper numpy-only do Silero VAD v6.2.1 em ONNX Runtime.

    O modelo oficial v6.2.1 usa, a 16 kHz, chunks de 512 amostras e contexto
    recorrente de 64 amostras. O estado LSTM é mantido entre chunks e deve ser
    resetado ao iniciar uma nova fonte/execução.
    """

    def __init__(
        self,
        model_path: str | Path | None = None,
        *,
        sample_rate: int | None = None,
        chunk_samples: int | None = None,
    ) -> None:
        self.model_path = Path(model_path or default_model_path()).resolve()
        self.sample_rate = int(sample_rate or VAD_CONFIG["sample_rate"])
        self.chunk_samples = int(chunk_samples or VAD_CONFIG["chunk_samples"])
        if self.sample_rate != 16000:
            raise ValueError("STAR Voice V0.1 usa Silero VAD em 16 kHz.")
        if self.chunk_samples != 512:
            raise ValueError("Silero VAD v6.2.1 espera chunks de 512 amostras a 16 kHz.")

        self._session: Any | None = None
        self._state = np.zeros(STATE_SHAPE, dtype=np.float32)
        self._context = np.zeros((1, CONTEXT_SAMPLES_16K), dtype=np.float32)
        self._last_probability = 0.0
        self._lock = threading.Lock()

    @property
    def configured(self) -> bool:
        return self.model_path.is_file()

    @property
    def ready(self) -> bool:
        return self._session is not None

    @property
    def last_probability(self) -> float:
        return self._last_probability

    def _create_session(self) -> Any:
        try:
            import onnxruntime as ort
        except ImportError as exc:
            raise VADLoadError(
                "onnxruntime não está instalado. Execute a instalação das dependências da STAR."
            ) from exc

        options = ort.SessionOptions()
        options.inter_op_num_threads = 1
        options.intra_op_num_threads = 1
        options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        try:
            return ort.InferenceSession(
                str(self.model_path),
                sess_options=options,
                providers=["CPUExecutionProvider"],
            )
        except Exception as exc:
            raise VADLoadError(f"Falha ao carregar Silero VAD: {exc}") from exc

    def load(self) -> None:
        """Carrega e valida o modelo local uma única vez."""
        with self._lock:
            if self._session is not None:
                return
            if not self.model_path.is_file():
                raise VADModelNotFoundError(
                    f"Modelo Silero VAD não encontrado em {self.model_path}. "
                    "Execute: python -m voice.install_models"
                )

            # Só publica a sessão como pronta depois de validar o contrato.
            session = self._create_session()
            self._validate_model_contract(session)
            self._session = session
            self._reset_state_unlocked()

    @staticmethod
    def _validate_model_contract(session: Any) -> None:
        input_names = {item.name for item in session.get_inputs()}
        required = {"input", "state", "sr"}
        if not required.issubset(input_names):
            raise VADLoadError(
                f"Modelo ONNX incompatível. Entradas esperadas: {sorted(required)}; "
                f"encontradas: {sorted(input_names)}"
            )

    def _reset_state_unlocked(self) -> None:
        self._state = np.zeros(STATE_SHAPE, dtype=np.float32)
        self._context = np.zeros((1, CONTEXT_SAMPLES_16K), dtype=np.float32)
        self._last_probability = 0.0

    def reset(self) -> None:
        """Reseta estado recorrente sem descarregar o modelo."""
        with self._lock:
            self._reset_state_unlocked()

    def _normalize_chunk(self, chunk: np.ndarray) -> np.ndarray:
        data = np.asarray(chunk, dtype=np.float32)
        if data.ndim == 2 and 1 in data.shape:
            data = data.reshape(-1)
        if data.ndim != 1:
            raise ValueError(f"Chunk VAD deve ser mono/1-D; recebido shape={data.shape}.")
        if data.size != self.chunk_samples:
            raise ValueError(
                f"Chunk VAD deve conter {self.chunk_samples} amostras; recebido {data.size}."
            )
        if not np.isfinite(data).all():
            raise ValueError("Chunk VAD contém valores não finitos.")
        return data

    def process_chunk(self, chunk: np.ndarray) -> float:
        """Processa 32 ms de áudio e retorna probabilidade de fala [0, 1]."""
        data = self._normalize_chunk(chunk)
        self.load()
        with self._lock:
            model_input = np.concatenate((self._context, data.reshape(1, -1)), axis=1)
            inputs = {
                "input": model_input.astype(np.float32, copy=False),
                "state": self._state,
                "sr": np.array(self.sample_rate, dtype=np.int64),
            }
            try:
                output, state = self._session.run(None, inputs)[:2]
            except Exception as exc:
                raise VADInferenceError(f"Falha na inferência Silero VAD: {exc}") from exc

            probability = float(np.asarray(output).reshape(-1)[0])
            if not np.isfinite(probability):
                raise VADInferenceError("Silero VAD retornou probabilidade não finita.")
            self._state = np.asarray(state, dtype=np.float32)
            self._context = model_input[:, -CONTEXT_SAMPLES_16K:].copy()
            self._last_probability = max(0.0, min(1.0, probability))
            return self._last_probability
