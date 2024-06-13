from typing import Callable, Literal

import pandas as pd
import tqdm
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class LLM:
    def __init__(self, max_docs: int = 2, api_key: str | None = None) -> None:
        self.max_docs = max_docs
        self.client = OpenAI(api_key=api_key)

    @staticmethod
    def _get_context_string(title: str, body: str) -> str:
        return (
            f"You are given a document with the following title:\n{title}\n"
            f"The content of the document is as follows:\n{body}\n"
        )

    def _get_informative_summary_prompt(
        self,
        index,
        doc: dict[str, str],
        question: str
    ) -> str:
        return (
            self._get_context_string(doc["title"], doc["body"]) +
            "Write a brief one paragraph summary of the document in "
            f"response to the following question:\n\"{question}\""
        )

    def _get_explain_the_reasoning_prompt(
        self,
        index: int,
        doc: dict[str, str],
        question: str
    ) -> str:
        return (
            "We are using a search engine to find information on an article database."
            "The search engine is using a hybrid serach with the "
            "HNSW and BM25 algorithms to rank documents.\n" +
            self._get_context_string(doc['title'], doc['body']) +
            "\nExplain briefly why the search engine returned this document "
            f"at rank {index + 1} in response to the following question:\n\"{question}\""
        )

    def process_docs(
        self,
        question: str,
        column_name: str,
        docs: pd.DataFrame,
        prompt_modifier: Callable[[int, pd.Series, str], str]
    ) -> pd.DataFrame:
        docs = docs.copy()
        docs[column_name] = pd.NA
        # For the first few documents, generate a response
        for index, doc in tqdm.tqdm(
            docs.iloc[:self.max_docs].iterrows(), total=min(self.max_docs, len(docs))
        ):
            prompt = prompt_modifier(index, doc, question)
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150
            )
            docs.at[index, column_name] = response.choices[0].message.content.strip()
        return docs

    def generate_response(
        self,
        question: str,
        docs: pd.DataFrame,
        response_type: Literal[
            "Informative Summary", "Explain the Reasoning", "Just Show the Results"
        ] = "Just Show the Results"
    ):
        docs["title"] = docs["title"].str.replace("\n", " ")
        docs["body"] = docs["body"].str.replace("\n", " ").str[:100] + "..."
        # Generate prompts for the LLM based on response type
        match response_type:
            case "Informative Summary":
                docs = self.process_docs(
                    question, "summary", docs, self._get_informative_summary_prompt
                )
            case "Explain the Reasoning":
                docs = self.process_docs(
                    question, "reasoning", docs, self._get_explain_the_reasoning_prompt
                )
            case "Just Show the Results":
                pass
        return docs.to_dict(orient="records")
