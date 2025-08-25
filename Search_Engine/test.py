from qdrant_client import QdrantClient, models
from datetime import datetime
import pandas as pd 
import numpy as np 
from tqdm import tqdm
import time
import argparse


def data_preprocessing(df): 
    df['post_title_text'] = df['post_title'] + '-' + df['post_text'] 
    return df 


def create_collection(client, collection_name,dim): 
    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=dim,  # for sentence-transformers embeddings
            distance=models.Distance.COSINE
        ),
        sparse_vectors_config={
            "bm25": models.SparseVectorParams(
                modifier=models.Modifier.IDF,
            )
        }
    )
    return None 


def truncate_text(text, max_length=4000):
    """Truncate text but try to end at sentence boundary."""
    if len(text) <= max_length:
        return text

    # Truncate and try to end at sentence
    truncated = text[:max_length]
    last_period = truncated.rfind('.')
    last_space = truncated.rfind(' ')

    # End at sentence if period found in last 200 chars
    if last_period > max_length - 200:
        return truncated[:last_period + 1]
    # Otherwise end at word boundary
    elif last_space > max_length - 50:
        return truncated[:last_space]
    else:
        return truncated


def create_points(input_df,model_handle): 
    filtered_points = []
    skipped_empty = 0
    truncated_count = 0
    id = 0

    for idx, row in input_df.iterrows():
        # Combine title and text
        title = str(row['post_title']) if pd.notna(row['post_title']) else ""
        text = str(row['post_text']) if pd.notna(row['post_text']) else ""
        comment = str(row['comment_text']) if pd.notna(row['comment_text']) else ""
        combined_text = f"{title}. {text}. {comment}".strip(". ")

        # Skip if essentially empty
        if not combined_text or combined_text == "No content":
            skipped_empty += 1
            continue

        # Truncate if too long
        original_length = len(combined_text)
        combined_text = truncate_text(combined_text, max_length=4000)

        if len(combined_text) < original_length:
            truncated_count += 1

        point = models.PointStruct(
            id=id,
            vector=models.Document(
                text=combined_text, 
                model=model_handle
            ),
            payload={
                "text": combined_text,
                "post_title": title,
                "post_text": str(row['post_text']) if pd.notna(row['post_text']) else "",
                "post_comment": str(row['comment_text']) if pd.notna(row['comment_text']) else "",
                "subreddit": str(row['subreddit']) if pd.notna(row['subreddit']) else "",
                "post_author": str(row['post_author']) if pd.notna(row['post_author']) else "",
                "post_url": str(row['post_url']) if pd.notna(row['post_url']) else "",
                "post_upvotes": int(row['post_upvotes']) if pd.notna(row['post_upvotes']) else 0,
                "post_downvotes": int(row['post_downvotes']) if pd.notna(row['post_downvotes']) else 0,
                "text_length": len(combined_text),
                "was_truncated": len(combined_text) < original_length,
            }
        )
        filtered_points.append(point)
        id += 1
    return filtered_points

def upsert(client, points, collection_name): 
    batch_size = 25  # Smaller batches
    successful_uploads = 0
    failed_batches = []

    print(f"\nUploading {len(points)} points in batches of {batch_size}...")

    for i in tqdm(range(0, len(points), batch_size)):
        try:
            batch = points[i:i + batch_size]

            client.upsert(
                collection_name=collection_name,
                points=batch
            )

            successful_uploads += len(batch)

            # Small delay to prevent overwhelming
            time.sleep(0.2)

        except Exception as e:
            print(f"\n❌ Error uploading batch {i//batch_size + 1}: {e}")
            failed_batches.append(i//batch_size + 1)
            continue

    print(f"\n✅ Upload complete!")
    print(f"Successful uploads: {successful_uploads}")
    print(f"Failed batches: {len(failed_batches)}")
    return None 


# Verify final count
def setup_VD(client, df,collection_name="reddit_post_comment", dim=512, model_handle="jinaai/jina-embeddings-v2-small-en"): 
    df = data_preprocessing(df)
    create_collection(client, collection_name,dim)
    points = create_points(df, model_handle)
    upsert(client, points, collection_name)
    collection_info = client.get_collection(collection_name)
    print(f"Collection now has {collection_info.points_count} points")
    return None 


def main(args): 
    # Decide which dense encoding model to use 
    client = QdrantClient("http://localhost:6333")
    reddit_df = pd.read_csv("/workspaces/reddit_search/data/reddit_posts_and_comments.csv")

    exists = client.collection_exists(collection_name=args.collection_name)

    if exists:
        print(f"Collection '{args.collection_name}' exists.")
        return None 
    else:
        print(f"Collection '{args.collection_name}' does not exist. Creating the new collection")
        setup_VD(client, reddit_df, collection_name=args.collection_name, dim=args.dim, model_handle=args.model_handle)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--collection_name", type=str, default="reddit_post_comment", help="Qdrant collection name")
    parser.add_argument("--dim", type=int, default=512, help="Embedding dimension (default=512)")
    parser.add_argument("--model_handle", type=str, default="jinaai/jina-embeddings-v2-small-en", help="embedding model")
    args = parser.parse_args()
    main(args) 
    
    


