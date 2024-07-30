import os
import http.server
import socketserver
import json
import tempfile
from io import BytesIO
from http import HTTPStatus
from pdfminer.high_level import extract_text
from PyPDF2 import PdfReader
import cgi
import mimetypes

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(HTTPStatus.OK)
        self.end_headers()
        msg = f'Hello At-Eases!!! testing deploy {self.path}'
        self.wfile.write(msg.encode())

    def do_POST(self):
        # Check for content type
        content_type = self.headers.get('Content-Type', '')
        if not content_type.startswith('multipart/form-data'):
            self.send_response(HTTPStatus.BAD_REQUEST)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 0,
                'message': 'Invalid content type. Multipart/form-data expected.'
            }).encode())
            return

        # Parse multipart form-data
        form = cgi.FieldStorage(fp=self.rfile, environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': content_type}, headers=self.headers)
        uploaded_file = form['file']

        if not uploaded_file.file:
            self.send_response(HTTPStatus.BAD_REQUEST)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 0,
                'message': 'File not provided'
            }).encode())
            return

        # Check file extension and MIME type
        filename = uploaded_file.filename
        if not filename.lower().endswith('.pdf'):
            self.send_response(HTTPStatus.BAD_REQUEST)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 0,
                'message': 'Invalid file type. Only PDF files are accepted.'
            }).encode())
            return

        # Optionally check MIME type
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type != 'application/pdf':
            self.send_response(HTTPStatus.BAD_REQUEST)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 0,
                'message': 'Invalid file type. Only PDF files are accepted.'
            }).encode())
            return

        # Get the continuation keyword
        continuation_keyword = form.getfirst('continuation_keyword', 'Qty')

        # Handle file upload
        uploaded_file_data = uploaded_file.file.read()

        # Create a temporary file to store the uploaded PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_pdf_path = temp_file.name
            temp_file.write(uploaded_file_data)

        try:
            # Extract the page ranges
            page_ranges = self.extract_airway_bills_by_page(temp_pdf_path, continuation_keyword)
            response = json.dumps({
                'status': 1,
                'message': 'success',
                'result': page_ranges
            })
        finally:
            # Clean up the temporary file
            os.remove(temp_pdf_path)

        self.send_response(HTTPStatus.OK)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(response.encode())

    def extract_airway_bills_by_page(self, pdf_path, continuation_keyword):
        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)
        current_bill_pages = []
        all_bills = []

        for page_num in range(total_pages):
            page_text = extract_text(pdf_path, page_numbers=[page_num])
            if page_text.lstrip().startswith(continuation_keyword):
                if current_bill_pages:
                    all_bills.append(current_bill_pages)
                    current_bill_pages = []
                current_bill_pages.append(page_num + 1)
            else:
                if current_bill_pages:
                    current_bill_pages.append(page_num + 1)
        
        if current_bill_pages:
            all_bills.append(current_bill_pages)

        formatted_output = []
        for bill_pages in all_bills:
            if len(bill_pages) == 1:
                formatted_output.append(str(bill_pages[0]))
            else:
                formatted_output.append(f"{bill_pages[0]}-{bill_pages[-1]}")

        return ",".join(formatted_output)


port = int(os.getenv('PORT', 80))
print(f'Listening on port {port}')
httpd = socketserver.TCPServer(('', port), Handler)
httpd.serve_forever()
