# ========================================
# NEW CELL: Extract Related Clauses
# ========================================

# Define clause relationships (which clauses provide context for others)
CLAUSE_RELATIONSHIPS = {
    'Non-Compete': ['Exclusivity', 'Competitive Restriction Exception', 'Termination for Convenience'],
    'Exclusivity': ['Non-Compete', 'No-Solicit of Customers'],
    'Cap on Liability': ['Uncapped Liability', 'Liquidated Damages', 'Insurance'],
    'License Grant': ['Non-Transferable License', 'Affiliate IP License-Licensor', 'Irrevocable or Perpetual License'],
    'Expiration Date': ['Renewal Term', 'Notice to Terminate Renewal', 'Effective Date'],
    'Termination for Convenience': ['Notice to Terminate Renewal', 'Post-Termination Services'],
    'Anti-Assignment': ['Change of Control'],
    'IP Ownership Assignment': ['Joint IP Ownership', 'License Grant'],
    # Add more as needed
}

def get_related_clauses(target_clause_type, contract_clauses_df, max_related=3):
    """
    Get semantically related clauses from same contract
    """
    if target_clause_type not in CLAUSE_RELATIONSHIPS:
        return []
    
    related_types = CLAUSE_RELATIONSHIPS[target_clause_type]
    related_clauses = []
    
    for _, clause in contract_clauses_df.iterrows():
        if clause['clause_type'] in related_types:
            related_clauses.append({
                'type': clause['clause_type'],
                'text': clause['clause_text_clean'][:200]  # Truncate for brevity
            })
            
            if len(related_clauses) >= max_related:
                break
    
    return related_clauses

def format_related_context(related_clauses):
    """
    Format related clauses for prompt
    """
    if not related_clauses:
        return ""
    
    context_parts = ["Related Clauses:"]
    for clause in related_clauses:
        context_parts.append(f"- {clause['type']}: {clause['text']}")
    
    return "\n".join(context_parts)

# Test
test_clause = first_contract_clauses[first_contract_clauses['clause_type'] == 'License Grant']
if len(test_clause) > 0:
    related = get_related_clauses('License Grant', first_contract_clauses)
    print("\n=== Testing Related Clause Extraction ===")
    print(f"Target: License Grant")
    print(f"\n{format_related_context(related)}")