from openai import OpenAI
import gradio as gr
import pandas as pd
import tqdm
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
class LLMModel:
    def __init__(self, max_docs=2):
        self.max_docs = max_docs
        self.client = OpenAI(api_key=api_key)
    def _get_informative_summary_prompt(self, idx, doc, question):
        return f'''
You are given a document with the following title:
{doc['title']}
The content of the document is as follows:
{doc['body']}
Write a brief one paragraph summary of the document in 
response to the following question:
"{question}"
'''

    def _get_explain_the_reasoning_prompt(self, idx, doc, question):
        return f'''
We are using a search engine to find information on a
articles database. 
The search engine is using a hybrid search with the
HNSW and BM25 algorithms to rank documents.
You are given a document with the following title:
{doc['title']}
The content of the document is as follows:
{doc['body']}
Explain briefly why the search engine returned this document 
at {idx+1} rank in response to the following question:
"{question}"
'''

    def process_docs(self, question, docs, prompt_modifier):
        docs = docs.copy()
        docs['model_answer'] = [None] * docs.shape[0]
        # For the first few documents, generate a response
        for idx, doc in tqdm.tqdm(docs[:self.max_docs].iterrows(), total=docs[:self.max_docs].shape[0]):
            prompt = prompt_modifier(idx, doc, question)
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150
            )
            print(response)
            model_answer = response.choices[0].message.content.strip()
            docs.loc[idx, 'model_answer'] = model_answer
        return docs

    def generate_response(
            self, 
            question: str,
            docs: pd.DataFrame, 
            response_type: str
        ):
        docs['body'] = docs['body'].str[:100] + '...'
        docs['title'] = docs['title'].str.replace('\n', ' ')
        docs['body'] = docs['body'].str.replace('\n', ' ')
        # Generate prompts for the LLM based on response type
        if response_type == 'Informative Summary':
            docs = self.process_docs(
                question, docs, self._get_informative_summary_prompt
            )
            docs.rename(columns={'model_answer': 'summary'}, inplace=True)
        elif response_type == 'Explain the Reasoning':
            docs = self.process_docs(
                question, docs, self._get_explain_the_reasoning_prompt
            )
            docs.rename(columns={'model_answer': 'reasoning'}, inplace=True)
        elif response_type == 'Just Show the Results':
            pass
        return docs.to_dict(orient='records')

# Example usage
if __name__ == "__main__":
    docs = pd.DataFrame({
        'title': ['Document 1', 'Document 2'],
        'relevance': [0.9, 0.85],
        'body': ['This is the body of document 1.', 'This is the body of document 2.']
    })

    model = LLMModel()
    question = "What is the impact of nitrogen-doped porous carbon on energy storage?"
    response_type = "Informative Summary"

    response = model.generate_response(question, docs, response_type)
    print(response)
