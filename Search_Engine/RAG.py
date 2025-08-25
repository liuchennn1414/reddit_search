from qdrant_client import QdrantClient, models
from datetime import datetime
import pandas as pd 
import numpy as np 
from tqdm import tqdm
import time
import os 
import requests 
import argparse

model_handle = "jinaai/jina-embeddings-v2-small-en"
client = QdrantClient("http://localhost:6333")
collection_name = "reddit_post_comment"

# do search 
def search(query, collection_name, limit=5):


    results = client.query_points(
        collection_name=collection_name,
        query=models.Document( 
            text=query, # query must be text, qdrant will do the embedding for you 
            model=model_handle 
        ),
        limit=limit, # top closest matches
        with_payload=True #to get metadata in the results
    )

    formatted_results = []
    for point in results.points:  # Access points attribute
        formatted_point = {
            'post_title': point.payload['post_title'],
            'post_text': point.payload['post_text'],
            'subreddit': point.payload['subreddit'], 
            'post_url': point.payload['post_url'],
            'post_upvotes': point.payload['post_upvotes'],
            'post_comment': point.payload['post_comment']
        }
        formatted_results.append(formatted_point) 

    return formatted_results

# Build Prompt 
def build_prompt(query, search_results):
    prompt_template = """
You're a reddit summariser. Answer user's question based on the CONTEXT given to you.
If you did not spot useful information, then answer based on your own knowledge. 
Otherwise, use only the facts from the CONTEXT when answering the question.

QUESTION: {question}

CONTEXT: 
{context}
""".strip()

    context = ""

    for doc in search_results:
        context = context + f"title: {doc['post_title']}\ncontent: {doc['post_text']}\ncomment: {doc['post_comment']}\nurl: {doc['post_url']}\nsubreddit: {doc['subreddit']}\npost_upvotes: {doc['post_upvotes']}\n\n"

    prompt = prompt_template.format(question=query, context=context).strip()
    return prompt

os.environ["API_KEY"] = "cannot tell"

def lamma3_groq(prompt):
    api_key = os.getenv('API_KEY') 
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }


    data = {
        "model": "llama3-8b-8192",  # or "llama3-70b-8192" for larger model
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1024
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None


def rag_pipeline(query,collection_name): 
    search_results = search(query,collection_name)
    prompt = build_prompt(query, search_results)
    answer = lamma3_groq(prompt)
    return answer 



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", type=str, help="Question")
    parser.add_argument("--collection_name", type=str, default="reddit_post_comment", help="Knowledge Base")
    args = parser.parse_args()
    result = rag_pipeline(args.query,args.collection_name)
    print(result)