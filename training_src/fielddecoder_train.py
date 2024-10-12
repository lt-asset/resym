import torch
from dataset import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
import argparse
from accelerate import Accelerator
from accelerate.utils import DistributedDataParallelKwargs
import os

hf_key = os.environ['HF_TOKEN']



def count_dataset_samples(file_path):
    count = 0
    with open(file_path, 'r') as file:
        for line in file:
            count += 1
    return count

def train(train_fpath, save_dir):
    kwargs = DistributedDataParallelKwargs(static_graph=True, find_unused_parameters=True)
    accelerator = Accelerator(kwargs_handlers=[kwargs])

    tokenizer = AutoTokenizer.from_pretrained('bigcode/starcoderbase-3b', use_auth_token=hf_key)
    model = AutoModelForCausalLM.from_pretrained(
        'bigcode/starcoderbase-3b', use_auth_token=hf_key, torch_dtype=torch.bfloat16
    )
    model.transformer.gradient_checkpointing = True

    train_dataset = Dataset(train_fpath, tokenizer, max_len=4096, shuffle=True)

    dataset_size = count_dataset_samples(train_fpath)
    num_devices = 4
    per_device_train_batch_size = 4
    total_steps_per_epoch = dataset_size / (per_device_train_batch_size * num_devices)  
    num_save_step = round(0.20 * total_steps_per_epoch)



    trainer_args = TrainingArguments(
        output_dir=save_dir,
        per_device_train_batch_size=per_device_train_batch_size,
        learning_rate=5e-5,
        lr_scheduler_type='cosine',
        warmup_steps=500,
        num_train_epochs=1,
        gradient_accumulation_steps=1,
        gradient_checkpointing=True,
        optim='adamw_torch',
        save_strategy='steps',
        save_steps=num_save_step,
        logging_dir='./logs',
        logging_strategy='steps',
        logging_steps=10,
        prediction_loss_only=True,
        bf16=True
    )
    trainer = Trainer(
        model=model, args=trainer_args, train_dataset=train_dataset,
    )

    trainer.train()


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('train_fpath')
    parser.add_argument('save_dir')
    args = parser.parse_args()

    train(args.train_fpath, args.save_dir)