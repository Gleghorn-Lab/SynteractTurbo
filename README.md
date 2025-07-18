# SynteractTurbo

This is a placeholder repository for the SynteractTurbo project. Currently, it contains some basic scripts to index and query SynteractTurbo outputs.

## Usage example


### Get the repository

```bash
git clone 
cd 
pip install -r requirements.txt
```

### Convert the npy to an indexable SQL database

```bash
python npy_to_sql.py --npy_path example_pred_file.npy --db_path example_sql_db.db
```

### Examples querying the database

```python
print("\nDatabase Statistics:")
stats = get_database_stats(db_path)
for key, value in stats.items():
    print(f"  {key}: {value}")

# Example queries
print("\n" + "="*50)
print("EXAMPLE USAGE:")
print("="*50)

# Get a sample protein for demonstration
conn = sqlite3.connect(db_path)
sample_protein = pd.read_sql_query('SELECT protein1 FROM protein_pairs LIMIT 1', conn)['protein1'].iloc[0]
conn.close()

print(f"\nExample 1: Query all pairs for protein '{sample_protein}':")
result = query_protein_pairs(db_path, sample_protein)
print(f"Found {len(result)} pairs involving this protein")
print(result.head())

min_score = 50
print(f"\nExample 2: Query pairs for '{sample_protein}' with score >= {min_score}:")
result_filtered = query_protein_pairs(db_path, sample_protein, min_score=min_score)
print(f"Found {len(result_filtered)} with score >= {min_score}")
if len(result_filtered) > 0:
    print(result_filtered.head())
```

```console
Database Statistics:
  total_pairs: 100000
  unique_proteins: 18758
  min_score: -95
  max_score: 99
  avg_score: 38.43

==================================================
EXAMPLE USAGE:
==================================================

Example 1: Query all pairs for protein 'AVEAYGEFLCMFEENYPETLKRLFVVKAPKLFPVAYNLIKPFLSEDTRKKIMVLGANWKEVLLKHISPDQVPVEYGGTMTDPDGNPKCKSKINYGGDIPRKYYVRDQVKQQYEHSVQISRGSSHQVEYEILFPGCVLRWQFMSDGADVGFGIFLKTKMGERQRAGEMTEVLPNQRYNSHLVPEDGTLTCSDPGICYANEVGEAFRSLVPAAVVWLSYGVASSYVLADAIDKGKKAGEVPSPEAGRSARVTVAVVDTFVWQALASVAIPGFTINRVCAASLYVLGTATRWPLAVRKWTTTALGLLTIPIIIHPIDRSVDFLLDSSLRKLYPTVGKPSSS':
Found 3 pairs involving this protein
                                            protein1                                           protein2  score
0  AVEAYGEFLCMFEENYPETLKRLFVVKAPKLFPVAYNLIKPFLSED...  MNGHLEAEEQQDQRPDQELTGSWGHGPRSTLVRAKAMAPPPPPLAA...     52
1  MSLKNEPRVNTSALQKIAADMSNIIENLDTRELHFEGEEVDYDVSP...  AVEAYGEFLCMFEENYPETLKRLFVVKAPKLFPVAYNLIKPFLSED...     23
2  MGVLLTQRTLLSLVLALLFPSMASMAAIGSCSKEYRVLLGQLQKQT...  AVEAYGEFLCMFEENYPETLKRLFVVKAPKLFPVAYNLIKPFLSED...    -63

Example 2: Query pairs for 'AVEAYGEFLCMFEENYPETLKRLFVVKAPKLFPVAYNLIKPFLSEDTRKKIMVLGANWKEVLLKHISPDQVPVEYGGTMTDPDGNPKCKSKINYGGDIPRKYYVRDQVKQQYEHSVQISRGSSHQVEYEILFPGCVLRWQFMSDGADVGFGIFLKTKMGERQRAGEMTEVLPNQRYNSHLVPEDGTLTCSDPGICYANEVGEAFRSLVPAAVVWLSYGVASSYVLADAIDKGKKAGEVPSPEAGRSARVTVAVVDTFVWQALASVAIPGFTINRVCAASLYVLGTATRWPLAVRKWTTTALGLLTIPIIIHPIDRSVDFLLDSSLRKLYPTVGKPSSS' with score >= 50:
Found 1 with score >= 50
                                            protein1                                           protein2  score
0  AVEAYGEFLCMFEENYPETLKRLFVVKAPKLFPVAYNLIKPFLSED...  MNGHLEAEEQQDQRPDQELTGSWGHGPRSTLVRAKAMAPPPPPLAA...     52
```

### Save query results to csv

```python
result.to_csv('csv_path.csv', index=False)
```

### Interpreting scores

Currently, scores range from -100 to 100, where -100 is a confident non-interacting protein pair and 100 is a confident interacting protein pair. However, the optimal threshold for binary predictions varies based on the model variant. A score of around 50 to threshold positive and negative predictions is typically optimal, but other models skew closer to 0. Reach out to Logan - lhallee@udel.edu - to get the optimal threshold for the checkpoint in question.
