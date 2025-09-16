import streamlit as st
import fitz  # PyMuPDF
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image
import torch

# --- CONFIG ---
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
import torch

# Device setup
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load processor and model (large or fallback to base)
try:
    processor = TrOCRProcessor.from_pretrained(
        "microsoft/trocr-large-handwritten"
    )
    model = VisionEncoderDecoderModel.from_pretrained(
        "microsoft/trocr-large-handwritten"
    ).to(device)
except Exception as e:
    print("⚠️ Large model failed, falling back to base. Error:", e)
    processor = TrOCRProcessor.from_pretrained(
        "microsoft/trocr-base-handwritten"
    )
    model = VisionEncoderDecoderModel.from_pretrained(
        "microsoft/trocr-base-handwritten"
    ).to(device)


@st.cache_resource
def load_model():
    processor = TrOCRProcessor.from_pretrained(
        "microsoft/trocr-large-handwritten",
        force_download=True,
        resume_download=True
    )
    model = VisionEncoderDecoderModel.from_pretrained(
        "microsoft/trocr-large-handwritten",
        force_download=True,
        resume_download=True
    ).to(device)
    return processor, model



# Your OCR function
def ocr(image, processor, model):
    pixel_values = processor(image, return_tensors='pt').pixel_values.to(device)
    generated_ids = model.generate(pixel_values, max_new_tokens=100)
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
    return generated_text


# Your segmentation code (unchanged, just wrapped for Streamlit)
def segment_and_ocr(image: Image.Image, num_lines=5, num_cols=1):
    width, height = image.size
    line_height = height // num_lines
    line_width = width // num_cols
    transcription = ""

    if num_lines == 1 and num_cols == 1:
        text = ocr(image, processor, model)
        transcription = text
        st.image(image, caption=text, use_column_width=True)
    else:
        for j in range(num_lines):
            start_h = j * line_height
            end_h = (j + 1) * line_height
            for w in range(num_cols):
                start_w = w * line_width
                end_w = (w + 1) * line_width
                line_image = image.crop((start_w, start_h, end_w, end_h))
                text = ocr(line_image, processor, model)
                transcription += text + "\n"
                st.image(line_image, caption=text, use_column_width=True)

    return transcription


# --- STREAMLIT UI ---
st.title("📄 Handwritten Exam Paper OCR (Fixed Segmentation)")

uploaded_file = st.file_uploader("Upload a scanned PDF", type=["pdf"])

if uploaded_file is not None:
    pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")

    page_number = st.number_input("Select Page", 1, len(pdf_document), 1)
    num_lines = st.number_input("Number of lines", 1, 20, 5)
    num_cols = st.number_input("Number of columns", 1, 5, 1)

    page = pdf_document[page_number - 1]
    pix = page.get_pixmap()
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    st.subheader("Original Page")
    st.image(img, use_column_width=True)

    st.subheader("OCR Results (with your segmentation)")
    transcription = segment_and_ocr(img, num_lines=num_lines, num_cols=num_cols)

    st.text_area("Extracted Text", transcription, height=300)
