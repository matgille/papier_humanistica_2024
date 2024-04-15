import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from bertalign.utils import yield_overlaps
# from sonar.inference_pipelines.text import TextToEmbeddingModelPipeline


class Encoder:
    def __init__(self, model_name):
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        if model_name == "LaBSE":
            self.model = SentenceTransformer(model_name_or_path=model_name, device=device)
            self.model_name = model_name
        else:
            self.t2vec_model = TextToEmbeddingModelPipeline(encoder="text_sonar_basic_encoder",
                                           tokenizer="text_sonar_basic_encoder")
        
    
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
