def text_only_fields(keys,mm_token_values):
    allowed={'input_ids','attention_mask','token_type_ids','mm_token_type_ids'}
    if not set(keys)<=allowed or any(v!=0 for v in mm_token_values):
        raise ValueError('Text-only oracle contains unexpected fields or non-text modality tags')
    return True
