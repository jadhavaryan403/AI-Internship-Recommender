import os
import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer
from langchain_core.embeddings import Embeddings
from django.conf import settings


class ONNXEmbeddings(Embeddings):
    def __init__(self, model_path=None):
        if model_path is None:
            model_path = os.path.join(settings.BASE_DIR, "onnx_model")

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            local_files_only=True
        )

        self.session = ort.InferenceSession(
            os.path.join(model_path, "model.onnx")
        )

    def embed_documents(self, texts):
        return self._embed(texts)

    def embed_query(self, text):
        return self._embed([text])[0]

    def _embed(self, texts):
        inputs = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            return_tensors="np"
        )

        ort_inputs = {}
        for input_meta in self.session.get_inputs():
            name = input_meta.name
            ort_inputs[name] = inputs[name]

        outputs = self.session.run(None, ort_inputs)
        token_embeddings = outputs[0]

        attention_mask = inputs["attention_mask"]

        embeddings = np.sum(
            token_embeddings * attention_mask[..., None],
            axis=1
        ) / np.sum(attention_mask, axis=1, keepdims=True)

        return embeddings.tolist()