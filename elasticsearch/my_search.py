import pandas as pd
import eland as ed
from eland.ml import MLModel
import elasticsearch
from elasticsearch import Elasticsearch
from elasticsearch import helpers
from pathlib import Path
from eland.common import es_version
from eland.ml.pytorch import PyTorchModel
from eland.ml.pytorch.transformers import TransformerModel
import torch
from transformers import pipeline, AutoModelForCausalLM


# class search(self):
# connection
def connection(elastic_cloud_id, username, password):
    es = Elasticsearch(
    cloud_id = elastic_cloud_id,
    basic_auth = (username, password)
    )

    print("elastic cloud information :", es.info())
    print("elastic cloud version :", es_version(es))



# 인덱스의 매핑 정보 가져오기
def mapping_info(index_name):
    print(es.indices.get_mapping(index = index_name))

# 삭제할 인덱스 이름 지정
def delete_index(index_name):
    index_name = "연구자_raw"  # 삭제하려는 인덱스 이름을 설정하세요

    # 인덱스 삭제 명령 실행
    if es.indices.exists(index = index_name):
        es.indices.delete(index = index_name)
        print(f"인덱스 '{index_name}' 삭제 완료")
    else:
        print(f"인덱스 '{index_name}'는 이미 존재하지 않습니다.")

# 인덱스 생성 함수
def create_index(data_path, index_name) :

    df = pd.read_csv(data_path)
    df = df.fillna(0)

    field_name = df.columns.to_list()
    f_type = df.dtypes

    # Define a custom analyzer
    custom_analyzer = {
        "tokenizer": "my_tokenizer",
        "filter": ["lowercase", "trim", "stop", "nori_filter"]
        # "char_filter": ["html_strip"]
    }

    # Define a custom filter for the analyzer
    custom_filter = {
        "type": "pattern_replace",
        "pattern": "[^a-zA-Z0-9가-힣\\s]",
        "replacement": " "
    }

    # Define a custom tokenizer
    custom_tokenizer = {
        "type": "nori_tokenizer",
        "decompound_mode": "none",
        "discard_punctuation": False
    }

    # nori 토큰 필터 설정
    nori_filter = {
        "type": "nori_part_of_speech",
        "stoptags": ["E", "IC", "J", "MAG", "MAJ", "MM", "NR", "SP", "SSC", "SSO", "SC", "SE", 
                 "XR", "XPN", "XSA", "XSN", "XSV", "VA", "VCN", "VCP", "VSV", "VV", "VX", 
                 "UNKNOWN", "UNA", "NA"],
        # "user_dictionary": "user_dictionary.txt"
    }

    # Create an index with custom analyzer and tokenizer settings
    index_settings = {
        "settings": {
            "analysis": {
                "analyzer": {
                    "my_analyzer": custom_analyzer
                },
                "filter": {
                    # "my_filter": custom_filter,
                    "nori_filter": nori_filter
                },
                "tokenizer": {
                    "my_tokenizer": custom_tokenizer
                }
            }
        },
        "mappings": {
            "properties": {}  # We'll add the properties dynamically
        }
    }

    # Iterate through the dataframes and dynamically add properties to the mappings
    # for df in dataframes:
    fields = df.columns.tolist()

    for field in fields:
        field_type = "text" if pd.api.types.is_string_dtype(df[field]) or pd.api.types.is_object_dtype(df[field]) else "long"
        if field_type == "text":
            index_settings["mappings"]["properties"][field] = {"type": field_type, "analyzer": "my_analyzer"}
        else:
            index_settings["mappings"]["properties"][field] = {"type": field_type}

    index_settings["mappings"]

    # Create the index with the defined settings
    es.indices.create(index = index_name, body = index_settings)

    # Bulk insert data into Elasticsearch
    actions = []
    for _, row in df.iterrows():
        data = row.to_dict()
        actions.extend([{"_index": index_name, "_source": data}])

    helpers.bulk(es, actions)


# import the embedding model in elastic could
def get_embedding_model(model_name, task_type, save_path) :
    # TransformerModel 로드
    tm = TransformerModel(model_id = model_name, task_type = task_type, es_version = es_version(es))

    # Export the model in a TorchScrpt representation which Elasticsearch uses
    Path(save_path).mkdir(parents=True, exist_ok=True)
    model_path, config, vocab_path = tm.save(save_path)

    print('model_path : ', model_path)
    print('config : ', config)
    print('vocab_path : ', vocab_path)

    # Import model into Elasticsearch
    ptm = PyTorchModel(es, tm.elasticsearch_model_id())
    print(ptm)
    ptm.import_model(model_path = model_path, config_path = None, vocab_path = vocab_path, config = config)

# prompt
def import_prompt(model_name):
    model = AutoModelForCausalLM.from_pretrained(
    MODEL,
    torch_dtype = torch.float16,
    low_cpu_mem_usage = False,
    ).to(device=f"cuda", non_blocking = True)
    model.eval()

    pipe = pipeline(
        'text-generation', 
        model=model,
        tokenizer=MODEL,
        device=0
    )

    def ask(x, context = '', is_input_full = False):
        ans = pipe(
            f"### 질문: {x}\n\n### 맥락: {context}\n\n### 답변:" if context else f"### 질문: {x}\n\n### 답변:", 
            do_sample = True, 
            max_new_tokens = 512,
            temperature = 0.7,
            top_p = 0.9,
            return_full_text = False,
            eos_token_id = 2,
        )
        print(ans[0]['generated_text'])


