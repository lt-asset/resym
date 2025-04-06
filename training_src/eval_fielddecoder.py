import argparse
import json
from typing import List


def safe_division(m,n):
    if n == 0:
        return 0
    else:
        return round(m/n, 4)
         

class Field_counter():
    # eval for perfect match
    def __init__(self):
        self.var_name_correct = 0
        self.var_type_correct = 0
        self.field_name_correct = 0
        self.field_type_correct = 0
        self.total = 0
        
        # metric
        self.var_name_acc = 0
        self.var_type_acc = 0
        self.field_name_acc = 0
        self.field_type_acc = 0

    def inc_total(self, n=1):
        self.total += n
    
    def update(self, label: List, pred: List):
        assert len(label) == 4
        assert len(pred) ==4

        if label[0] == pred[0]:
            self.var_name_correct += 1
        if label[1] == pred[1]:
            self.var_type_correct += 1

        if label[2] == pred[2]:
            self.field_name_correct += 1
        if label[3] == pred[3]:
            self.field_type_correct += 1
       

    def print(self,):
        print(f'var_name_correct: {self.var_name_correct}/ {self.total} = {safe_division(self.var_name_correct, self.total)}')
        print(f'var_type_correct: {self.var_type_correct}/ {self.total} = {safe_division(self.var_type_correct, self.total)}')
        print(f'field_name_correct: {self.field_name_correct}/ {self.total} = {safe_division(self.field_name_correct, self.total)}')
        print(f'field_type_correct: {self.field_type_correct}/ {self.total} = {safe_division(self.field_type_correct, self.total)}')
        


def eval(fpath):
    counter = Field_counter()
    num_mismatch = 0   # prediction mismatch
    with open(fpath, 'r') as fp:
        for i, line in enumerate(fp.readlines()):
        
            line = json.loads(line)
            ground_truth, inference = line['output'], line['predict']
            
            vars_gt = {}
            vars_pred = {}

            try:
                for var in ground_truth.strip().split('\n'):
                    expr, nt = var.split(': ')
                    c1, c2 = nt.split('->')
                    n1, t1 = c1.strip().split(',')
                    n2, t2 = c2.strip().split(',')
                    vars_gt[expr] = [n1.strip(), t1.strip(), n2.strip(), t2.strip()]
                    assert len(vars_gt[expr]) == 4
            except:
                print(f"Ground truth parsing issue with {line['bin']}-{line['fun_id']} {var}")
                continue

            try:
                for var in inference.strip().split('\n'):
                    expr, nt = var.split(': ')
                    c1, c2 = nt.split('->')
                    n1, t1 = c1.strip().split(',')
                    n2, t2 = c2.strip().split(',')
                    vars_pred[expr] = [n1.strip(), t1.strip(), n2.strip(), t2.strip()]
            except:
                num_mismatch += 1
                continue
            if len(vars_gt) != len(vars_pred):
                num_mismatch += 1
            counter.inc_total(len(vars_gt))

            
            for expr in vars_gt:
                if expr not in vars_pred:
                    continue
                if len(vars_pred[expr]) != 4:
                    num_mismatch += 1
                    continue
                counter.update(vars_gt[expr], vars_pred[expr])


    print('#mismatch: '+ str(num_mismatch))
    counter.print()

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('fpath',  help='Path to jsonl file') 
    args = parser.parse_args()

    eval(args.fpath)
 