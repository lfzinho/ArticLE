import google.generativeai as genai
import gradio as gr
import pandas as pd
import tqdm
from utils import to_markdown, get_key


class LLMModel:
    def __init__(self, max_docs=2):
        self.max_docs = max_docs
        genai.configure(api_key=get_key())
        self.model = genai.GenerativeModel('gemini-1.5-pro-latest')
    
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
HSNW and BM25 algorithms to rank documents.
You are given a document with the following title:
{doc['title']}
The content of the document is as follows:
{doc['body']}
Explain why the search engine returned this document 
at {idx+1} rank in response to the following question:
"{question}"
'''

    def process_docs(self, question, docs, prompt_modifier):
        partial_response = ''
        docs = docs.copy()
        # For the first few documents, generate a response
        for idx, doc in tqdm.tqdm(docs[:self.max_docs].iterrows()):
            prompt = prompt_modifier(idx, doc, question)
            partial_response += pd.DataFrame(doc).T[['title', 'relevance', 'body']].to_markdown()
            model_answer = self.model.generate_content(prompt).text
            partial_response += f'\n\n{to_markdown(model_answer)}\n\n'
        # For the rest of the documents, just show the results
        docs = docs.iloc[self.max_docs:]
        return partial_response, docs

    def generate_response(
            self, 
            question: str,
            docs: pd.DataFrame, 
            response_type: str
        ):
        response = ''
        docs['body'] = docs['body'].str[:100] + '...'
        docs['title'] = docs['title'].str.replace('\n', ' ')
        docs['body'] = docs['body'].str.replace('\n', ' ')
        # Generate prompts for the LLM based on response type
        match response_type:
            case 'Informative Summary':
                partial_response, docs = self.process_docs(
                    question, docs, self._get_informative_summary_prompt
                )
                response += partial_response
            case 'Explain the Reasoning':
                partial_response, docs = self.process_docs(
                    question, docs, self._get_explain_the_reasoning_prompt
                )
                response += partial_response
            case 'Just Show the Results':
                pass
        response += docs.to_markdown()
        response = f'# Result *({response_type})*\n' + response
        return response
