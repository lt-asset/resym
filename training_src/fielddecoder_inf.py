import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import argparse
from huggingface_hub import login
import os 

hf_key = os.environ['HF_TOKEN']
login(token = token)

def inference(test_fpath, out_fpath, model_path):
    print('==========start loading model==========')
    
    tokenizer = AutoTokenizer.from_pretrained('bigcode/starcoderbase-3b', use_auth_token=hf_key)
    model = AutoModelForCausalLM.from_pretrained(
        model_path, use_auth_token=hf_key,
        torch_dtype=torch.bfloat16, device_map='auto'
    )

    wp = open(out_fpath, 'w')

    with open(test_fpath, 'r') as fp:
        for i, line in enumerate(fp.readlines()):
            line = json.loads(line)
            first_token = line['output'].split(':')[0]
            prompt = line['input'] + first_token + ':'
            input_ids = tokenizer.encode(prompt, return_tensors='pt').cuda()[:, : 8192 - 1024]
            output = model.generate(
                input_ids=input_ids, max_new_tokens=1024, num_beams=4, num_return_sequences=1, do_sample=False,
                early_stopping=False, pad_token_id=tokenizer.eos_token_id, eos_token_id=tokenizer.eos_token_id
            )[0]
            output = tokenizer.decode(output[input_ids.size(1): ], skip_special_tokens=True, clean_up_tokenization_spaces=True)
            output = first_token + ':' + output

            save_data = line
            save_data['predict'] = output
            wp.write(json.dumps(save_data) + '\n')


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('test_fpath')
    parser.add_argument('out_fpath')
    parser.add_argument('model_path')
    args = parser.parse_args()

    inference(args.test_fpath, args.out_fpath, args.model_path)