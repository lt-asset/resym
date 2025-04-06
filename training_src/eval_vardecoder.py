
import argparse
import json
from tqdm import tqdm
from typing import List, Dict, Union, Set

def safe_division(m,n):
    if n == 0:
        return 0
    else:
        return round(m/n, 4)
         

def debug_print(verbose, msg):
    if verbose:
        print(msg)


class Eval_counter():
    # eval for perfect match
    def __init__(self):
        self.name_correct = 0
        self.type_correct = 0
        self.total = 0

        # metric
        self.name_acc = 0
        self.type_acc = 0

    def inc_total(self, n):
        self.total += n
    
    def update(self, label: Dict[str,List], pred: Dict[str,List]):
        all_correct = True
        for var in label:
            if var not in pred:
                continue
            
            this_correct = self.update_var(label[var], pred[var])
            if not this_correct:
                all_correct = False
        
        return all_correct

    def update_var(self, var_label: List[str], var_pred:  Union[None, List[str]]):
        if not var_pred:
            return 

        if var_label[0] == var_pred[0]:
            self.name_correct += 1
        
        if var_label[1] == var_pred[1]:
            self.type_correct += 1


    def eval(self,):
        self.name_acc = safe_division(self.name_correct, self.total)
        self.type_acc = safe_division(self.type_correct, self.total)
        
    def print(self,):
        print(f'name_correct: {self.name_correct}/ {self.total} = {round(safe_division(self.name_correct, self.total), 4)}')
        print(f'type_correct: {self.type_correct}/{self.total} = {round(safe_division(self.type_correct, self.total), 4)}')
     
class Cluster_counter():
    def __init__(self,):
        self.num_correctly_pred = 0
        self.num_cluster = 0   # number of array/struct varibales (v1 v2 v3 -> arr[3] are counted as ONE)
        self.num_pred = 0
        self.precision = 0
        self.recall = 0
        self.f1 = 0
    def print(self, ):
        self.precision = self.num_correctly_pred/self.num_pred
        self.recall = self.num_correctly_pred/self.num_cluster
        self.f1 = safe_division(2 * (self.precision * self.recall), (self.precision + self.recall))
        print(f'precision: {self.num_correctly_pred}/ {self.num_pred} = {self.precision}')
        print(f'recall: {self.num_correctly_pred}/ {self.num_cluster} = {self.recall}')
        print(f'F1: {self.f1}')

class Cluster():
    def __init__(self, head_var:str, all_var:List[str], name:str, tp:str):
        self.head_var = head_var   # v1
        self.all_var = all_var   # v1, v2, v3
        self.name = name   # name of the head var
        self.type = tp
        self.is_struct = self.set_is_struct()

    def set_is_struct(self):
        return self.type.startswith('struct ')
    
    def add_var(self, varname):
        if varname not in self.all_var:
            self.all_var.append(varname)

    def comp_bound(self, other_cluster)-> bool:
        # compare if this cluster and other_cluster have the same boundary
        return self.head_var == other_cluster.head_var and set(self.all_var) == set(other_cluster.all_var) 

    def comp_type(self, other_cluster)-> bool:
        # compare if this cluster and other_cluster have the same type (array/struct)
        return self.is_struct == other_cluster.is_struct

    def comp_perfect_match(self, other_cluster, consider_type:bool)-> bool:
        if consider_type:
            return self.comp_bound(other_cluster) and self.comp_type(other_cluster)
        else:
            return self.comp_bound(other_cluster)

def get_cluster_head(cluster_vars:List[str], gt_var_order:List[str]):
    # cluster_vars: [v2,v1,v3]
    # gt_var_order: [v1, v2, v3, v4, v5 ...]
    # return v1
    first_var = None
    first_var_index = 10000
    for var in cluster_vars:
        if var not in gt_var_order:
            continue
        tmp_var_index = gt_var_order.index(var)
        if tmp_var_index < first_var_index:
            first_var_index = tmp_var_index
            first_var = var 

    return first_var


