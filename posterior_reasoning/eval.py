import argparse
import json
from tqdm import tqdm
from typing import List, Dict
import os

def normalize_type(type_str):
    if type_str is None:
        return ""
    type_str = type_str.replace('const ', '')
    type_str = type_str.replace('struct ', '')
    type_str = type_str.replace('*', '')
    return type_str.strip()


def read_json(path):
    with open(path, 'r') as f:
        data = json.load(f)
    return data

def safe_division(m,n):
    return m/n if n!=0 else 0

class Evaluator():
    # report accuracy, use perfect match
    def __init__(self):
        self.num_correct = 0
        self.total = 0

    def update(self, label:str, pred:str) -> bool:
        self.total += 1
        if label == pred:
            self.num_correct += 1 
            return True
        return False
        
    def print(self):
        print(f"Accuracy: {self.num_correct}/{self.total} = {round(safe_division(self.num_correct, self.total), 4)}")



class LayoutEvaluator():
    # report precision, recall, and F1
    def __init__(self):
        self.num_correct = 0
        self.num_label = 0
        self.num_pred = 0

        self.recall = 0
        self.precision = 0
        self.f1 = 0
        

    def update(self, ground_truth:Dict, prediction: Dict):
        ground_truth = {int(k): int(v) for k, v in ground_truth.items()}
        prediction = {int(k): int(v) for k, v in prediction.items()}

        self.num_label += len(list(ground_truth.keys()))
        self.num_pred += len(list(prediction.keys()))

        for off, size in prediction.items():
            if off in ground_truth and ground_truth[off] == size:
                self.num_correct += 1

    def eval(self):
        # self.sem_evaluator.eval()
        self.precision = round(safe_division(self.num_correct, self.num_pred), 4)
        self.recall = round(safe_division(self.num_correct, self.num_label), 4)
        self.f1 = round(safe_division(2 * (self.precision * self.recall), (self.precision + self.recall)), 4)

    def print(self,):
        self.eval()
        print(f'Precision: {self.num_correct}/ {self.num_pred} = {self.precision}')
        print(f'Recall: {self.num_correct}/ {self.num_label} = {self.recall}')
        print(f'F1: {self.f1}')
        


def eval(fpath):


    offset_evaluator = LayoutEvaluator()
    struct_type_evaluator = Evaluator()
    field_name_evaluator = Evaluator()
    field_type_evaluator = Evaluator()

    data = read_json(fpath)

    for key, value in tqdm(data.items()):
        pred_type = normalize_type(value['pred']['type'])
        gt_type = normalize_type(value['gt']['type'])


        # offset : size
        pred_offsets = {}  
        gt_offsets = {}

        for offset in value['pred']['offsets']:
            pred_offsets[offset] = value['pred']['offsets'][offset]['size']

        for offset in value['gt']['offsets']:
            gt_offsets[offset] = value['gt']['offsets'][offset]['size']

        assert (len(gt_offsets) > 1 or len(pred_offsets) > 1)

        offset_evaluator.update(gt_offsets, pred_offsets)
        
        if len(gt_offsets.keys())>1:
            struct_type_evaluator.update(pred_type, gt_type)
            for offset in value['gt']['offsets']:
                pred = value['pred']['offsets'].get(offset, {'name': '-', 'type': '-'})
                field_name_evaluator.update(
                    value['gt']['offsets'][offset]['name'],
                    pred['name'],
                    )
                field_type_evaluator.update(
                    value['gt']['offsets'][offset]['type'],
                    pred['type'],
                    )

    print('=========Struct Layout==========')
    offset_evaluator.print()
    print('=========Struct Annotation: Struct Type==========')
    struct_type_evaluator.print()
    print('=========Struct Annotation: Field Name ==========')
    field_name_evaluator.print()
    print('=========Struct Annotation: Field Type ==========')
    field_type_evaluator.print()



if __name__=='__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('results_fpath')
    args = parser.parse_args()

    eval(args.results_fpath,)
