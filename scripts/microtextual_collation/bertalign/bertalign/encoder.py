import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from bertalign.bertalign.utils import yield_overlaps


# from sonar.inference_pipelines.text import TextToEmbeddingModelPipeline


class Encoder:
    def __init__(self, model_name):
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        # device = "cpu"
        self.model_name = model_name
    
    def load_model(self):
        print("Start loading model")
        self.model = SentenceTransformer(model_name_or_path=self.model_name, device=self.device)
        print("End loading model")

    def simple_vectorization(self, sents):
        """
        This function produces a simple vectorisation of a sentence, without
        taking into account its lenght as transform does
        """
        sent_vecs = self.model.encode(sents)
        return sent_vecs

    def transform(self, sents, num_overlaps):
        overlaps = []
        for line in yield_overlaps(sents, num_overlaps):
            overlaps.append(line)

        if self.model_name == "LaBSE":
            sent_vecs = self.model.encode(overlaps)
        else:
            sents_vecs = self.t2vec_model.predict()
        embedding_dim = sent_vecs.size // (len(sents) * num_overlaps)
        sent_vecs.resize(num_overlaps, len(sents), embedding_dim)

        len_vecs = [len(line.encode("utf-8")) for line in overlaps]
        len_vecs = np.array(len_vecs)
        len_vecs.resize(num_overlaps, len(sents))

        return sent_vecs, len_vecs
