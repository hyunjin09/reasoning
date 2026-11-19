"""Contact sheets of source images only, with source coordinates and questions."""
import argparse
from PIL import Image, ImageDraw
from scripts.stage7a.common import OUT, read_jsonl, write_jsonl
from scripts.stage6a.review_candidates import open_image


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--dataset', required=True)
    p.add_argument('--start', type=int, default=0)
    p.add_argument('--count', type=int, default=12)
    a = p.parse_args()
    rows = [r for r in read_jsonl(OUT / 'cohort/source_candidate_order.jsonl') if r['dataset'] == a.dataset]
    rows = rows[a.start:a.start + a.count]
    cw, ch = (850, 1250) if a.dataset == 'DocVQA' else (640, 630)
    columns = 2 if a.dataset == 'DocVQA' else 3
    sheet = Image.new('RGB', (cw * columns, ch * ((len(rows) + columns - 1) // columns)), 'white')
    draw = ImageDraw.Draw(sheet)
    for i, row in enumerate(rows):
        original = open_image(row)
        size = original.size
        original.thumbnail((cw - 60, ch - 150))
        x, y = i % columns * cw + 40, i // columns * ch + 50
        sheet.paste(original, (x, y))
        draw.text((x, y - 42), f"{a.start+i} {row['base_id']} {size}", fill='black')
        for j in range(6):
            dx, dy = round(original.width * j / 5), round(original.height * j / 5)
            draw.text((x + dx - 8, y - 18), str(round(size[0] * j / 5)), fill='red')
            draw.text((x - 35, y + dy), str(round(size[1] * j / 5)), fill='red')
        question = row['question']
        for j in range(min(3, (len(question) + 87) // 88)):
            draw.text((x, i // columns * ch + ch - 76 + j * 14), question[88*j:88*(j+1)], fill='black')
        draw.text((x, i // columns * ch + ch - 30), 'source answer: ' + str(row['answer'])[:85], fill='black')
    dest = OUT / 'review' / f'{a.dataset}_{a.start:03d}'
    dest.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(dest.with_suffix('.png'))
    write_jsonl(dest.with_suffix('.jsonl'), rows)
    print(dest.with_suffix('.png'))


if __name__ == '__main__':
    main()
