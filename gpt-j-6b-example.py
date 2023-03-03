#!/bin/python3
# -*- coding: utf-8 -*-

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

tokenizer = AutoTokenizer.from_pretrained("EleutherAI/gpt-j-6B", cache_dir='./.cache', resume_download=True)

model = AutoModelForCausalLM.from_pretrained(
    "EleutherAI/gpt-j-6B",
    cache_dir='./.cache',
    resume_download=True,
#    torch_dtype=torch.float16,
    low_cpu_mem_usage=True
)

prompt = (
    "In a shocking finding, scientists discovered a herd of unicorns living in a remote, "
    "previously unexplored valley, in the Andes Mountains. Even more surprising to the "
    "researchers was the fact that the unicorns spoke perfect English."
)

input_ids = tokenizer(prompt, return_tensors="pt").input_ids

gen_tokens = model.generate(
    input_ids,
    do_sample=True,
    temperature=0.9,
    max_length=100
)
gen_text = tokenizer.batch_decode(gen_tokens)[0]

print(gen_text)
