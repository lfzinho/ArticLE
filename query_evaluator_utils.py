from groq import Groq
from time import sleep
from tqdm import tqdm
import json

from AuthKey import GROQ_API_KEY

client = Groq(
    api_key=GROQ_API_KEY,
)

def get_initial_response(prompt: str, model: str = 'llama3-70b-8192', max_tokens: int = 1000):
    """
    prompt: string with the prompt to be used in the completion
    model: string with a valid model name from the GROQ API
    max_tokens: integer with the maximum number of tokens to be used in the completion

    Returns a string with the initial evaluation (0, 1, 2, or 3) given by the LLM
    """
    while True:
        try:
            response = client.chat.completions.create(
                model=model,
                n=1,
                messages=[
                    {"role": "user", "content": "You are an assistant AI specialized in evaluating articles based on a given query. \
                    Your goal is to evaluate an article's relevance based on a search query. You should return only one of the following integers: 0, 1, 2, or 3. \
                    0 means that the article has absolutely no relevance for the query. \
                    1 means that the article is only very slightly relevant to the query, sharing at most a similar topic. \
                    2 means that the article is relevant to the query, sharing many similarities, but it's still not entirely relevant to the query. \
                    3 means that the article is completely relevant to the query. \
                    For example: \n \
                    Read the following article, named 'Increased lifespan on athletes', with the following content: \n Sports practicing has been shown to increase lifespawn and health. \n\
                    Evaluate how relevant the article is to the following query: Positive health impacts on volleyball practice. \n \
                    Response: 2"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens = max_tokens)
            return response.choices[0].message.content.lower()
        except Exception as e:
            print("Error when generating initial response:", e)
            sleep(30)
            continue

def get_feedback(artigo: dict, query: str, response: str, model: str = 'llama3-70b-8192', max_tokens: int = 1000):
    """
    artigo: dictionary with the keys 'title' and 'abstract'
    query: string with the query that the article will be evaluated against
    response: string with the initial response given by the LLM
    model: string with a valid model name from the GROQ API
    max_tokens: integer with the maximum number of tokens to be used in the completion

    Returns a string containing the revised evaluation and the explanation given by the LLM
    """
    while True:
        try:
            feedback = client.chat.completions.create(
                model=model,
                n=1,
                messages=[
                    {"role": "user", "content": f"You are an assistant AI specialized in reevaluating articles based on a given query. \
                    Your goal is to reevaluate the classification given by the previous assistant, about an article's relevance based on a search query. The relevance levels are: \
                    0 means that the article has absolutely no relevance for the query. \
                    1 means that the article is only very slightly relevant to the query, sharing at most a similar topic. \
                    2 means that the article is relevant to the query, sharing many similarities, but it's still not entirely relevant to the query. \
                    3 means that the article is completely relevant to the query. \
                    The article, titled '{artigo['title']}', has the following content: \n {artigo['abstract']} \n \
                    The query is: {query} \n \
                    The previous evaluation is: {response} \n \
                    Do you agree with the previous evaluation? \
                    Try to avoid extreme answers like 0 or 3 unless you are sure that is the case. \
                    Write your answer in the following json structure, where 'explanation' represents your reasoning, and 'eval' represents your evaluation: \n \
                    {{\"explanation\": \"your explanation\", \"eval\": \"your evaluation, needs to be exactly 0, 1, 2, or 3.\"\}}"}
                ],
                max_tokens = max_tokens)
            return feedback.choices[0].message.content.lower()
        except Exception as e:
            print("Error when generating feedback:", e)
            sleep(30)
            continue

def get_feedback_json(artigo: dict, query: str, response: str, model: str = 'llama3-70b-8192', max_tokens: int = 1000):
    """
    artigo: dictionary with the keys 'title' and 'abstract'
    query: string with the query that the article will be evaluated against
    response: string with the initial response given by the LLM
    model: string with a valid model name from the GROQ API
    max_tokens: integer with the maximum number of tokens to be used in the completion

    Converts the string given by the get_feedback function into a dictionary, and checks if the 'eval' key is a valid integer

    Returns a dictionary with the keys 'explanation' and 'eval' where 'eval' is an integer from 0 to 3
    """
    while True:
        try:
            feedback = get_feedback(artigo, query, response, model, max_tokens)
            dict = json.loads(feedback)
            dict['eval'] = int(dict['eval'])
            if dict['eval'] in [0, 1, 2, 3]:
                return dict
            else:
                raise Exception("Invalid evaluation: ", dict['eval'])
        except Exception as e:
            print("Error when parsing feedback:", e)

def evaluate_articles_levels(artigos: list, 
                      query: str,
                      model: str = 'llama3-70b-8192',
                      max_tokens: int = 1000,
                      verbose: bool = True):
    """
    artigos: list of dictionaries with the following keys: 'title', 'abstract'
    query: string with the query that the articles will be evaluated against
    model: string with a valid model name from the GROQ API
    max_tokens: integer with the maximum number of tokens to be used in the completion
    verbose: boolean to print the evaluation process

    Returns a list of dictionaries with the following keys: 'title', 'abstract', 'eval', 'explanation',
    where 'eval' is an integer from 0 to 3 where 0 means no relevance, 1 is very slightly relevant,
    2 is relevant, and 3 means completely relevant to the query, and 'explanation' is a string with the reasoning behind the evaluation    
    """

    evaluated = []
    if verbose: print("Query:", query)

    for artigo in tqdm(artigos, desc="Evaluating articles"):
        prompt = f"Read the following article, named '{artigo['title']}', with the following content: \n {artigo['abstract']} \n \
                Evaluate how relevant the article is to the following query: {query} \n"

        response = get_initial_response(prompt, model, max_tokens)

        feedback = get_feedback_json(artigo, query, response, model, max_tokens)
        
        if verbose: print(f"Article: '{artigo['title']}'\n Classification: {feedback}")
        evaluated.append({'title': artigo['title'], 'abstract': artigo['abstract'], 'eval': feedback['eval'], 'explanation': feedback['explanation']})
    return evaluated

def evaluate_articles_boolean(artigos: list, 
                      query: str,
                      model: str = 'llama3-70b-8192',
                      max_tokens: int = 1000,
                      verbose: bool = True):
    """
    artigos: list of dictionaries with the following keys: 'title', 'abstract'
    query: string with the query that the articles will be evaluated against
    model: string with a valid model name from the GROQ API
    max_tokens: integer with the maximum number of tokens to be used in the completion
    verbose: boolean to print the evaluation process

    Returns a list of dictionaries with the following keys: 'title', 'abstract', 'eval', where 'eval' is a boolean value where 1 means relevant and 0 means not relevant to the query    
    """

    evaluated = []
    if verbose: print("Query:", query)

    for artigo in tqdm(artigos, desc="Evaluating articles"):
        prompt = f"Read the following article, named '{artigo['title']}', with the following content: \n {artigo['abstract']} \n \
                Evaluate if the article is relevant to the following query, and don't be strict about your classification: {query} \n"

        while True:
            try:
                response = client.chat.completions.create(
                    model=model,
                    n=1,
                    messages=[
                        {"role": "user", "content": "You are an assistant AI specialized in evaluating articles based on a given query. \
                        Your goal is to evaluate an article's relevance based on a search query. You should return only the number 1 or 0, where 1 means true and 0 means false, \
                        based on whether the article is at least slightly relevant to a given query. If the article is related to the same field, it is enough for it to be considered relevant. For example: \n \
                        Read the following article, named 'Increased lifespan on athletes', with the following content: \n Sports practicing has been shown to increase lifespawn and health. \n\
                        Evaluate if the article is relevant to the following query: Positive health impacts on volleyball practice. \n \
                        Response: 1"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens = max_tokens)
                if int(response.choices[0].message.content.lower()) in [0, 1]:
                    evaluated.append({'title': artigo['title'], 'abstract': artigo['abstract'], 'eval': response.choices[0].message.content.lower()})
                    if verbose: print(f"Article '{artigo['title']}' evaluated as {response.choices[0].message.content.lower()}")
                    break
                else:
                    print("Invalid response, trying again.")
            except Exception as e:
                print("Rate limit achieved:", e)
                sleep(30)
                continue
    return evaluated