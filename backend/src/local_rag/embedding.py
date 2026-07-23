class Embedder:
    def __init__(self, model_name: str, device: str, batch_size: int) -> None:
        # Imported here because FlagEmbedding pulls torch, which must not load
        # for commands that never embed.
        from FlagEmbedding import BGEM3FlagModel

        self._batch_size = batch_size
        self._model = BGEM3FlagModel(model_name, devices=[device], use_fp16=device != "cpu")

    def encode(self, texts: list[str]) -> tuple[list[list[float]], list[dict[int, float]]]:
        output = self._model.encode(
            texts,
            batch_size=self._batch_size,
            max_length=1024,
            return_dense=True,
            return_sparse=True,
            return_colbert_vecs=False,
        )
        dense = [vector.tolist() for vector in output["dense_vecs"]]
        sparse = [
            {int(token): float(weight) for token, weight in weights.items()}
            for weights in output["lexical_weights"]
        ]
        return dense, sparse
