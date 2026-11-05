
import xml.etree.ElementTree as ET
import base64
import argparse
import shutil
from pathlib import Path
from io import BytesIO
from pypdf import PdfReader, PdfWriter

INPUT_DIR = Path("/app/files")
OUTPUT_DIR = INPUT_DIR / "converted"

NAMESPACES = {
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
}

# Preserve original XML namespace prefixes
for prefix, uri in NAMESPACES.items():
    ET.register_namespace(prefix, uri)



def convert_file(file_path: Path, save_merged_pdf: bool = False):

    print(f"\nProcessing: {file_path.name}")

    output_file = OUTPUT_DIR / file_path.name

    try:
        # Read XML
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Find all attachments
        attachments = []

        commercial_invoice_reference = None

        document_references = root.findall(
            "cac:AdditionalDocumentReference", NAMESPACES
        )

        for document_reference in document_references:

            description = document_reference.find(
                "cbc:DocumentDescription", NAMESPACES
            )

            description_value = (
                (description.text or "").strip()
                if description is not None
                else ""
            )

            attachment = document_reference.find(
                "cac:Attachment", NAMESPACES
            )

            if attachment is None:
                continue

            embedded = attachment.find(
                "cbc:EmbeddedDocumentBinaryObject", NAMESPACES
            )

            if embedded is None or not embedded.text:
                continue

            attachments.append({
                "reference": document_reference,
                "attachment": attachment,
                "embedded": embedded,
                "description": description_value
            })

            if description_value == "Commercial invoice":
                commercial_invoice_reference = document_reference

        print(f"Found {len(attachments)} attachments")

        # No attachments
        if len(attachments) == 0:
            print("No attachments found")
            shutil.copy2(file_path, output_file)
            return

        # Exactly one Commercial invoice: leave XML unchanged
        if (
            len(attachments) == 1
            and attachments[0]["description"] == "Commercial invoice"
        ):
            print("Only one Commercial invoice. XML remains unchanged.")
            shutil.copy2(file_path, output_file)
            return

        # Multiple attachments require a Commercial invoice reference
        if commercial_invoice_reference is None:
            print("ERROR: No Commercial invoice reference found.")
            return

        # Merge all PDF attachments
        pdf_writer = PdfWriter()

        for attachment in attachments:

            encoded_pdf = attachment["embedded"].text.strip()

            # Base64 decode
            pdf_bytes = base64.b64decode(encoded_pdf, validate=True)

            # Read PDF
            pdf_reader = PdfReader(BytesIO(pdf_bytes))

            print(
                f"Adding {attachment['description']}: "
                f"{len(pdf_reader.pages)} pages"
            )

            # Append all pages
            pdf_writer.append_pages_from_reader(pdf_reader)

        # Create merged PDF in memory
        merged_pdf = BytesIO()
        pdf_writer.write(merged_pdf)

        merged_pdf_bytes = merged_pdf.getvalue()

        # Optionally save the merged PDF as a separate file
        if save_merged_pdf:

            pdf_output_file = OUTPUT_DIR / f"{file_path.stem}_merged.pdf"

            pdf_output_file.write_bytes(merged_pdf_bytes)

            print(f"Merged PDF saved: {pdf_output_file.name}")

        # Base64 encode merged PDF
        merged_base64 = base64.b64encode(
            merged_pdf_bytes
        ).decode("utf-8")


        # Base64 encode merged PDF
        merged_base64 = base64.b64encode(
            merged_pdf_bytes
        ).decode("utf-8")

        print(f"Merged PDF size: {len(merged_pdf_bytes)} bytes")

        # Find Commercial invoice attachment
        commercial_attachment = commercial_invoice_reference.find(
            "cac:Attachment", NAMESPACES
        )

        commercial_embedded = commercial_attachment.find(
            "cbc:EmbeddedDocumentBinaryObject", NAMESPACES
        )

        # Replace Commercial invoice with merged PDF
        commercial_embedded.text = merged_base64

        # Remove the other attachment references to avoid duplicates
        for attachment in attachments:

            if attachment["reference"] is not commercial_invoice_reference:
                root.remove(attachment["reference"])

        # Write updated XML
        ET.indent(tree, space="    ")

        tree.write(
            output_file,
            encoding="utf-8",
            xml_declaration=True
        )

        print(f"Successfully converted: {output_file.name}")

    except Exception as ex:
        print(f"ERROR processing {file_path.name}: {ex}")


def main():

    parser = argparse.ArgumentParser(
        description="EHF XML and PDF converter"
    )

    parser.add_argument(
        "--save-merged-pdf",
        action="store_true",
        help="Save the merged PDF as a separate file"
    )

    args = parser.parse_args()

    print(f"Input directory:  {INPUT_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Save merged PDF:  {args.save_merged_pdf}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    files = list(INPUT_DIR.glob("*.xml"))

    print(f"Found {len(files)} XML files")

    for file_path in files:
        convert_file(file_path, args.save_merged_pdf)

    print("\nProcessing completed!")


if __name__ == "__main__":
    main()
