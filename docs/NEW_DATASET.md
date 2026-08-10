# New dataset guide

New datasets are defined in [`vibe/datasets.py`](../vibe/datasets.py).

## 1. Define the dataset

For example, use a Hugging Face embedding model with a Hugging Face text dataset:

```python
def minilm_embedding():
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return lambda sentences: model.encode(sentences)


def example_dataset(out_fn, embedding, metric):
    text_embedding_dataset(
        out_fn,
        dataset_name="sentence-transformers/agnews",
        attribute="description",
        query_attribute=None,
        embedding=embedding,
        metric=metric,
    )
```

For a custom data source, call `write_output` directly with two-dimensional `train` and `test` arrays containing corpus and query embeddings. We normally use 1,000 test queries. For an out-of-distribution dataset, pass additional query samples as `learn`; VIBE stores their true 100 nearest neighbors for methods that implement `fit_ood`.

Reuse the download, splitting, embedding, text, and image helpers already in `vibe/datasets.py` when possible.

## 2. Register the dataset

Add the function to the `DATASETS` dictionary:

```python
DATASETS = {
    # ...
    "agnews-minilm-384-cosine": lambda out_fn: example_dataset(out_fn, minilm_embedding(), "cosine"),
}
```

Use the form `<source>-<model>-<dimension>-<distance>[-<point_type>]`. The dimension must be the first numeric component. Available distances are `euclidean`, `cosine`, `ip`, `normalized`, and `hamming`. Omit the point-type suffix for floats; otherwise use `int8`, `uint8`, or `binary`.

## 3. Create the dataset

If you need extra dependencies, add Python or Conda packages to `dataset_environment.yml` and system or build packages to `dataset.def`, pinning versions where possible. Then build the image and create the dataset:

```sh
singularity build dataset.sif dataset.def
./create_dataset.sh --dataset agnews-minilm-384-cosine
```

Pass `--singularity-args "--nv"` when the job needs a GPU.