class Cluster_Evaluator():
    def __init__(self,):
        self.counter = Cluster_counter()
        self.num_pred = 0
    
    def eval(self, vars_gt, vars_pred, gt_var_order, target_varlist, consider_type=True):
        # consider_type: has to correctly predict whether it is an array or struct
        # this eval does not consider name and type name, only consider array/struct and their boundary
        
        gt_var_cluster:Dict[str, Cluster]  = {}  # ground_truth {head_var -> cluster obj}
        # 1. build gt_var_cluster
        for var_list in target_varlist:  # e.g., [v1 v2 v3]
            cluster_head = get_cluster_head(var_list, gt_var_order)
            gt_var_cluster[cluster_head] = Cluster(
                cluster_head, 
                var_list, 
                vars_gt[cluster_head][0],
                vars_gt[cluster_head][1]
                )

        assert len(list(gt_var_cluster.keys()))==len(target_varlist)

        # update counter
        self.counter.num_cluster += len(target_varlist)
        

        # 2. build pred_var_cluster
        pred_var_cluster:Dict[str, Cluster]  = {}  # predicted  {head_var -> cluster obj}
        last_not_dash = None      # the last previous var that is not dash, i.e., the next singleton var
        for var in gt_var_order:  # e.g., v1
            if var not in vars_pred:
                continue
            pred_name, pred_type = vars_pred[var][0], vars_pred[var][1]

            if pred_name == '-':
                if last_not_dash is not None and not last_not_dash.startswith('a'):
                    if last_not_dash not in pred_var_cluster:
                        pred_var_cluster[last_not_dash] = Cluster(
                            last_not_dash,
                            [last_not_dash, var],
                            vars_pred[last_not_dash][0], 
                            vars_pred[last_not_dash][1]
                        )
                    else:
                        pred_var_cluster[last_not_dash].add_var(var)
               
            else:
                last_not_dash = var

        # update counters
        self.counter.num_pred += len(list(pred_var_cluster.keys()))
        

        # 3. update num_correctly_pred
        for pred_head_var, pred_cluster in pred_var_cluster.items():
            for gt_head_var, gt_cluster in gt_var_cluster.items():
                if pred_cluster.comp_perfect_match(gt_cluster, consider_type):
                    self.counter.num_correctly_pred += 1
                    
        self.num_pred += len(list(pred_var_cluster.keys()))
       
        return -1

    def print(self,):
        self.counter.print()
            
def eval(fpath, verbose=True):
    all_counter = Eval_counter()
    cluster_counter = Cluster_Evaluator()

    num_mismatch = 0
    with open(fpath, 'r') as fp:
        for i, line in tqdm(enumerate(fp.readlines())):
            pred_mismatch=False
            gt_mismatch = False
            line = json.loads(line)
            ground_truth, inference = line['output'], line['predict']

            vars_gt = {}  # parsed ground truth
            gt_var_order = []   # variable order
            vars_pred = {}   # parsed prediction

            # 1. parse ground truth
            for var in ground_truth.strip().split('\n'):
                varname, labels = var.split(': ')
                vars_gt[varname] = labels.split(', ')
                gt_var_order.append(varname)
                if len(vars_gt[varname]) != 2:
                    debug_print(verbose, f"Ground truth format issue: {ground_truth}")
                    gt_mismatch = True
                    break

            if gt_mismatch:   # Skip if parsing issue with ground truth 
                continue
            
            # 2. parse prediction
            try:
                for var in inference.strip().split('\n'):
                    varname, labels = var.split(': ')
                    vars_pred[varname] = labels.split(', ')
                    assert len(vars_pred[varname]) == 2

            except Exception as e:
                debug_print(verbose, f"Cannot parse the prediction of {str(line['bin'])}-{str(line['fun_id'])}: {var}")
                num_mismatch += 1
                pred_mismatch=True
                vars_pred = {}
            else:
                if pred_mismatch:
                    vars_pred = {}

                elif len(vars_gt) != len(vars_pred):
                    extra_var = set()   # vars in pred but not in gt
                    for var in vars_pred:
                        if var not in vars_gt:
                            extra_var.add(var)
                    if extra_var:
                        debug_print(verbose, f"Extra variables predicted: {str(line['bin'])}-{str(line['fun_id'])}: {extra_var}")
                        for var in extra_var:
                            vars_pred.pop(var)
                    num_mismatch += 1
                    pred_mismatch = True
            
            # 3. eval all stack variables
            all_counter.inc_total(len(vars_gt))
            all_counter.update(vars_gt, vars_pred)

            # 4. eval cluster variables
            struct_vars, array_vars = [], []
            if 'cluster_var' in line:
                struct_vars = line['cluster_var'].get('struct', [])
                array_vars = line['cluster_var'].get('array', [])

            cluster_counter.eval(vars_gt, vars_pred, gt_var_order, struct_vars+array_vars)


    print("================= Result =================")
    print("mismatch", num_mismatch)
    print("ALL stack variables:")
    all_counter.print()


    print("Cluster variables:")
    cluster_counter.print()

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('fpath', help='path to jsonl file') 
    args = parser.parse_args()

    eval(args.fpath, verbose=True)
