"""Deterministic answer-neutral ROI presentation using original image pixels."""
from pathlib import Path
from PIL import Image,ImageDraw
from scripts.stage14d1.contracts import box_pixels,pixel_to_normalized,validate_address

def render_views(image_path,address,destination):
 source=Image.open(image_path).convert('RGB');w,h=source.size
 if not validate_address(address,w,h):return dict(paths=[image_path],status='INVALID_ADDRESS_FULL_IMAGE_FALLBACK',transforms=[])
 if address['mode'] in ['GLOBAL','UNRESOLVABLE']:return dict(paths=[image_path],status=address['mode'],transforms=[])
 dest=Path(destination);dest.mkdir(parents=True,exist_ok=True)
 # Keep original full image unchanged. Put a thin neutral border around local crops, not source glyphs.
 # The explicit predicted address is shared with QIA; original global remains unmarked.
 paths=[image_path];transforms=[]
 for k,box in enumerate(address['boxes']):
  pix=box_pixels(box,w,h);crop=source.crop(pix);p=dest/f'roi_{k}.png'
  if p.exists():raise FileExistsError(p)
  crop.save(p);paths.append(str(p));transforms.append(dict(original_size=[w,h],normalized_box=box,pixel_box=list(pix),actual_normalized_box=pixel_to_normalized(pix,w,h),crop_size=list(crop.size),crop_to_source=dict(scale=[1,1],offset=list(pix[:2])),semantic_overlay=False))
 return dict(paths=paths,status='PREDICTED_ROI_PLUS_UNMODIFIED_GLOBAL',transforms=transforms)
