import json
import torch
import random
 
random.seed(1234)
 
class Dataset(torch.utils.data.Dataset):
    def __init__(self, file_path, tokenizer, max_len=2048, shuffle=False, max_cnt=None, truncat=True):
        self.data = []
        with open(file_path, 'r') as fp:
            for line in fp.readlines():
                line = json.loads(line)
 
                inputs = tokenizer.encode(line['input'])
                outputs = tokenizer.encode(line['output'] + tokenizer.eos_token)  
                all_input = inputs+outputs
                cur_len = len(all_input)
                if not truncat and cur_len > max_len:
                    continue
                elif cur_len < max_len:
                    input_id = inputs + outputs + [tokenizer.eos_token] * (max_len - cur_len) 
                    label = [-100] * len(inputs) + outputs + [-100] * (max_len - cur_len)
                    attention_mask = [1] * cur_len + [0] * (max_len - cur_len)   
                else:
                    # truncat output
                    input_id = all_input[:max_len]
                    label = ([-100] * len(inputs) + outputs)[:max_len]
                    attention_mask = [1] * max_len
 
                self.data.append({
                        'input_ids': torch.LongTensor(input_id),
                        'labels': torch.LongTensor(label),
                        'attention_mask': torch.tensor(attention_mask)
                    })
        if max_cnt is not None:
            self.data = self.data[: max_cnt]
        if shuffle:
            random.shuffle(self.data)
        if not torch.distributed.is_initialized() or torch.distributed.get_rank() == 0:
            print(file_path, 'loaded:', len(self.data))
 
    def __len__(self):
        return len(self.data)
    def __getitem__(self, index):
        return self.data[index]