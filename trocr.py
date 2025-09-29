import streamlit as st
import os
import cv2
import numpy as np
import fitz
from PIL import Image
import torch
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
import shutil
import base64
import io

# ---------------------- CONFIG ----------------------
DATASET_DIR = "dataset"
os.makedirs(DATASET_DIR, exist_ok=True)

# Load TrOCR model (cached in session)
if "processor" not in st.session_state:
    st.session_state.processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
if "model" not in st.session_state:
    st.session_state.model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")


# ---------------------- HELPERS ----------------------
def get_paper_folder(pdf_name: str) -> str:
    """Return the folder path for a given PDF (creates it if missing)."""
    base = os.path.splitext(os.path.basename(pdf_name))[0]
    folder = os.path.join(DATASET_DIR, base)
    os.makedirs(folder, exist_ok=True)
    return folder


def segment_lines(page_img: np.ndarray):
    """Segment lines from a page image."""
    gray = cv2.cvtColor(page_img, cv2.COLOR_RGB2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    kernel = np.ones((5, 100), np.uint8)
    dilated = cv2.dilate(binary, kernel, iterations=1)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    lines = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if h > 15 and w > 30:  # filter noise
            line = page_img[y:y+h, x:x+w]
            lines.append((y, line))

    lines = sorted(lines, key=lambda x: x[0])
    return [line for _, line in lines]


def run_ocr(line_img: np.ndarray) -> str:
    """Run TrOCR on a line image."""
    pil_img = Image.fromarray(line_img)
    processor = st.session_state.processor
    model = st.session_state.model

    pixel_values = processor(pil_img, return_tensors="pt").pixel_values
    with torch.no_grad():
        generated_ids = model.generate(pixel_values)
    return processor.batch_decode(generated_ids, skip_special_tokens=True)[0]


def save_line(paper_folder: str, page_no: int, line_no: int, img: np.ndarray, text: str):
    """Save line image and OCR text."""
    page_folder = os.path.join(paper_folder, f"page_{page_no}")
    os.makedirs(page_folder, exist_ok=True)

    img_path = os.path.join(page_folder, f"line_{line_no}.png")
    cv2.imwrite(img_path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))

    txt_path = os.path.join(page_folder, f"line_{line_no}.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)


def make_download_button(pdf_name: str):
    """Create a download button for zipped dataset folder."""
    folder = get_paper_folder(pdf_name)
    zip_base = folder
    zip_path = shutil.make_archive(base_name=zip_base, format="zip", root_dir=folder)

    with open(zip_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    href = f'<a href="data:application/zip;base64,{b64}" download="{os.path.basename(zip_path)}">📥 Download Segmented Lines + OCR</a>'
    st.markdown(href, unsafe_allow_html=True)


# ---------------------- STREAMLIT UI ----------------------
st.title("📄 PDF Line Segmentation + TrOCR OCR")

uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

if uploaded_file:
    # Ensure paper folder is created immediately ✅ FIX
    paper_folder = get_paper_folder(uploaded_file.name)

    if uploaded_file.name not in st.session_state:
        # Extract PDF pages as images
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        images = []
        for page in doc:
            pix = page.get_pixmap(dpi=200)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(np.array(img))
        st.session_state[uploaded_file.name] = images
        st.session_state.current_page = 1

    images = st.session_state[uploaded_file.name]
    total_pages = len(images)

    # Page selector
    page_no = st.number_input("Page", 1, total_pages, st.session_state.current_page)
    st.session_state.current_page = page_no
    page_img = images[page_no-1]

    st.image(page_img, caption=f"Page {page_no}")

    if st.button("🔍 Segment and OCR Lines"):
        lines = segment_lines(page_img)
        st.write(f"Found {len(lines)} lines")

        for idx, line in enumerate(lines, start=1):
            text = run_ocr(line)
            save_line(paper_folder, page_no, idx, line, text)

            st.image(line, caption=f"Line {idx}")
            st.text_area(f"OCR Line {idx}", value=text, height=50)

        make_download_button(uploaded_file.name)
