"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0
"""

import json

def generate_bedrock_claude_response(bedrock_runtime,
                              prompt,
                              model_name,
                              max_tokens=2000,
                              temp=0,
                              topP=0.1,
                              topk=10,
                              stop_sequences=[],
                             ):
                                  
    MODEL_ID_MAPPING = {
        "Claude1": "anthropic.claude-v1",
        "Claude2": "anthropic.claude-v2",
        "ClaudeInstant": "anthropic.claude-instant-v1",
        "Claude2:1": "anthropic.claude-v2:1",
        "Claude3Sonnet": "anthropic.claude-3-sonnet-20240229-v1:0",
        "Claude3Haiku": "anthropic.claude-3-haiku-20240307-v1:0",
    }
    
    MODEL_KWARGS_MAPPING = {
        "Claude1": {
            "max_tokens_to_sample": max_tokens,
            "temperature": temp,
            "top_p": topP,
            "top_k": topk,
            "stop_sequences": stop_sequences,
        },
        "Claude2": {
            "max_tokens_to_sample": max_tokens,
            "temperature": temp,
            "top_p": topP,
            "top_k": topk,
            "stop_sequences": stop_sequences,
        },
        "ClaudeInstant": {
            "max_tokens_to_sample": max_tokens,
            "temperature": temp,
            "top_p": topP,
            "top_k": topk,
            "stop_sequences": stop_sequences,
        },
        "Claude2:1": {
            "max_tokens_to_sample": max_tokens,
            "temperature": temp,
            "top_p": topP,
            "top_k": topk,
            "stop_sequences": stop_sequences,
        },
        "Claude3Sonnet": {
            "max_tokens": max_tokens,
            "temperature": temp,
            "top_p": topP,
            "top_k": topk,
            "stop_sequences": stop_sequences,
        },
        "Claude3Haiku": {
            "max_tokens": max_tokens,
            "temperature": temp,
            "top_p": topP,
            "top_k": topk,
            "stop_sequences": stop_sequences,
        },
    }
    
    model_id = MODEL_ID_MAPPING[model_name]
    
    model_kwargs = MODEL_KWARGS_MAPPING[model_name]
    
    if model_name == "Claude3Sonnet" or model_name == "Claude3Haiku":
        model_kwargs["messages"] = [{"role":"user", "content":prompt}]
        model_kwargs["anthropic_version"] = ""
    else:
        model_kwargs["prompt"] = prompt
        
    body = json.dumps(model_kwargs)
    accept = "application/json"
    contentType = "application/json"
    
    response = bedrock_runtime.invoke_model(
            body=body, modelId=model_id, accept=accept, contentType=contentType
        )
    response_body = json.loads(response.get("body").read())
        
    if model_name == "Claude3Sonnet" or model_name == "Claude3Haiku":
        generated_response = response_body.get("content")[0]['text']
    else:
        generated_response = response_body.get("completion")
    
    return generated_response


def generate_bedrock_claude_response_with_token_count(bedrock_runtime,
                              prompt,
                              model_name,
                              max_tokens=512,
                              temp=0,
                              topP=1,
                              topk=50,
                              stop_sequences=[],
                             ):
                                  
    MODEL_ID_MAPPING = {
        "Claude1": "anthropic.claude-v1",
        "Claude2": "anthropic.claude-v2",
        "ClaudeInstant": "anthropic.claude-instant-v1",
        "Claude2:1": "anthropic.claude-v2:1",
        "Claude3Sonnet": "anthropic.claude-3-sonnet-20240229-v1:0",
        "Claude3Haiku": "anthropic.claude-3-haiku-20240307-v1:0",
    }
    
    MODEL_KWARGS_MAPPING = {
        "Claude1": {
            "max_tokens_to_sample": max_tokens,
            "temperature": temp,
            "top_p": topP,
            "top_k": topk,
            "stop_sequences": stop_sequences,
        },
        "Claude2": {
            "max_tokens_to_sample": max_tokens,
            "temperature": temp,
            "top_p": topP,
            "top_k": topk,
            "stop_sequences": stop_sequences,
        },
        "ClaudeInstant": {
            "max_tokens_to_sample": max_tokens,
            "temperature": temp,
            "top_p": topP,
            "top_k": topk,
            "stop_sequences": stop_sequences,
        },
        "Claude2:1": {
            "max_tokens_to_sample": max_tokens,
            "temperature": temp,
            "top_p": topP,
            "top_k": topk,
            "stop_sequences": stop_sequences,
        },
        "Claude3Sonnet": {
            "max_tokens": max_tokens,
            "temperature": temp,
            "top_p": topP,
            "top_k": topk,
            "stop_sequences": stop_sequences,
        },
        "Claude3Haiku": {
            "max_tokens": max_tokens,
            "temperature": temp,
            "top_p": topP,
            "top_k": topk,
            "stop_sequences": stop_sequences,
        },
    }
    
    model_id = MODEL_ID_MAPPING[model_name]
    
    model_kwargs = MODEL_KWARGS_MAPPING[model_name]
    
    if model_name == "Claude3Sonnet" or model_name == "Claude3Haiku":
        model_kwargs["messages"] = [{"role":"user", "content":prompt}]
        model_kwargs["anthropic_version"] = ""
    else:
        model_kwargs["prompt"] = prompt
        
    body = json.dumps(model_kwargs)
    accept = "application/json"
    contentType = "application/json"
    
    response = bedrock_runtime.invoke_model(
            body=body, modelId=model_id, accept=accept, contentType=contentType
        )
    
    input_token_count = response["ResponseMetadata"]["HTTPHeaders"][
    "x-amzn-bedrock-input-token-count"
    ]
    
    output_token_count = response["ResponseMetadata"]["HTTPHeaders"][
    "x-amzn-bedrock-output-token-count"
    ]
    
    response_body = json.loads(response.get("body").read())
        
    if model_name == "Claude3Sonnet" or model_name == "Claude3Haiku":
        generated_response = response_body.get("content")[0]['text']
    else:
        generated_response = response_body.get("completion")
    
    return generated_response, input_token_count, output_token_count