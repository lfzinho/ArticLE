"""Search Engine using Colbert Max Sim Global ranking with abstract field and sentence split"""

import pandas as pd

import unicodedata
from vespa.package import ApplicationPackage, Field, Schema, Document, RankProfile, HNSW, RankProfile, Component, Parameter, \
    FieldSet, GlobalPhaseRanking, Function, FirstPhaseRanking, SecondPhaseRanking
from vespa.deployment import VespaDocker
from datasets import load_dataset
from vespa.io import VespaResponse, VespaQueryResponse


def sentence_split(string, split_on="."):
    return string.split(split_on)


def remove_control_characters(s):
    s = s.replace("\\", "")
    s = s.replace("\n", " ").strip()
    return "".join(ch for ch in s if unicodedata.category(ch)[0] != "C")

def flatten_to_string(data):
    def flatten(item, parent_key='', sep='_'):
        if isinstance(item, dict):
            for k, v in item.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                yield from flatten(v, new_key, sep=sep)
        elif isinstance(item, list):
            for i, v in enumerate(item):
                new_key = f"{parent_key}{sep}{i}" if parent_key else str(i)
                yield from flatten(v, new_key, sep=sep)
        else:
            yield parent_key, item

    flattened_items = list(flatten(data))
    return ', '.join(f"{k}: {v}" for k, v in flattened_items)

class SearchEngine:
    def __init__(self):
        self.set_package()
        self.set_docker()
        self.set_app()

    def set_package(self):
        self.package = ApplicationPackage(
            name="max_sim_per_context_sentences_abstract_only",
            schema=[
                Schema(
                    name="doc",
                    mode="streaming",
                    document=Document(
                        fields=[
                            Field(name="id", type="string", indexing=["summary"]),
                            Field(name="body", type="array<string>", indexing=["summary", "index"]),
                            Field(name="authors", type="array<string>", indexing=["summary", "index"]),
                            Field(
                                name="embedding",
                                type="tensor<bfloat16>(body{}, x[384])",
                                indexing=[
                                    "input body",
                                    "embed e5",
                                    "attribute",
                                ],
                                attribute=["distance-metric: angular"],
                                is_document_field=False,
                            ),
                            Field(
                                name="colbert",
                                type="tensor<int8>(body{}, token{}, v[16])",
                                indexing=["input body", "embed colbert body", "attribute"],
                                is_document_field=False,
                            ),
                        ]
                    ),
                    rank_profiles=[
                        RankProfile(
                            name="colbert_local",
                            inputs=[
                                ("query(q)", "tensor<float>(x[384])"),
                                ("query(qt)", "tensor<float>(querytoken{}, v[128])"),
                            ],
                            functions=[
                                Function(name="cos_sim", expression="closeness(field, embedding)"),
                                Function(
                                    name="max_sim_per_body",
                                    expression="""
                                        sum(
                                            reduce(
                                                sum(
                                                    query(qt) * unpack_bits(attribute(colbert)) , v
                                                ),
                                                max, token
                                            ),
                                            querytoken
                                        )
                                    """,
                                ),
                                Function(
                                    name="max_sim_local", expression="reduce(max_sim_per_body, max, body)"
                                ),
                            ],
                            first_phase=FirstPhaseRanking(expression="cos_sim"),
                            second_phase=SecondPhaseRanking(expression="max_sim_local"),
                            match_features=["cos_sim", "max_sim_local", "max_sim_per_body"],
                        ),
                        RankProfile(
                            name="colbert_global",
                            inputs=[
                                ("query(q)", "tensor<float>(x[384])"),
                                ("query(qt)", "tensor<float>(querytoken{}, v[128])"),
                            ],
                            functions=[
                                Function(name="cos_sim", expression="closeness(field, embedding)"),
                                Function(
                                    name="max_sim_cross_body",
                                    expression="""
                                    sum(
                                        reduce(
                                            sum(
                                                query(qt) *  unpack_bits(attribute(colbert)) , v
                                            ),
                                            max, token, body
                                        ),
                                        querytoken
                                    )
                                    """
                                ),
                                Function(
                                    name="max_sim_global", expression="reduce(max_sim_cross_body, max)"
                                ),
                            ],
                            first_phase=FirstPhaseRanking(expression="cos_sim"),
                            second_phase=SecondPhaseRanking(expression="max_sim_global"),
                            match_features=["cos_sim", "max_sim_global", "max_sim_cross_body"],
                        )
                    ]
                )
            ],
            components=[
                Component(
                    id="e5",
                    type="hugging-face-embedder",
                    parameters=[
                        Parameter(
                            name="transformer-model",
                            args={
                                "url": "https://huggingface.co/intfloat/e5-small-v2/resolve/main/model.onnx"
                            },
                        ),
                        Parameter(
                            name="tokenizer-model",
                            args={
                                "url": "https://huggingface.co/intfloat/e5-small-v2/raw/main/tokenizer.json"
                            },
                        ),
                    ],
                ),
                Component(
                    id="colbert",
                    type="colbert-embedder",
                    parameters=[
                        Parameter(
                            name="transformer-model",
                            args={
                                "url": "https://huggingface.co/colbert-ir/colbertv2.0/resolve/main/model.onnx"
                            },
                        ),
                        Parameter(
                            name="tokenizer-model",
                            args={
                                "url": "https://huggingface.co/colbert-ir/colbertv2.0/raw/main/tokenizer.json"
                            },
                        ),
                    ],
                ),
            ]
        )

    def set_docker(self):
        self.docker = VespaDocker()

    def set_app(self):
        self.app = self.docker.deploy(application_package=self.package)

    def callback(self, response, id):
        if not response.is_successful():
            print(f"Error when feeding document {id}: {response.get_json()}")

    def feed_json(self, data_dir, data_files, split_size_limit):
        dataset = load_dataset(
            "json",
            data_dir=data_dir,
            data_files=data_files,
            split=f"train[0:{split_size_limit}]",
        )

        docs = []

        for row in dataset:
            text_chunks = [remove_control_characters(chunk) for chunk in row["abstract"].split(".")]
            if text_chunks[-1] == "":
                text_chunks = text_chunks[:-1]
            fields = {
                "id": row["id"], # str
                "body": text_chunks, # list[str]
                "authors": sentence_split(remove_control_characters(row["authors"])), # list[str]
            }

            docs.append(fields)
        
        def vespa_feed():
            for doc in docs:
                yield {"fields": doc, "id": doc["id"], "groupname": "article-groupname"}

        self.app.feed_iterable(iter=vespa_feed(), schema="doc", namespace="article", callback=self.callback)

    def hits_to_df(self, response:VespaQueryResponse) -> pd.DataFrame:
        records = []
        fields = ["id", "body", "authors"]
        for hit in response.hits:
            record = {}
            for field in fields:
                if isinstance(hit['fields'][field], str):
                    record[field] = hit['fields'][field]
                else:
                    record[field] = flatten_to_string(hit['fields'][field])
            record["relevance"] = hit["relevance"]
            records.append(record)
        return pd.DataFrame(records)

    def search(self, query, n_hits: int = 5):
        with self.app.syncio(connections=1) as session:
            response:VespaQueryResponse = session.query(
                yql="select * from sources * where ({targetHits:1000}nearestNeighbor(embedding,q))",
                groupname="article-groupname",
                ranking="colbert_local",
                query=query,
                body={
                    "input.query(q)": f'embed(e5, "{query}")',
                    "input.query(qt)": f'embed(colbert, "{query}")',
                },
            )
        assert(response.is_successful())
        return self.hits_to_df(response)