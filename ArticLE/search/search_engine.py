from collections import defaultdict
from pathlib import Path
from typing import Iterable, Sequence

import datasets
import pandas as pd
from vespa.application import Vespa
from vespa.package import ApplicationPackage, Field, Schema, Document, RankProfile, HNSW, RankProfile, Component, Parameter, FieldSet, GlobalPhaseRanking, Function
from vespa.deployment import VespaDocker
from vespa.io import VespaResponse, VespaQueryResponse


class SearchEngine:
    app: Vespa

    def _hits_to_df(self, response: VespaQueryResponse) -> pd.DataFrame:
        fields = ["id", "title", "body"]
        records = defaultdict(list)

        for hit in response.hits:
            for field in fields:
                records[field].append(hit["fields"][field])
            records["relevance"].append(hit["relevance"])

        return pd.DataFrame(records)

    def _search(
        self,
        queries: Iterable[str],
        n_hits: int,
        connect_timeout: float = 5.0,
        read_timeout: float = 10.0
    ) -> list[VespaQueryResponse]:
        results = []
        with self.app.syncio(connections=1) as session:
            for i, query in enumerate(queries, start=1):
                response = session.query(
                    body={"input.query(q)": f"embed({query})"},
                    query=query,
                    ranking="fusion",
                    timeout=(connect_timeout, read_timeout),
                    yql=f"select * from sources * where userQuery() limit {n_hits}",
                )
                if not response.is_successful():
                    raise RuntimeError(
                        f"Query number {i} failed with HTTP status code {response.status_code}"
                    )
                results.append(response)
        return results

    def search(self, query: str, n_hits: int = 10, timeout: float = 5.0) -> pd.DataFrame:
        response = self._search([query], n_hits, timeout)[0]
        return self._hits_to_df(response)


class SearchEngineCloud(SearchEngine):
    def __init__(self, endpoint: str, cert_path: Path | str, key_path: Path | str) -> None:
        self.endpoint = endpoint
        self.cert_path = cert_path
        self.key_path = key_path
        self.app = Vespa(self.endpoint, cert=self.cert_path, key=self.key_path)


class SearchEngineLocal(SearchEngine):
    def __init__(
        self,
        data_dir: Path | str,
        data_files: Sequence[str],
        max_data_samples: int | None = None,
        **kwargs
    ) -> None:
        self.set_package()
        self.docker = VespaDocker()
        self.app = self.docker.deploy(application_package=self.package)
        self.feed_json(data_dir, data_files, max_data_samples, **kwargs)

    def set_package(self):
        self.package = ApplicationPackage(
        name="hybridsearch",
        schema=[Schema(
            name="doc",
            document=Document(
                fields=[
                    Field(name="id", type="string", indexing=["summary"]),
                    Field(name="title", type="string", indexing=["index", "summary"], index="enable-bm25"),
                    Field(name="body", type="string", indexing=["index", "summary"], index="enable-bm25", bolding=True),
                    Field(
                        name="embedding", type="tensor<float>(x[384])",
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
                    first_phase="closeness(field, embedding)",
                    global_phase=GlobalPhaseRanking(
                        expression="bm25sum + closeness(embedding)",
                        rerank_count=1000
                    )
                )
            ]
        )],
        components=[Component(id="e5", type="hugging-face-embedder",
            parameters=[
                Parameter("transformer-model", {"url": "https://github.com/vespa-engine/sample-apps/raw/master/simple-semantic-search/model/e5-small-v2-int8.onnx"}),
                Parameter("tokenizer-model", {"url": "https://raw.githubusercontent.com/vespa-engine/sample-apps/master/simple-semantic-search/model/tokenizer.json"})
            ]
        )]
    )

    def callback(self, response: VespaResponse, id: str) -> None:
        if not response.is_successful():
            print(f"Error while feeding document {id}: {response.get_json()}")

    def feed_json(
        self,
        data_dir: Path | str,
        data_files: Sequence[str],
        max_data_samples: int | None = None,
        **kwargs
    ) -> None:
        self.dataset = datasets.load_dataset(
            "json",
            data_dir=data_dir,
            data_files=data_files,
            split=f"train[0:{max_data_samples}]" if max_data_samples else "train",
            **kwargs
        )
        vespa_feed = self.dataset.map(lambda x: {
            "id": x["id"],
            "fields": {
                "title": x["title"],
                "body": x["abstract"],
                "id": x["id"]
            }
        })
        self.app.feed_iterable(
            vespa_feed, schema="doc", namespace="article", callback=self.callback
        )
