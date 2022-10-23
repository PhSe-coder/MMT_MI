from typing import List
from torch.utils.data import Dataset
from transformers.tokenization_utils import PreTrainedTokenizer
from constants import TAGS
from transformers.utils.generic import PaddingStrategy
import torch

class MyDataset(Dataset):
    def __init__(self, filename, tokenizer: PreTrainedTokenizer, device=None):
        data = []
        with open(filename, "r") as f:
            for line in f:
                line = line.strip()
                text, label = line.split("***")[0:2]
                text_tokens, text_labels = text.split(), label.split()
                assert len(text_tokens) == len(text_labels)
                label_tuplelist = [(text_tokens[i], text_labels[i]) for i in range(len(text_tokens))]
                label_tuplelist_idx, inner_offset = 0, 0
                res = tokenizer(text, padding=PaddingStrategy.MAX_LENGTH, truncation=True)
                input_ids = res.input_ids
                labels: List[str] = []
                for token in tokenizer.convert_ids_to_tokens(input_ids):
                    if token in tokenizer.all_special_tokens:
                        tag = 'SPECIAL_TOKEN'
                    else:
                        label_tuple = label_tuplelist[label_tuplelist_idx]
                        if token.startswith("##"):
                            tag = f'I{labels[-1][1:]}' if labels[-1] not in ["O", "SPECIAL_TOKEN"] else 'O'
                        else:
                            tag = label_tuple[-1]
                            if tag != 'O':
                                tag = f'B{tag[1:]}' if labels[-1] in ["O", "SPECIAL_TOKEN"] else f'I{tag[1:]}'
                        inner_offset += len(token.replace("##", ""))
                        if inner_offset == len(label_tuple[0]):
                            label_tuplelist_idx += 1
                            inner_offset = 0
                    labels.append(tag)
                try:
                    data.append(
                        {
                            "input_ids": torch.as_tensor(input_ids, device=device), 
                            "labels": torch.as_tensor([TAGS.index(label) if label in TAGS else -1 for label in labels], device=device), 
                            "attention_mask": torch.as_tensor(res.attention_mask, device=device),
                            "token_type_ids": torch.as_tensor(res.token_type_ids, device=device)
                        })
                except KeyError as e:
                    print(e)
        self.data = data
        


    def __getitem__(self, index):
        return self.data[index]

    def __len__(self):
        return len(self.data)
