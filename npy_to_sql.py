import numpy as np
import sqlite3
import pandas as pd
import os
from tqdm.auto import tqdm


def convert_npy_to_sql(npy_path, db_path):
    """
    Convert .npy file containing pairs and measurements to SQLite database.
    
    Args:
        npy_path (str): Path to the .npy file
        db_path (str): Path where the SQLite database will be created
    """
    print(f"Loading data from {npy_path}...")
    
    # Load the .npy file
    loaded_data = np.load(npy_path, allow_pickle=True).item()
    measurements = loaded_data['measurements']
    pairs = loaded_data['pairs']
    
    print(f"Found {len(pairs)} pairs with {len(measurements)} measurements")
    
    # Create SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS protein_pairs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            protein1 TEXT NOT NULL,
            protein2 TEXT NOT NULL,
            score INTEGER NOT NULL
        )
    ''')
    
    # Create indexes for faster querying
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_protein1 ON protein_pairs(protein1)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_protein2 ON protein_pairs(protein2)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_both_proteins ON protein_pairs(protein1, protein2)')
    
    print("Inserting data into database...")
    
    # Insert data in batches for better performance
    batch_size = 10000
    data_to_insert = []
    
    for i, (pair, score) in tqdm(enumerate(zip(pairs, measurements)), total=len(pairs), desc="Inserting data"):
        protein1, protein2 = pair
        data_to_insert.append((protein1, protein2, int(score)))
        
        # Insert in batches
        if len(data_to_insert) >= batch_size:
            cursor.executemany(
                'INSERT INTO protein_pairs (protein1, protein2, score) VALUES (?, ?, ?)',
                data_to_insert
            )
            data_to_insert = []
    
    # Insert remaining data
    if data_to_insert:
        cursor.executemany(
            'INSERT INTO protein_pairs (protein1, protein2, score) VALUES (?, ?, ?)',
            data_to_insert
        )
    
    conn.commit()
    conn.close()
    
    print(f"Database created successfully at {db_path}")


def query_protein_pairs(db_path, protein_name, min_score=None, max_score=None):
    """
    Query the database for all pairs involving a specific protein.
    
    Args:
        db_path (str): Path to the SQLite database
        protein_name (str): The protein name to search for
        min_score (int, optional): Minimum score threshold
        max_score (int, optional): Maximum score threshold
    
    Returns:
        pandas.DataFrame: DataFrame containing all pairs and scores involving the protein
    """
    conn = sqlite3.connect(db_path)
    
    # Build the query
    query = '''
        SELECT protein1, protein2, score
        FROM protein_pairs 
        WHERE protein1 = ? OR protein2 = ?
    '''
    params = [protein_name, protein_name]
    
    # Add score filters if provided
    if min_score is not None:
        query += ' AND score >= ?'
        params.append(min_score)
    
    if max_score is not None:
        query += ' AND score <= ?'
        params.append(max_score)
    
    query += ' ORDER BY score DESC'
    
    # Execute query and return as DataFrame
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    return df


def get_database_stats(db_path):
    """
    Get basic statistics about the database.
    
    Args:
        db_path (str): Path to the SQLite database
    
    Returns:
        dict: Dictionary containing database statistics
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Total number of pairs
    cursor.execute('SELECT COUNT(*) FROM protein_pairs')
    total_pairs = cursor.fetchone()[0]
    
    # Unique proteins
    cursor.execute('SELECT COUNT(DISTINCT protein1) + COUNT(DISTINCT protein2) FROM protein_pairs')
    # More accurate count of unique proteins
    cursor.execute('''
        SELECT COUNT(DISTINCT protein) FROM (
            SELECT protein1 as protein FROM protein_pairs
            UNION
            SELECT protein2 as protein FROM protein_pairs
        )
    ''')
    unique_proteins = cursor.fetchone()[0]
    
    # Score statistics
    cursor.execute('SELECT MIN(score), MAX(score), AVG(score) FROM protein_pairs')
    min_score, max_score, avg_score = cursor.fetchone()
    
    conn.close()
    
    return {
        'total_pairs': total_pairs,
        'unique_proteins': unique_proteins,
        'min_score': min_score,
        'max_score': max_score,
        'avg_score': round(avg_score, 2) if avg_score else None
    }


def search_proteins_by_pattern(db_path, pattern):
    """
    Search for proteins matching a pattern.
    
    Args:
        db_path (str): Path to the SQLite database
        pattern (str): SQL LIKE pattern (use % as wildcard)
    
    Returns:
        list: List of unique proteins matching the pattern
    """
    conn = sqlite3.connect(db_path)
    
    query = '''
        SELECT DISTINCT protein FROM (
            SELECT protein1 as protein FROM protein_pairs WHERE protein1 LIKE ?
            UNION
            SELECT protein2 as protein FROM protein_pairs WHERE protein2 LIKE ?
        ) ORDER BY protein
    '''
    
    df = pd.read_sql_query(query, conn, params=[pattern, pattern])
    conn.close()
    
    return df['protein'].tolist()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert .npy file to SQLite database")
    parser.add_argument("--npy_path", type=str, required=True, help="Path to the .npy file")
    parser.add_argument("--db_path", type=str, required=True, help="Path to the SQLite database")
    args = parser.parse_args()

    npy_path = args.npy_path
    db_path = args.db_path

    if not os.path.exists(db_path):
        print("Converting .npy file to SQLite database...")
        convert_npy_to_sql(npy_path, db_path)
    else:
        print(f"Database already exists at {db_path}")

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
    
    result.to_csv('csv_path.csv', index=False)

    min_score = 50
    print(f"\nExample 2: Query pairs for '{sample_protein}' with score >= {min_score}:")
    result_filtered = query_protein_pairs(db_path, sample_protein, min_score=min_score)
    print(f"Found {len(result_filtered)} with score >= {min_score}")
    if len(result_filtered) > 0:
        print(result_filtered.head())
