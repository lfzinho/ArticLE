import random
import json
from groq import Groq
from time import sleep
from tqdm import tqdm
import dotenv
import os

dotenv.load_dotenv()

GROQ_API_KEY = os.getenv('GROQ_API_KEY')

client = Groq(
    api_key=GROQ_API_KEY,
)

def generate_query(artigo,
                model    =  'llama3-70b-8192' ,
                max_tokens = 1000 ):
    
    prompt = f"Read the following article, named '{artigo['title']}', and create a search query based on its content. \
        The article's content is as follows: \n {artigo['abstract']}."

    while True:
        try:
            response = client.chat.completions.create(
                model=model,
                n=1,
                messages=[
                    {"role": "system", "content": "You are an assistant AI specialized in creating search queries based on the content of articles. \
                     Your goal is to generate a search query that would be able to find the article you just read. Remember to be concise and clear in your query. \
                     The query should be made as if it were written by a human user, using natural language, and can't be a direct copy of something written in the text. \
                     You should return only the query, without any additional information."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens = max_tokens)

            return response.choices[0].message.content.lower()
        except Exception as e:
            print("Rate limit achieved:", e)
            sleep(30)
            continue

def generate_and_save_queries(sample, num_queries, output_path):
    artigos = []
    # Limit the processing to the first `num_queries` articles
    for artigo in tqdm(sample[:num_queries], desc="Generating queries for articles"):
        query = generate_query(artigo)
        print(f"Article: {artigo['title']}")
        print(f"Query: {query}")
        artigo['query'] = query
        artigos.append(artigo)
        sleep(2)  # simulate some delay
    
    # Use `output_path` to save the file
    with open(output_path, 'w') as f:
        for artigo in artigos:
            artigo['query'] = artigo['query'].replace('"', '').replace("'", "")
            f.write(json.dumps(artigo) + '\n')
        print("\n\n")
