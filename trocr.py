
import streamlit as st
import fitz  # PyMuPDF
import numpy as np
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image, ImageEnhance
import pandas as pd
import cv2
from typing import List
import os
import shutil  # <-- added for zipping

# --- DATASET FOLDER (Desktop with per-paper subfolders) ---
desktop = os.path.join(os.path.expanduser("~"), "Desktop")
dataset_folder = os.path.join(desktop, "dataset")
os.makedirs(dataset_folder, exist_ok=True)

def get_paper_folder(filename: str) -> str:
    """
    Create a subfolder inside dataset for each uploaded PDF.
    Example: dataset/myfile.pdf -> dataset/myfile
    """
    base_name = os.path.splitext(filename)[0]  # remove .pdf
    paper_folder = os.path.join(dataset_folder, base_name)
    os.makedirs(paper_folder, exist_ok=True)
    return paper_folder
                 # create if not exists

# --- ZIP DOWNLOAD FUNCTION ---
import shutil, base64, os

def make_download_button(pdf_name: str):
    import shutil, base64, os
    base_name = os.path.splitext(os.path.basename(pdf_name))[0]
    dataset_folder = "dataset"
    paper_folder = os.path.join(dataset_folder, base_name)
    os.makedirs(paper_folder, exist_ok=True)

    # Zip must be created outside the folder
    zip_base = os.path.join(dataset_folder, base_name)  # dataset/myfile
    zip_path = shutil.make_archive(
        base_name=zip_base,       # where the .zip will be placed
        format="zip",
        root_dir=dataset_folder,  # parent folder
        base_dir=base_name        # folder inside dataset to compress
    )

    # Make download button
    with open(zip_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    href = f'<a href="data:application/zip;base64,{b64}" download="{os.path.basename(zip_path)}">📥 Download Cropped Images</a>'
    st.markdown(href, unsafe_allow_html=True)


# --- CONFIGURE PAGE ---
st.set_page_config(page_title="Handwritten OCR Labeling Tool", layout="wide")

# --- LOAD OCR MODEL ---
@st.cache_resource
def load_model():
    processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
    model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")
    return processor, model

processor, model = load_model()

# --- SEGMENTATION LOGIC ---
def segment_lines_opencv(image: Image.Image) -> List[Image.Image]:
    gray = np.array(image.convert("L"))
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    horizontal_proj = np.sum(thresh, axis=1)
    lines = []
    h, w = thresh.shape
    start = None
    for i in range(h):
        if horizontal_proj[i] > 0 and start is None:
            start = i
        elif horizontal_proj[i] == 0 and start is not None:
            if i - start > 10:
                line_img = image.crop((0, start, image.width, i))
                if line_img.height > 5:
                    lines.append(line_img)
            start = None
    if start is not None and h - start > 10:
        line_img = image.crop((0, start, image.width, h))
        if line_img.height > 5:
            lines.append(line_img)
    return lines

def run_ocr(img: Image.Image) -> str:
    pixel_values = processor(images=img, return_tensors="pt").pixel_values
    generated_ids = model.generate(pixel_values)
    return processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

# --- SESSION STATE ---
if "pdf_images_cache" not in st.session_state:
    st.session_state.pdf_images_cache = {}
if "labeled_lines" not in st.session_state:
    st.session_state.labeled_lines = []
if "current_page" not in st.session_state:
    st.session_state.current_page = 1
if "line_index" not in st.session_state:
    st.session_state.line_index = 0
if "show_all_lines" not in st.session_state:
    st.session_state.show_all_lines = False
if "ocr_texts" not in st.session_state:
    st.session_state.ocr_texts = {}

# --- SIDEBAR FILE UPLOAD ---
st.sidebar.title("OCR Labeling Tool")
current_file = st.sidebar.file_uploader("Upload PDF", type=["pdf"])

if current_file:
    if current_file.name not in st.session_state.pdf_images_cache:
        with st.spinner("Extracting pages..."):
            doc = fitz.open(stream=current_file.read(), filetype="pdf")
            images = []
            for page in doc:
                pix = page.get_pixmap(dpi=200)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                images.append(img)
            st.session_state.pdf_images_cache[current_file.name] = images
            st.session_state.current_page = 1
            st.session_state.line_index = 0

    images = st.session_state.pdf_images_cache[current_file.name]
    total_pages = len(images)

    # --- PAGE NAVIGATION ---
    st.sidebar.markdown("**Page Navigation**")
    col_prev, col_page, col_next = st.sidebar.columns([1, 2, 1])
    with col_prev:
        if st.button("⬅️", key="prev_page") and st.session_state.current_page > 1:
            st.session_state.current_page -= 1
            st.session_state.line_index = 0
            st.rerun()
    with col_next:
        if st.button("➡️", key="next_page") and st.session_state.current_page < total_pages:
            st.session_state.current_page += 1
            st.session_state.line_index = 0
            st.rerun()
    with col_page:
        st.markdown(
            f"<div style='text-align:center;font-size:16px;'>Page {st.session_state.current_page}/{total_pages}</div>",
            unsafe_allow_html=True
        )

    # --- IMAGE SELECTION ---
    page_num = st.session_state.current_page
    selected_img = images[page_num - 1]

    # --- SEGMENTATION ---
    with st.spinner("Segmenting lines..."):
        lines = segment_lines_opencv(selected_img)

    # --- FILTER ONLY SINGLE-LINE SEGMENTS ---
    MIN_HEIGHT = 15
    MAX_HEIGHT = 100
    filtered_lines = [line for line in lines if MIN_HEIGHT <= line.height <= MAX_HEIGHT]

    total_lines = len(filtered_lines)

    # --- TOGGLE: SHOW ALL LINES ---
    st.sidebar.markdown("**Line Display**")
    st.session_state.show_all_lines = st.sidebar.checkbox(
        "Show All Lines",
        value=st.session_state.show_all_lines
    )

    # --- LINE LABELING SECTION ---
    if not lines:
        st.warning("No lines detected on this page.")
    else:
        st.markdown("### Segmented Lines and OCR Text")

        base_index = 0 if st.session_state.show_all_lines else st.session_state.line_index
        display_lines = filtered_lines if st.session_state.show_all_lines else filtered_lines[base_index:base_index + 5]

        # --- Batch Progress Bar ---
        progress_placeholder = st.empty()
        progress_bar = progress_placeholder.progress(0)

        for i, line_img in enumerate(display_lines):
            progress_bar.progress(int(((i + 1) / len(display_lines)) * 100))

            global_line_num = base_index + i + 1
            line_id = f"{current_file.name}_page{page_num:03d}_line{global_line_num:03d}"

            if line_id not in st.session_state.ocr_texts:
                st.session_state.ocr_texts[line_id] = run_ocr(line_img)

            with st.container():
                st.markdown(f"**Line {global_line_num}** — ID: `{line_id}`")

                enhancer = ImageEnhance.Contrast(line_img)
                enhanced_img = enhancer.enhance(2.5)

                resized_img = enhanced_img.copy()
                resized_img.thumbnail((700, 300))
                st.image(resized_img)

                st.text_area(
                    "Corrected Text",
                    value=st.session_state.ocr_texts[line_id],
                    key=f"text_{line_id}",
                    height=80
                )

                corrected_text = st.session_state[f"text_{line_id}"]
                st.session_state.ocr_texts[line_id] = corrected_text

                # --- SAVE LINE IMAGE ---
                paper_folder = get_paper_folder(current_file.name)
                image_path = os.path.join(paper_folder, f"{line_id}.png")
                line_img.save(image_path)

                existing = next((item for item in st.session_state.labeled_lines if item["line_id"] == line_id), None)
                if existing:
                    existing["corrected_text"] = corrected_text
                    existing["image_path"] = image_path
                else:
                    st.session_state.labeled_lines.append({
                        "filename": current_file.name,
                        "line_id": line_id,
                        "corrected_text": corrected_text,
                        "image_path": image_path
                    })

        progress_placeholder.empty()  # Remove progress bar when done

        # --- ZIP DOWNLOAD BUTTON FOR CROPPED IMAGES ---
        make_download_button(current_file.name)

        # --- LINE SET NAVIGATION ---
        if not st.session_state.show_all_lines:
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("⬅️ Prev 5", key="prev_5") and st.session_state.line_index >= 5:
                    st.session_state.line_index -= 5
                    st.rerun()
            with col2:
                if st.button("Next 5 ➡️", key="next_5") and st.session_state.line_index + 5 < total_lines:
                    st.session_state.line_index += 5
                    st.rerun()

    # --- EXPORT SECTION ---
    st.markdown("### Export Corrected Labels")
    if st.session_state.labeled_lines:
        cur_rows = [r for r in st.session_state.labeled_lines if r["filename"] == current_file.name]
        if cur_rows:
            df = pd.DataFrame(cur_rows).drop_duplicates("line_id", keep="last")
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download CSV",
                data=csv,
                file_name=f"{current_file.name}_labeled_output.csv",
                mime="text/csv"
            )

else:
    st.markdown("## Welcome to the OCR Labeling Tool")
    st.markdown(
        """
        Upload a handwritten PDF from the sidebar to begin labeling segmented lines.
        This tool uses TR-OCR for handwritten recognition and OpenCV for line segmentation.

        ---
        **Features**
        - Accurate OCR for handwritten text
        - Clean UI with professional navigation
        - Label 5 lines at a time or view all
        - Download labeled data as CSV
        ---
        """
    )


