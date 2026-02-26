import json
import re
from pprint import pprint
import pandas as pd

pd.set_option('display.max_colwidth', None)


def extract_clause_type_from_question(question):

    match = re.search(r'"([^"]+)"', question) #search for the pattern "..."

    if match:
        return match.group(1)
    return "Unknown"

def extract_clauses_from_cuad(cuad_data):

    data = cuad_data['data']

    return_list =[]

    for contract in data:

        for item in contract['paragraphs']:

            for qa in item['qas']:

                if  not qa['is_impossible'] and qa['answers']:
                    for answer in qa['answers']:
                        dict1 = {}
                        clause_type = extract_clause_type_from_question(qa['question'])

                        dict1['contract_name'] = contract['title']
                        dict1['clause_type'] = clause_type
                        dict1['question'] = qa['question']
                        dict1['q_id'] = qa['id']
                        dict1['clause_text'] = answer['text']
                        dict1['full_context'] = item['context']


                        return_list.append(dict1)
    
    return return_list


with open("data/raw/CUAD_v1/CUAD_v1.json", 'r') as f:

    f = json.load(f) 

clauses = extract_clauses_from_cuad(f)


#print('Total Clauses extracted : ', len(clauses))
#print("-----Sample Clause------")
#pprint(clauses[0]['clause_text'])


clause_types = pd.Series(c['clause_type'] for c in clauses)

#print("Clause Type Distribution: ")
#print(clause_types.value_counts())


df = pd.DataFrame(clauses)
word_count = df['clause_text'].apply(lambda x : len(str(x).split()))
df['clause_text_cleaned'] = df['clause_text'].apply(lambda x : ' '.join(x.split())) #removing the extra spaces between words

#print(df['clause_text'][word_count>20].iloc[0][:100])
#print(df['clause_text_cleaned'][word_count>20].iloc[0][:100])
#print((df[['clause_text_cleaned', 'clause_type']][word_count<5]).iloc[:5,])
#print((df[['clause_text_cleaned', 'clause_type']][word_count>20]).iloc[10])
# print(df[['clause_text','clause_text_cleaned']][word_count>20])

'''
print(df.isnull().sum())
contract_name    0
clause_type      0
question         0
q_id             0
clause_text      0
full_context     0
'''

#print(df['q_id'].head())
'''
print(df.shape, df.head(), df.columns.to_list())

shape: (13823, 6)    
columns:['contract_name', 'clause_type', 'question', 'q_id', 'clause_text', 'full_context']

'''

'''
print(len(word_count), max(word_count), min(word_count), sum(word_count)/len(word_count))

Output: 13823 479 1 40.678289806843665


print(df[word_count==1]['clause_text'])
'''

df_final = df[['clause_text_cleaned', 'clause_type', 'contract_name']].copy()
df_final['clause_text_cleaned'] = df_final['clause_text_cleaned'].str.lower()

df_final.to_csv('cuad_cleaned.csv', index = False)

#Extract contract Metadata
clauses_by_contract = df_final.groupby('contract_name').apply(lambda x: list(zip(x['clause_type'] ,x['clause_text_cleaned'] ))).reset_index(name='clause_tuple')
#the above groups by contract_name and creates a new column clause_tuple with a list of tuples, of the format (clause_type, clause_text_cleaned)


#print(clauses_by_contract['clause_tuple'].iloc[0][2])
#print(clauses_by_contract['contract_name'].iloc[0])

#Extracting columns from the master_clauses file to metadata.
new_df = pd.read_csv('data/raw/CUAD_v1/master_clauses.csv', usecols=['Filename', 'Document Name-Answer', 'Agreement Date-Answer', 'Effective Date-Answer',
                                                                     'Expiration Date-Answer','Renewal Term-Answer',
                                                                     'Notice Period To Terminate Renewal- Answer',
                                                                     'Governing Law-Answer'], encoding='cp1252')
new_df['Filename'] = new_df['Filename'].str.replace(r'\.pdf\s*$', '', case=False, regex=True).str.strip()

clauses_by_contract['contract_name'] =clauses_by_contract['contract_name'].str.strip()

#print(clauses_by_contract.columns)
clauses_by_contract['contract_name'] = clauses_by_contract['contract_name'].replace('LECLANCHÉ S.A. - JOINT DEVELOPMENT AND MARKETING AGREEMENT', 'LECLANCH S.A. - JOINT DEVELOPMENT AND MARKETING AGREEMENT')
df_final['contract_name'] = df_final['contract_name'].replace('LECLANCHÉ S.A. - JOINT DEVELOPMENT AND MARKETING AGREEMENT', 'LECLANCH S.A. - JOINT DEVELOPMENT AND MARKETING AGREEMENT')

clauses_by_contract = pd.merge(clauses_by_contract, new_df, left_on='contract_name',
                                right_on= 'Filename', how='inner').drop(columns='Filename')

df_final['contract_name'] = df_final['contract_name'].str.replace(r'\.pdf\s*$', '', case=False, regex=True).str.strip()
#print(clauses_by_contract[clauses_by_contract['_merge'] == 'right_only'][['Filename', 'Expiration Date-Answer']])

#print(clauses_by_contract[clauses_by_contract['_merge'] == 'left_only']['contract_name'])





