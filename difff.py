import difflib
import html
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs

def escape_and_preserve(text):
    """Escape HTML characters and preserve spaces and tabs."""
    return html.escape(text).replace(" ", "&nbsp;").replace("\t", "&nbsp;&nbsp;&nbsp;&nbsp;")

def compare_characters(line1, line2):
    """Compare two lines character by character and highlight differences."""
    seq_matcher = difflib.SequenceMatcher(None, line1, line2, autojunk=False)
    diff_line1 = []
    diff_line2 = []

    for tag, i1, i2, j1, j2 in seq_matcher.get_opcodes():
        if tag == 'equal':
            diff_line1.append(escape_and_preserve(line1[i1:i2]))
            diff_line2.append(escape_and_preserve(line2[j1:j2]))
        elif tag in ('replace', 'delete'):
            chunk1 = line1[i1:i2]
            diff_line1.append(f'<span class="highlight">{escape_and_preserve(chunk1)}</span>')
        if tag in ('replace', 'insert'):
            chunk2 = line2[j1:j2]
            diff_line2.append(f'<span class="highlight">{escape_and_preserve(chunk2)}</span>')

    return ''.join(diff_line1), ''.join(diff_line2)

def compare_texts(text1, text2):
    """Compare two texts line by line and character by character."""
    lines1 = text1.splitlines()
    lines2 = text2.splitlines()
    matcher = difflib.SequenceMatcher(None, lines1, lines2, autojunk=False)
    
    aligned_lines = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            for line in lines1[i1:i2]:
                escaped = escape_and_preserve(line)
                aligned_lines.append((escaped, escaped))
        elif tag == 'replace':
            len1 = i2 - i1
            len2 = j2 - j1
            max_len = max(len1, len2)
            for idx in range(max_len):
                if idx < len1 and idx < len2:
                    line1 = lines1[i1 + idx]
                    line2 = lines2[j1 + idx]
                    # Perform character-level diff regardless of similarity
                    diff_line1, diff_line2 = compare_characters(line1, line2)
                    aligned_lines.append((diff_line1, diff_line2))
                elif idx < len1:
                    line1 = lines1[i1 + idx]
                    highlighted1 = f'<span class="highlight">{escape_and_preserve(line1)}</span>'
                    aligned_lines.append((highlighted1, ''))
                elif idx < len2:
                    line2 = lines2[j1 + idx]
                    highlighted2 = f'<span class="highlight">{escape_and_preserve(line2)}</span>'
                    aligned_lines.append(('', highlighted2))
        elif tag == 'delete':
            for line in lines1[i1:i2]:
                highlighted1 = f'<span class="highlight">{escape_and_preserve(line)}</span>'
                aligned_lines.append((highlighted1, ''))
        elif tag == 'insert':
            for line in lines2[j1:j2]:
                highlighted2 = f'<span class="highlight">{escape_and_preserve(line)}</span>'
                aligned_lines.append(('', highlighted2))
    
    # Generate HTML table rows
    html_diff = []
    for left, right in aligned_lines:
        html_diff.append(f'''
            <tr>
                <td class="result-text">{left}</td>
                <td class="result-text">{right}</td>
            </tr>
        ''')
    
    # Combine all rows into a single HTML string
    full_html_diff = ''.join(html_diff)
    return full_html_diff


def get_stats(text):
    """Generate statistics about the text."""
    words = len(text.split())
    chars = len(text)
    spaces = text.count(' ')
    linefeeds = text.count('\n')
    return f"{words} words<br>{chars} chars<br>{spaces} spaces (sum: {chars} chars)<br>{linefeeds} linefeeds (sum: {chars + linefeeds} chars)"

class DiffHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        with open('difff_template.html', 'r') as f:
            template = f.read()
        
        self.wfile.write(template.encode())

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        params = parse_qs(post_data)
        
        text1 = params.get('sequenceA', [''])[0]
        text2 = params.get('sequenceB', [''])[0]
        
        diff_result = compare_texts(text1, text2)
        stats1 = get_stats(text1)
        stats2 = get_stats(text2)
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        with open('difff_template.html', 'r') as f:
            template = f.read()
        
        # Insert the diff_result into the template
        result_html = template.replace('<!-- DIFF_RESULT -->', f'''
            <table class="diff-table">
                <thead>
                    <tr>
                        <th>Text A</th>
                        <th>Text B</th>
                    </tr>
                </thead>
                <tbody>
                    {diff_result}
                </tbody>
            </table>
            <div class="stats-container">
                <div class="column">
                    <div class="stats">{stats1}</div>
                </div>
                <div class="column">
                    <div class="stats">{stats2}</div>
                </div>
            </div>
        ''')
        result_html = result_html.replace('VALUE_A', html.escape(text1))
        result_html = result_html.replace('VALUE_B', html.escape(text2))
        
        self.wfile.write(result_html.encode())

def run(server_class=HTTPServer, handler_class=DiffHandler, port=8004):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting server on port {port}")
    webbrowser.open(f'http://localhost:{port}')
    httpd.serve_forever()

if __name__ == '__main__':
    run()
