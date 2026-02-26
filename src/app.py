import gradio as gr
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel



base_model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.2-3B-Instruct",
    device_map="auto",
    torch_dtype=torch.float16,
    trust_remote_code=True,
)

#load fine-tuned model
finetuned_model = PeftModel.from_pretrained(base_model, f"https://huggingface.co/bharathgrinds/contract-analyzer-and-summarizer-Qlora", dtype=torch.float16)

tokenizer = AutoTokenizer.from_pretrained(f"https://huggingface.co/bharathgrinds/contract-analyzer-and-summarizer-Qlora", trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = 'right'

#Inference Function:

def analyze_clause(clause_text, contract_type="Service Agreement", jurisdiction="Delaware", renewal_term = "Not Applicable", notice_period = "none",key_provisions = [],
                   target_clause =""):


    instruction = f"""Analyze the following contract clause and provide:
1. Clause Type Classification
2. Risk assessment (HIGH/MEDIUM/LOW) with explanation
3. Plain English summary


**Contract Context:**
Type: {contract_type}
Jurisdiction: {jurisdiction}

**Clause Text:**
{clause_text}

Provide your analysis:"""

    instruction = f"""
  Analyse the following clause and provide:
1. Clause type classification
2. Risk assessment (HIGH/MEDIUM/LOW) with explanation
3. Plain English summary

**Contract Context:**
    Contract Type: {contract_type}
Jurisdiction : {jurisdiction}
Renewal Term: {renewal_term}
Notice Period to terminate renewal: {notice_period}
Key Provisions: {', '.join(key_provisions)}

    **Target Clause Type:** {target_clause}
    **Clause Text:**
      {clause_text}

Provide your analysis:
"""

  #tokenize the inference input
    inputs = tokenizer(instruction, return_tensors = 'pt', truncation = True, max_length = 2048).to(finetuned_model.device)

  #generate
    with torch.no_grad():

      outputs = finetuned_model.generate(**inputs, max_new_tokens = 350, temperature = 0.3, do_sample=True,top_p=0.9, pad_token_id=tokenizer.eos_token_id,
                                         eos_token_id=tokenizer.eos_token_id,)

      full_output = tokenizer.decode(outputs[0], skip_special_tokens = True)


      response = full_output[len(instruction):].strip()

      return response



def analyze_clause_wrapper(clause_text, target_clause, contract_type, jurisdiction,
                          renewal_term, notice_period,
                          has_liability_cap, has_termination, has_change_control, has_minimum_commitment):
    """
    Wrapper to convert UI inputs to your function signature
    """

    if not clause_text.strip():
        return "⚠️ Please enter clause text"

    if target_clause == "Select clause type...":
        return "⚠️ Please select clause type"

    # Build key provisions list
    key_provisions = []
    if has_liability_cap:
        key_provisions.append("Cap on Liability")
    if has_termination:
        key_provisions.append("Termination for Convenience")
    if has_change_control:
        key_provisions.append("Change of Control")
    if has_minimum_commitment:
        key_provisions.append("Minimum Commitment")

    # Call your actual function
    response = analyze_clause(
        clause_text=clause_text,
        contract_type=contract_type,
        jurisdiction=jurisdiction,
        renewal_term=renewal_term,
        notice_period=notice_period,
        key_provisions=key_provisions,
        target_clause=target_clause
    )

    return response


with gr.Blocks(title="Contract Risk Analyzer", theme=gr.themes.Soft()) as demo:

    gr.Markdown("""
    # ⚖️ Contract Risk Analyzer
    ### Context-Aware Legal Clause Analysis

    Fine-tuned Llama 3.2 3B (QLoRA) provides:
    - 🎯 Risk assessment with jurisdiction-aware reasoning
    - 📝 Plain English explanations
    - 🔍 Contract context integration
    """)

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("## 📝 Input")

            clause_input = gr.Textbox(
                label="Contract Clause Text",
                placeholder="Paste your contract clause here...",
                lines=6
            )

            target_clause_input = gr.Dropdown(
                choices=[
                    "Select clause type...",
                    "Non-Compete",
                    "Non-Disparagement",
                    "Covenant Not to Sue",
                    "Exclusivity",
                    "License Grant",
                    "Cap on Liability",
                    "Termination for Convenience",
                    "Change of Control",
                    "Minimum Commitment",
                    "Volume Restriction",
                    "Anti-Assignment",
                    "Post-Termination Services",
                    "Audit Rights",
                    "Insurance",
                    "Renewal Term",
                    "Notice to Terminate Renewal",
                    "IP Ownership Assignment",
                    "No-Solicit of Employees",
                    "Warranty Duration",
                    "Competitive Restriction Exception",
                ],
                value="Select clause type...",
                label="Clause Type",
                allow_custom_value=True
            )

            gr.Markdown("### Contract Context")

            with gr.Row():
                contract_type_input = gr.Dropdown(
                    choices=[
                        "Service Agreement",
                        "Employment Agreement",
                        "License Agreement",
                        "Distribution Agreement",
                        "Distributor Agreement",
                        "Franchise Agreement",
                        "Master Franchise Agreement",
                        "License and Reseller Agreement",
                        "Exclusive License And Product Development Agreement",
                        "NDA",
                        "Other"
                    ],
                    value="Service Agreement",
                    label="Contract Type",
                    allow_custom_value=True
                )

                jurisdiction_input = gr.Dropdown(
                    choices=[
                        "Delaware",
                        "California",
                        "New York",
                        "Texas",
                        "Florida",
                        "Illinois",
                        "Washington",
                        "Ontario, Canada",
                        "British Columbia, Canada",
                        "Other"
                    ],
                    value="Delaware",
                    label="Jurisdiction",
                    allow_custom_value=True
                )

            with gr.Row():
                renewal_term_input = gr.Textbox(
                    label="Renewal Term",
                    placeholder="e.g., 3 years, 6 months, Perpetual",
                    value="Not Applicable"
                )

                notice_period_input = gr.Textbox(
                    label="Notice Period to Terminate",
                    placeholder="e.g., 30 days, 60 days, none",
                    value="none"
                )

            gr.Markdown("### Key Provisions Present")

            with gr.Row():
                has_liability_cap = gr.Checkbox(label="Cap on Liability", value=False)
                has_termination = gr.Checkbox(label="Termination for Convenience", value=False)

            with gr.Row():
                has_change_control = gr.Checkbox(label="Change of Control", value=False)
                has_minimum_commitment = gr.Checkbox(label="Minimum Commitment", value=False)

            analyze_btn = gr.Button("🔍 Analyze Clause", variant="primary", size="lg")

        with gr.Column(scale=1):
            gr.Markdown("## 📊 Analysis")

            output = gr.Textbox(
                label="Model Output",
                lines=16,
                interactive=False,
                show_copy_button=True
            )

    gr.Markdown("## 💡 Real CUAD Dataset Examples")

    gr.Examples(
        examples=[
            [
                # Example 1: Non-Disparagement
                "the franchisee will not directly or indirectly, at any time during the term of this agreement or thereafter, do or cause to be done any act or thing disputing, attacking or in any way impairing the validity of and bkc's right, title or interest in the burger king marks and the burger king system.",
                "Non-Disparagement",
                "Franchise Agreement",
                "Florida",
                "Not Applicable",
                "none",
                True,   # Cap on Liability
                False,  # Termination for Convenience
                True,   # Change of Control
                True    # Minimum Commitment
            ],
            [
                # Example 2: Non-Compete
                "during the term of this agreement, and for a period of two (2) years thereafter, aucta shall not research, develop, manufacture, file, sell, market, or distribute more than two products containing the active ingredient lamotrigine; nor will aucta directly or indirectly assist any other person or entity in carrying or any such activities.",
                "Non-Compete",
                "Exclusive License And Product Development Agreement",
                "Delaware",
                "Not Applicable",
                "none",
                True,   # Cap on Liability
                True,   # Termination for Convenience
                True,   # Change of Control
                True    # Minimum Commitment
            ],
            [
                # Example 3: Covenant Not to Sue
                "franchisee shall not challenge, directly or indirectly, franchisor's interest in, or the validity of, any franchisor property, or any application for registration or trademark registration thereof or any rights of franchisor therein.",
                "Covenant Not to Sue",
                "Master Franchise Agreement",
                "New York",
                "Not Applicable",
                "none",
                True,   # Cap on Liability
                False,  # Termination for Convenience
                True,   # Change of Control
                True    # Minimum Commitment
            ],
            [
                # Example 4: Warranty Duration
                "its products are warranted free from defects of material or workmanship for 3 years after shipment from the manufacturer. equipment purchased from its, which becomes defective within that time period will be repaired by its at its headquarters in san antonio, texas at no cost to comware beyond cost of shipping the equipment to its.",
                "Warranty Duration",
                "Distributor Agreement",
                "Texas",
                "6 months",
                "none",
                True,   # Cap on Liability
                True,   # Termination for Convenience
                True,   # Change of Control
                True    # Minimum Commitment
            ],
            [
                # Example 5: Competitive Restriction Exception
                "for clarity, a competitive transaction shall not include an agreement for use, integration or interfacing, or co-marketing, of the ehave companion solution with other services, solutions, devices, goods or products, where such other services, solutions, devices, goods or products do not contain the same or similar functionality of the ehave companion solution, but provides for a complementary solution.",
                "Competitive Restriction Exception",
                "License and Reseller Agreement",
                "Ontario, Canada",
                "Not Applicable",
                "none",
                True,   # Cap on Liability
                True,   # Termination for Convenience
                True,   # Change of Control
                True    # Minimum Commitment
            ],
        ],
        inputs=[
            clause_input,
            target_clause_input,
            contract_type_input,
            jurisdiction_input,
            renewal_term_input,
            notice_period_input,
            has_liability_cap,
            has_termination,
            has_change_control,
            has_minimum_commitment
        ],
        label="Click any example to load it"
    )

    # Connect button
    analyze_btn.click(
        fn=analyze_clause_wrapper,
        inputs=[
            clause_input,
            target_clause_input,
            contract_type_input,
            jurisdiction_input,
            renewal_term_input,
            notice_period_input,
            has_liability_cap,
            has_termination,
            has_change_control,
            has_minimum_commitment
        ],
        outputs=output
    )

    gr.Markdown("""
    ---
    ### 📚 Project Details

    **Model:**
    - Base: Llama 3.2 3B Instruct
    - Fine-tuning: QLoRA (LoRA rank 16, alpha 32, ~20M trainable params)
    - Training: 3 epochs, 825 steps on 3,900 samples
    - Dataset: CUAD (Contract Understanding Atticus Dataset)

    **Key Learnings:**
    - Model performs best with rich contract context matching training distribution
    - Token-level cross-entropy loss prioritizes explanation fluency over discrete classification
    - Risk assessment quality benefits from jurisdiction and multi-provision context
    - Train/inference distribution alignment is critical for generative task performance

    **Evaluation:**
    - Risk classification: ~55-60% (vs 63% majority baseline)
    - Explanation quality: High (context-aware, legally sound reasoning)
    - Summarization: High (captures key points in plain language)
    """)


demo.queue().launch()


