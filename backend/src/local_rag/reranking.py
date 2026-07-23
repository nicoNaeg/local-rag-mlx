class Reranker:
    def __init__(self, model_name: str, device: str, batch_size: int = 16) -> None:
        # Imported here because torch and transformers must not load for
        # commands that never rerank.
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self._torch = torch
        self._device = device
        self._batch_size = batch_size
        self._tokenizer = AutoTokenizer.from_pretrained(model_name)
        dtype = torch.float16 if device != "cpu" else torch.float32
        model = AutoModelForSequenceClassification.from_pretrained(model_name, dtype=dtype)
        self._model = model.to(device).eval()

    def score(self, query: str, passages: list[str]) -> list[float]:
        scores: list[float] = []
        for start in range(0, len(passages), self._batch_size):
            batch = passages[start : start + self._batch_size]
            encoded = self._tokenizer(
                [query] * len(batch),
                batch,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            ).to(self._device)
            with self._torch.no_grad():
                logits = self._model(**encoded).logits.squeeze(-1)
            scores.extend(self._torch.sigmoid(logits).float().cpu().tolist())
        return scores