def extract_contract_metadata(contract_name, clauses_by_contract):
    """Extract all the metadata(clause_type_info) for each contract"""

    metadata = {
        'contract name': contract_name,
        'document name': '',
        #'parties': [],
        'governing law': '',
        #'agreement date': 'Unknown',
        #'effective date': 'Unknown',
        #'expiration date': 'Unknown',
        'renewal term': 'Not Applicable',
        'notice period to terminate renewal' : 'None',
        'termination for convenience': 'None',
        'change of control': 'None',
        'cap on liability': 'None',
        'minimum commitment': 'None'
    }

    row = clauses_by_contract[clauses_by_contract['contract_name']==contract_name]

    clause_tuple = row.iloc[0,1] #1st row 2nd column

    for clause_type, clause_text in clause_tuple:
        
        if clause_type.lower() not in metadata:
            #print(clause_type)
            continue
        if clause_type.lower() == 'document name':
            metadata['document name'] = row.iloc[0]['Document Name-Answer']

        #elif clause_type.lower() == 'parties':
        #   metadata['parties'].append(clause_text)

        elif clause_type.lower() == 'governing law':
            metadata['governing law'] = row.iloc[0]['Governing Law-Answer']

        #elif clause_type.lower() == 'agreement date':
        #    metadata['agreement date'] = row.iloc[0]['Agreement Date-Answer']

        #elif clause_type.lower() == 'effective date':
        #    metadata['effective date'] = row.iloc[0]['Effective Date-Answer']

        #elif clause_type.lower() == 'expiration date':
        #    metadata['expiration date'] = row.iloc[0]['Expiration Date-Answer']

        elif clause_type.lower() == 'renewal term':
            metadata['renewal term'] = row.iloc[0]['Renewal Term-Answer']

        elif clause_type.lower() == 'notice period to terminate renewal':
            metadata['notice period to terminate renewal'] = row.iloc[0]['Notice Period To Terminate Renewal- Answer']
        elif clause_type.lower() in metadata:
            if clause_text:
                metadata[clause_type.lower()] = 'Yes'

    return metadata
        
        
#print(clauses_by_contract.shape)


def format_metadata_context(metadata):
    """Format metadata into clean text for prompt"""
    #Skipping parties, feels like its just gonna add noise

    #Need to process the governing law field to get a single state name.
    context_parts =[]

    if metadata['document name']:
        context_parts.append(f"Contract Type: {metadata['document name']}")

    #if metadata['parties']:
    #    parties_text = '; '.join(metadata['parties'])
    #    context_parts.append(f"Parties Involved: {parties_text}")

    if metadata['governing law']:
        context_parts.append(f"Jurisdiction : {metadata['governing law']}")

    #if metadata['agreement date']:
    #    context_parts.append(f"Date signed: {metadata['agreement date']}")
    
    #if metadata['expiration date']:
    #    context_parts.append(f"Expiration Date: {metadata['expiration date']}")
    
    #if metadata['effective date']:
    #    context_parts.append(f"Effective Date: {metadata['effective date']}")

    if metadata['renewal term']:
        context_parts.append(f"Renewal Term: {metadata['renewal term']}")

    if metadata['notice period to terminate renewal']:
        context_parts.append(f"Notice Period to terminate renewal: {metadata['notice period to terminate renewal']}")
    
    provisions = []

    if metadata['termination for convenience'] != 'None':
        provisions.append('Termination for Convenience')
    if metadata['change of control'] != None:
        provisions.append('Change of Control')
    if metadata['cap on liability'] != None:
        provisions.append('Cap on Liability')
    if metadata['minimum commitment'] != None:
        provisions.append('Minimum Commitment')    

    if provisions:
        context_parts.append(f"Key Provisions: {','.join(provisions)}")

    return ('\n'.join(context_parts))

#metadata = extract_contract_metadata((clauses_by_contract['contract_name'].iloc[90]), clauses_by_contract)
#print(format_metadata__context(metadata))

# ========================================
# NEW CELL: Create Enriched Dataset
# ========================================

def create_enriched_example(clause_row, contract_metadata):
    """
    Combine everything into rich training example
    """
    # Format metadata
    metadata_context = format_metadata_context(contract_metadata)
    
    # Format related clauses, not implemented yet
    #related_context = format_related_context(related_clauses)

#{related_context if related_context else ""} need to add this to full_context once related_context is implemented.
    # Build full context
    full_context = f"""**Contract Context:**
    {metadata_context}

    **Target Clause Type:** {clause_row['clause_type']}
    **Clause Text:**
    {clause_row['clause_text_cleaned']}"""
    
    return {
        'contract_name': clause_row['contract_name'],
        'clause_type': clause_row['clause_type'],
        'clause_text': clause_row['clause_text_cleaned'],
        'enriched_context': full_context,
        'metadata': contract_metadata,
#        'has_related_clauses': len(related_clauses) > 0
    }



# Process ALL contracts
print("Creating enriched dataset...")

enriched_data = []

metadata = {}

for _, row in clauses_by_contract.iterrows():
    # Get all clauses for this contract
    #contract_clauses = df[df['contract_name'] == contract_name]
    
    # Extract metadata once per contract
    metadata[row['contract_name']] = extract_contract_metadata(row['contract_name'], clauses_by_contract)
    

# Process each clause
for idx, clause_row in df_final.iterrows():
    # Skip metadata clauses (they're already in context)
    '''
    if clause_row['clause_type'] in ['Document Name', 'Parties', 'Governing Law', 'Agreement Date']:
        continue
    '''
    
    # Get related clauses
    '''
    related = get_related_clauses(
        clause_row['clause_type'], 
        contract_clauses, 
        max_related=2
    )
    '''

    # Create enriched example
    example = create_enriched_example(clause_row, metadata[clause_row['contract_name']])
    enriched_data.append(example)

# Convert to DataFrame
enriched_df = pd.DataFrame(enriched_data)

print(f" Created {len(enriched_df)} enriched training examples")
#print(f" {enriched_df['has_related_clauses'].sum()} examples have related clause context")

# Save
enriched_df.to_csv('cuad_enriched.csv', index=False)
print(" Saved to cuad_enriched.csv")



