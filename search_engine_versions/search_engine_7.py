"""Version using only the title"""

import pandas as pd

from vespa.package import ApplicationPackage, Field, Schema, Document, RankProfile, HNSW, RankProfile, Component, Parameter, \
    FieldSet, GlobalPhaseRanking, Function, FirstPhaseRanking, SecondPhaseRanking
from vespa.deployment import VespaDocker
from datasets import load_dataset
from vespa.io import VespaResponse, VespaQueryResponse
from langchain_text_splitters import RecursiveCharacterTextSplitter

class SearchEngine:
    def __init__(self):
        self.set_package()
        self.set_docker()
        self.set_app()

    def set_package(self):
        self.package = ApplicationPackage(
            name="colbert",
            schema=[
                Schema(
                    name="doc",
                    mode="streaming",
                    document=Document(
                        fields=[
                            Field(name="id", type="string", indexing=["summary"]),
                            Field(name="title", type="string", indexing=["index", "summary"]),
                            Field(name="body", type="string", indexing=["index", "summary"]),
                            Field(
                                name="metadata",
                                type="map<string,string>",
                                indexing=["summary", "index"],
                            ),
                            Field(name="page", type="int", indexing=["summary", "attribute"]),
                            Field(name="contexts", type="array<string>", indexing=["summary", "index"]),
                            Field(
                                name="embedding",
                                type="tensor<bfloat16>(context{}, x[384])",
                                indexing=[
                                    "input contexts",
                                    'for_each { (input title || "") . " " . ( _ || "") }',
                                    "embed e5",
                                    "attribute",
                                ],
                                attribute=["distance-metric: angular"],
                                is_document_field=False,
                            ),
                            Field(
                                name="colbert",
                                type="tensor<int8>(context{}, token{}, v[16])",
                                indexing=["input contexts", "embed colbert context", "attribute"],
                                is_document_field=False,
                            ),
                        ]
                    ),
                    rank_profiles=[
                        RankProfile(
                            name="colbert",
                            inputs=[
                                ("query(q)", "tensor<float>(x[384])"),
                                ("query(qt)", "tensor<float>(querytoken{}, v[128])"),
                            ],
                            functions=[
                                Function(name="cos_sim", expression="closeness(field, embedding)"),
                                Function(
                                    name="max_sim_per_context",
                                    expression="""
                                        sum('
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
                                    name="max_sim", expression="reduce(max_sim_per_context, max, context)"
                                ),
                            ],
                            first_phase=FirstPhaseRanking(expression="cos_sim"),
                            second_phase=SecondPhaseRanking(expression="max_sim"),
                            match_features=["cos_sim", "max_sim", "max_sim_per_context"],
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
                        Parameter(
                            name="prepend",
                            args={},
                            children=[
                                Parameter(name="query", args={}, children="query: "),
                                Parameter(name="document", args={}, children="passage: "),
                            ],
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
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1024,
            chunk_overlap=0,
            length_function=len,
            is_separator_regex=False,
        )

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
        vespa_feed = dataset.map(
            lambda x: {
                "id": x["id"],
                "fields": {
                    "title": x["title"],
                    "body": self.text_splitter.transform_documents(x["abstract"]),
                    "id": x["id"],
                }
            }
        )
        self.app.feed_iterable(iter=vespa_feed, schema="doc", namespace="article", callback=self.callback)

    def hits_to_df(self, response:VespaQueryResponse) -> pd.DataFrame:
        records = []
        fields = ["id", "title", "body"]
        for hit in response.hits:
            record = {}
            for field in fields:
                record[field] = hit['fields'][field]
            record["relevance"] = hit["relevance"]
            records.append(record)
        return pd.DataFrame(records)

    def search(self, query, n_hits: int = 5):
        with self.app.syncio(connections=1) as session:
            response:VespaQueryResponse = session.query(
                yql="select * from sources * where rank({targetHits:1000}nearestNeighbor(embedding, q), userQuery()) limit " + str(n_hits),
                query=query,
                ranking="fusion",
                body={
                    "input.query(q)": f"embed({query})",
                    "input.query(qt)": f"embed(colbert, {query}",
                },
            )
        assert(response.is_successful())
        return self.hits_to_df(response)
    
# Usage
# se = SearchEngine()
# se.feed_json(DATA_FILES)
# se.query("Machine learning and data science and stock market", n_hits=10)