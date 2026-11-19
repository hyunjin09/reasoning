"""Decode only a frozen parquet image; raw datasets stay external."""
import base64
import hashlib
import io
from functools import lru_cache
from PIL import Image

@lru_cache(maxsize=2)
def image_column(path):
    import pyarrow.parquet as pq
    return pq.read_table(path,columns=['image'])

def source_image(task):
    ref=task['image_reference'];value=image_column(ref['parquet']).slice(ref['row_index'],1).to_pylist()[0]['image']
    payload=value['bytes'] if isinstance(value,dict) else base64.b64decode(value) if isinstance(value,str) else value
    assert hashlib.sha256(payload).hexdigest()==task['image_sha256']
    im=Image.open(io.BytesIO(payload));im.load();return im

def prepare(task,processor,build_prompt,prepare_inputs):
    if task['image_reference']:
        image=source_image(task)
        messages=build_prompt({'question':task['prompt']},lambda row:image,'MathVision')
        inp=prepare_inputs(messages,processor)
        receipt_messages=[{'role':'user','content':[dict(type='image',source=task['image_reference'],sha256=task['image_sha256'],min_pixels=602112,max_pixels=4014080),dict(type='text',text=task['prompt'])]}]
    else:
        messages=[dict(role='user',content=[dict(type='text',text=task['prompt'])])]
        inp=dict(prompt=processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True))
        assert '<|image_pad|>' not in inp['prompt'];receipt_messages=messages
    return inp,receipt_messages
