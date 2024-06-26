"""Search Engine using Hybrid Search ranking with body and title fields"""

import pandas as pd

from vespa.package import ApplicationPackage, Field, Schema, Document, RankProfile, HNSW, RankProfile, Component, Parameter, FieldSet, GlobalPhaseRanking, Function
from vespa.deployment import VespaDocker
from datasets import load_dataset
from vespa.io import VespaResponse, VespaQueryResponse


class SearchEngine:
    def __init__(self):
        self.set_package()
        self.set_docker()
        self.set_app()

    def set_package(self):
        self.package = ApplicationPackage(
            name="hybridabstractandtitle",
            schema=[Schema(
                name="doc",
                document=Document(
                    fields=[
                        Field(name="id", type="string", indexing=["summary"]),
                        Field(name="title", type="string", indexing=["index", "summary"], index="enable-bm25"),
                        Field(name="body", type="string", indexing=["index", "summary"], index="enable-bm25", bolding=True),
                        Field(name="embedding", type="tensor<float>(x[384])",
                            indexing=["input title . \" \" . input body", "embed", "index", "attribute"],
                            ann=HNSW(distance_metric="angular"),
                            is_document_field=False
                        )
                    ]
                ),
                fieldsets=[
                    FieldSet(name = "default", fields = ["title", "body"])
                ],
                rank_profiles=[
                    RankProfile(
                        name="bm25",
                        inputs=[("query(q)", "tensor<float>(x[384])")],
                        functions=[Function(
                            name="bm25sum", expression="bm25(title) + bm25(body)"
                        )],
                        first_phase="bm25sum"
                    ),
                    RankProfile(
                        name="semantic",
                        inputs=[("query(q)", "tensor<float>(x[384])")],
                        first_phase="closeness(field, embedding)"
                    ),
                    RankProfile(
                        name="fusion",
                        inherits="bm25",
                        inputs=[("query(q)", "tensor<float>(x[384])")],
                        first_phase="closeness(embedding)",
                        global_phase=GlobalPhaseRanking(
                            expression="bm25sum + closeness(embedding)",
                            rerank_count=1000
                        )
                    )
                ]
            )
            ],
            components=[Component(id="e5", type="hugging-face-embedder",
                parameters=[
                    Parameter("transformer-model", {"url": "https://github.com/vespa-engine/sample-apps/raw/master/simple-semantic-search/model/e5-small-v2-int8.onnx"}),
                    Parameter("tokenizer-model", {"url": "https://raw.githubusercontent.com/vespa-engine/sample-apps/master/simple-semantic-search/model/tokenizer.json"})
                ]
            )]
        )

    def set_docker(self):
        self.docker = VespaDocker()

    def set_app(self):
        self.app = self.docker.deploy(application_package=self.package)

    def callback(self, response, id):
        if not response.is_successful():
            print(f"Error when feeding document {id}: {response.get_json()}")

    def feed_json(self, data_dir, data_files, split_size_limit, **kwargs):
        dataset = load_dataset(
            "json",
            data_dir=data_dir,
            data_files=data_files,
            split=f"train[0:{split_size_limit}]",
        )
        vespa_feed = dataset.map(lambda x: {"id": x["id"], "fields": { "title": x["title"], "body": x["abstract"], "id": x["id"]}})
        self.app.feed_iterable(vespa_feed, schema="doc", namespace="article", callback=self.callback)

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

    def search(self, query, n_hits: int = 10):
        with self.app.syncio(connections=1) as session:
            response:VespaQueryResponse = session.query(
                yql="select * from sources * where rank({targetHits:1000}nearestNeighbor(embedding, q), userQuery()) limit " + str(n_hits),
                query=query,
                ranking="fusion",
                body={"input.query(q)": f"embed({query})"},
            )
        assert(response.is_successful())
        return self.hits_to_df(response)