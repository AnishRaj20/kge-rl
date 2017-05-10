import util
import numpy as np
import os
import constants

class Evaluator(object):
    def __init__(self,model,neg_sampler):
        self.ns = neg_sampler
        self.model = model

    def evaluate(self,batch):
        raise NotImplementedError()


class RankEvaluator(Evaluator):
    def __init__(self,model,neg_sampler):
        super(RankEvaluator,self).__init__(model,neg_sampler)
        self.init_score = float('inf') # because lower the better
        self.metric_name = "Mean Rank"
        self.tol = 0.0

    def comparator(self,curr_score,prev_score):
        # write if curr_score less than prev_score
        return curr_score < prev_score + self.tol

    def evaluate(self,batch):
        s_negs = self.ns.batch_sample(batch, False)
        t_negs = self.ns.batch_sample(batch, True)
        s_scores = self.model.predict(batch,s_negs, False).data.cpu().numpy()
        t_scores = self.model.predict(batch, t_negs,True).data.cpu().numpy()
        s_rank = np.mean(util.ranks(s_scores, ascending=False))
        t_rank = np.mean(util.ranks(t_scores, ascending=False))
        return (s_rank + t_rank)/2.


class TestEvaluator(Evaluator):
    def __init__(self,model,neg_sampler,results_dir):
        super(TestEvaluator,self).__init__(model,neg_sampler)
        self.all_ranks = []
        self.results_dir =results_dir

    def metrics(self,batch,is_target):
        negs = self.ns.batch_sample(batch, is_target)
        scores = self.model.predict(batch, negs, is_target, is_pad=True).data.cpu().numpy()
        ranks = util.ranks(scores, ascending=False)
        self.all_ranks.extend(ranks)
        # self.write_ranks()
        hits_10 = len([x for x in ranks if x <= 10]) / float(len(ranks))
        rr = 1. / np.asarray(ranks)
        return np.mean(rr), hits_10

    def evaluate(self,batch):
        rr_s,hits_s = self.metrics(batch,False)
        rr_t, hits_t = self.metrics(batch, True)
        return (rr_s+rr_t)/2., (hits_s + hits_t)/2.

    def write_ranks(self):
        all_ranks = [str(x) for x in self.all_ranks]
        with open(os.path.join(self.results_dir, 'ranks_checkpoint'), 'w') as f:
            f.write("\n".join(all_ranks))



