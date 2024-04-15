import numpy as np

from bertalign.Bertalign import model
import bertalign.corelib as core
import bertalign.utils as utils
import torch.nn as nn
import torch

class Bertalign:
    def __init__(self,
                 src,
                 tgt,
                 max_align=3,
                 top_k=3,
                 win=5,
                 skip=-0.1,
                 margin=True,
                 len_penalty=True,
                 is_split=False,
               ):
        
        self.max_align = max_align
        self.top_k = top_k
        self.win = win
        self.skip = skip
        self.margin = margin
        self.len_penalty = len_penalty
        
    
        
        src_sents = src
        tgt_sents = tgt
        # print(src_sents)
        # print(tgt_sents)
 
        src_num = len(src_sents)
        tgt_num = len(tgt_sents)
        assert len(src_sents) != 0, "Problemo"

        print("Embedding source and target text using {} ...".format(model.model_name))
        src_vecs, src_lens = model.transform(src_sents, max_align - 1)
        tgt_vecs, tgt_lens = model.transform(tgt_sents, max_align - 1)
        
        self.search_simple_vecs = model.simple_vectorization(src_sents)
        self.tgt_simple_vecs = model.simple_vectorization(tgt_sents)

        char_ratio = np.sum(src_lens[0,]) / np.sum(tgt_lens[0,])

        self.src_sents = src_sents
        self.tgt_sents = tgt_sents
        self.src_num = src_num
        self.tgt_num = tgt_num
        self.src_lens = src_lens
        self.tgt_lens = tgt_lens
        self.char_ratio = char_ratio
        self.src_vecs = src_vecs
        self.tgt_vecs = tgt_vecs
    
    def compute_distance(self):
        if torch.cuda.is_available():  # GPU version
            cos = nn.CosineSimilarity(dim=1, eps=1e-6)
            output = cos(torch.from_numpy(self.search_simple_vecs), torch.from_numpy(self.tgt_simple_vecs))
        return output
        
    def align_sents(self, first_alignment_only=False):

        print("Performing first-step alignment ...")
        D, I = core.find_top_k_sents(self.src_vecs[0,:], self.tgt_vecs[0,:], k=self.top_k)
        first_alignment_types = core.get_alignment_types(2) # 0-1, 1-0, 1-1
        first_w, first_path = core.find_first_search_path(self.src_num, self.tgt_num)
        first_pointers = core.first_pass_align(self.src_num, self.tgt_num, first_w, first_path, first_alignment_types, D, I)
        first_alignment = core.first_back_track(self.src_num, self.tgt_num, first_pointers, first_path, first_alignment_types)
        
        print("Performing second-step alignment ...")
        second_alignment_types = core.get_alignment_types(self.max_align)
        second_w, second_path = core.find_second_search_path(first_alignment, self.win, self.src_num, self.tgt_num)
        second_pointers = core.second_pass_align(self.src_vecs, self.tgt_vecs, self.src_lens, self.tgt_lens,
                                            second_w, second_path, second_alignment_types,
                                            self.char_ratio, self.skip, margin=self.margin, len_penalty=self.len_penalty)
        second_alignment = core.second_back_track(self.src_num, self.tgt_num, second_pointers, second_path, second_alignment_types)
        
        if first_alignment_only:
            self.result = first_alignment
        else:
            self.result = second_alignment
    
    def print_sents(self):
        for bead in (self.result):
            src_line = self._get_line(bead[0], self.src_sents)
            tgt_line = self._get_line(bead[1], self.tgt_sents)
            print(bead)
            print(src_line + "\n" + tgt_line + "\n")

    @staticmethod
    def _get_line(bead, lines):
        line = ''
        if len(bead) > 0:
            line = ' '.join(lines[bead[0]:bead[-1]+1])
        return line
