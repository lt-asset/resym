# ReSym Artifact

This repository provides artifacts for the paper [**"ReSym: Harnessing LLMs to Recover Variable and Data Structure Symbols from Stripped Binaries"**](https://www.cs.purdue.edu/homes/lintan/publications/resym-ccs24.pdf) (CCS 2024).

## Provided Data and Resources

- **Data preparation script**: Located in the `process_data` folder. It generates training data with ground truth symbol information. The script is push-button, and usage instructions are provided in the folder.
- **Binary files and decompiled code**: Available on [Zenodo](https://zenodo.org/records/13917253) (`ReSym_rawdata`). This includes raw binary files and corresponding decompiled code we used in this project:
     - `bin/`: Contains raw **non-stripped binary files** with debugging information.
     - `decompiled/`: Decompiled code from **fully stripped** binaries.
     - `metadata.json`: Metadata for the binaries, including project information.
     - **Note**: You can generate annotations using the provided scripts in this repository.
- **Training/inference scripts**: Found in the `training_src` folder for VarDecoder and FieldDecoder models.
- **Training, testing, and prediction data**: Available on [Zenodo](https://zenodo.org/records/13917253) (`ReSym_data`). This includes:
   - `fielddecoder_train.jsonl`: Training data for the FieldDecoder.
   - `fielddecoder_test.jsonl`: Testing data for the FieldDecoder.
   - `fielddecoder_pred.jsonl`: Prediction results from the FieldDecoder.
   - `vardecoder_train.jsonl`: Training data for the VarDecoder.
   - `vardecoder_test.jsonl`: Testing data for the VarDecoder.
   - `vardecoder_pred.jsonl`: Prediction results from the VarDecoder.
   - `train_proj.json`: List of projects used for training (split by project, as specified in the paper).
   - `test_proj.json`: List of projects used for testing (split by project, as specified in the paper).
- **Model checkpoints**: Fine-tuned VarDecoder and FieldDecoder model checkpoints are available on [Zenodo](https://zenodo.org/records/13917253).
- **Final results**: Posterior reasoning results for recovering user-defined data structures in folder `posterior_reasoning`. The details and instructions can be found int the folder.




## Citing us
```
@article{xie2024resym,
  title={ReSym: Harnessing LLMs to Recover Variable and Data Structure Symbols from Stripped Binaries},
  author={Xie, Danning and Zhang, Zhuo and Jiang, Nan and Xu, Xiangzhe and Tan, Lin and Zhang, Xiangyu},
  year={2024}
}
```
