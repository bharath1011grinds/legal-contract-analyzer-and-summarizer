# Contract Risk Analyzer 📄⚖️

AI-powered legal contract clause analysis using fine-tuned Llama 3.2 3B with QLoRA.

[![HuggingFace Space](https://img.shields.io/badge/🤗-Demo%20Space-yellow)](https://huggingface.co/spaces/bharathgrinds/legal-contract-analyzer-summarizer-Qlora)
[![Model](https://img.shields.io/badge/🤗-Model-blue)](https://huggingface.co/bharathgrinds/contract-analyzer-and-summarizer-Qlora-checkpoint825)

## Overview

This project fine-tunes Llama 3.2 3B to analyze contract clauses and provide:
- **Risk assessment** (HIGH/MEDIUM/LOW) with context-aware explanations
- **Plain English summaries** for non-legal audiences
- **Jurisdiction-aware analysis** considering governing law and contract context

## Demo

Try it live: [HuggingFace Space](https://huggingface.co/spaces/bharathgrinds/legal-contract-analyzer-summarizer-Qlora)

*Note: Demo runs on CPU (free tier). Inference takes ~3-5 mins seconds. Production deployment uses GPU for 20-30 second responses.*

## Model Details

- **Base Model:** meta-llama/Llama-3.2-3B-Instruct
- **Fine-tuning Method:** QLoRA (4-bit quantization + LoRA adapters)
- **Training Data:** 3,500+ contract clauses from CUAD dataset
- **LoRA Config:** rank=16, alpha=32, ~20M trainable parameters (0.6% of total)
- **Training:** 3 epochs, ~800 steps on 3,900 samples

## Dataset

**CUAD** (Contract Understanding Atticus Dataset)
- 510 commercial contracts from SEC EDGAR filings
- 13,000+ labeled clauses across 41 categories
- Enriched with contract metadata (jurisdiction, parties, key provisions)

## Key Features

### Context-Aware Analysis
Model considers:
- Contract type (Service Agreement, Employment, License, etc.)
- Jurisdiction (Delaware, California, Texas, etc.)
- Key provisions (Liability caps, termination rights, etc.)
- Renewal terms and notice periods

### Example Output

**Input:**
```
Clause: "Employee shall not compete in the software industry 
for two years after termination."
Type: Non-Compete
Jurisdiction: California
```

**Output:**
```
Risk Assessment: LOW

Explanation: California Business & Professions Code §16600 
generally prohibits non-compete agreements for employees. 
This clause is likely unenforceable in California courts, 
significantly reducing risk for the employee.

Plain Summary: You cannot be legally restricted from working 
in the software industry after leaving, as California law 
protects employee mobility.
```

## Technical Approach

### Training Pipeline
1. **Data Preparation:** Extracted 13K+ clauses from CUAD, enriched with contract metadata
2. **Label Generation:** Used Llama 3.3 70B via Groq API to generate risk assessments and summaries
3. **Fine-tuning:** QLoRA on Llama 3.2 3B with instruction masking
4. **Deployment:** HuggingFace Spaces with Gradio interface

### Challenges & Learnings

**Train/Inference Distribution Mismatch:**
- Model was trained with ground-truth clause types in context
- Learned to condition analysis on provided type rather than classify from scratch
- **Solution:** Accept as two-stage system - classification handled separately or by user input

**Token-Level Loss Limitations:**
- Cross-entropy loss treats all tokens equally
- Single risk classification token (HIGH/MEDIUM/LOW) has same weight as 200+ explanation tokens
- Model optimized for fluent explanations over exact classification
- **Result:** ~58% classification accuracy, but high-quality contextual reasoning in explanations

**Context Richness Impact:**
- Model performance heavily dependent on metadata availability
- Rich context (jurisdiction, provisions) → nuanced risk assessment
- Minimal context → defaults to majority class (MEDIUM)


**Key Insight:** Model excels at generating legally sound explanations and plain-language summaries when given proper context, despite moderate exact classification accuracy.


## Installation & Usage

### Local Inference
```python
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load model
model = AutoModelForCausalLM.from_pretrained(
    "bharathgrinds/contract-analyzer-merged",
    torch_dtype=torch.float16,
    device_map="auto"
)

tokenizer = AutoTokenizer.from_pretrained(
    "bharathgrinds/contract-analyzer-merged"
)

# Analyze clause
instruction = """Analyze this clause:
[Your clause text here]
"""

inputs = tokenizer(instruction, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=300)
response = tokenizer.decode(outputs[0], skip_special_tokens=True)

print(response)
```

### Deploy Your Own Space

1. Clone this repo
2. Create HuggingFace Space
3. Upload `app.py` and `requirements.txt`
4. Add `HF_TOKEN` secret (for Llama access)
5. Deploy!

## Future Improvements

- **Separate classification head** for better discrete predictions
- **Task-specific loss weighting** to prioritize classification accuracy
- **Expand training data** to include more diverse jurisdictions
- **Multi-task architecture** to better balance classification vs generation
- **Remove clause type from input** to force true end-to-end classification

## Tech Stack

- **Model:** Llama 3.2 3B, QLoRA/PEFT
- **Training:** Transformers, TRL, BitsAndBytes
- **Deployment:** HuggingFace Spaces, Gradio
- **Infrastructure:** Google Colab (T4 GPU)

## Citation

**CUAD Dataset:**
```
@article{hendrycks2021cuad,
  title={CUAD: An Expert-Annotated NLP Dataset for Legal Contract Review},
  author={Hendrycks, Dan and Burns, Collin and Chen, Anya and Ball, Spencer},
  journal={arXiv preprint arXiv:2103.06268},
  year={2021}
}
```

## License

MIT License - see LICENSE file for details



*Built as a portfolio project demonstrating LLM fine-tuning, prompt engineering, and practical ML deployment.*

