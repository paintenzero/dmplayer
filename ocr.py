import argparse
from typing import Optional
import fitz  # PyMuPDF to get page images
from PIL import Image
import torch
import os
from ocr.phi3v import Phi3V
from kb.knowledge_base import KnowledgeBase
from tqdm import tqdm

EMBEDDING_MODEL = "mixedbread-ai/mxbai-embed-large-v1"

# Create the parser
parser = argparse.ArgumentParser(description='An app to parse videogame manuals and embed it in ChromaDB')

# Add arguments
parser.add_argument('--db', type=str, help='Database file for embeddings', default='embeddings.db')
parser.add_argument('--collection', type=str, help='Collection in the database', default=None)
parser.add_argument('--file', type=str, help='PDF file of the book', required=True)
parser.add_argument('--cpu', type=bool, help='Force workload on CPU', default=False)
args = parser.parse_args()

book_name = os.path.splitext(os.path.basename(args.file))[0]
ocr_dir=os.path.dirname(args.file) + os.path.sep + book_name
if not os.path.isdir(ocr_dir):
    os.mkdir(ocr_dir)
document = fitz.open(args.file)

device = 'cuda' if torch.cuda.is_available() and not args.cpu else 'cpu'
ocr = None

print("perform OCR on PDF pages...")
full_text = []
# Iterate through each page
for page_number in tqdm(range(document.page_count)):
    ocr_result_filename = ocr_dir + os.path.sep + f'page_{page_number}.txt'
    res = ''
    if os.path.isfile(ocr_result_filename):
        with open(ocr_result_filename) as file:
            res = file.read()
    else:
        page = document.load_page(page_number)
        pix = page.get_pixmap(colorspace=fitz.csGRAY)
        image = Image.frombytes('L', [pix.width, pix.height], pix.samples)
        if ocr is None:
            ocr = Phi3V(device)
        res = ocr.recognize(image)
    if len(res) > 0 and res != 'no text':
        with open(ocr_dir + os.path.sep + f'page_{page_number}.txt', 'w+') as file:
            file.write(res)
        lines = res.splitlines()
        for l in lines:
            full_text.append({
                'page': page_number,
                'text': l.rstrip('\n')
            })

if args.collection != None:
    kb = KnowledgeBase(
        path=args.db, 
        embedding_model=EMBEDDING_MODEL,
        device=device,
    )
    kb.embed(full_text, collection=args.collection, book_name=book_name)
