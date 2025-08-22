from qdrant_client import QdrantClient, models
from datetime import datetime
import pandas as pd 
import numpy as np 
from tqdm import tqdm
import time


# Decide which dense encoding model to use 
model_handle = "jinaai/jina-embeddings-v2-small-en"
client = QdrantClient("http://localhost:6333")
reddit_df = pd.read_csv("/workspaces/reddit_search/data/reddit_posts_and_comments.csv")
reddit_df['post_title_text'] = reddit_df['post_title'] + '-' + reddit_df['post_text'] 

# Define the collection name
collection_name = "reddit_post_comment"

client.create_collection(
    collection_name=collection_name,
    vectors_config=models.VectorParams(
        size=512,  # for sentence-transformers embeddings
        distance=models.Distance.COSINE
    ),
    sparse_vectors_config={
        "bm25": models.SparseVectorParams(
            modifier=models.Modifier.IDF,
        )
    }
)


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


filtered_points = []
skipped_empty = 0
truncated_count = 0
id = 0

for idx, row in reddit_df.iterrows():
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

batch_size = 25  # Smaller batches
successful_uploads = 0
failed_batches = []

print(f"\nUploading {len(filtered_points)} points in batches of {batch_size}...")

for i in tqdm(range(0, len(filtered_points), batch_size)):
    try:
        batch = filtered_points[i:i + batch_size]

        client.upsert(
            collection_name="reddit_post_comment",
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

# Verify final count
collection_info = client.get_collection("reddit_post_comment")
print(f"Collection now has {collection_info.points_count} points")


