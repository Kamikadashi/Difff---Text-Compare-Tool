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
    """Compare two texts using a sliding window approach to align lines within 15 lines."""
    lines1 = text1.splitlines()
    lines2 = text2.splitlines()
    aligned_lines = []
    window_size = 15
    threshold = 0.5  # Similarity threshold for line matching

    i = 0
    j = 0

    while i < len(lines1) or j < len(lines2):
        # Handle remaining lines when one text is exhausted
        if i >= len(lines1):
            while j < len(lines2):
                highlighted = f'<span class="highlight">{escape_and_preserve(lines2[j])}</span>'
                aligned_lines.append(('', highlighted))
                j += 1
            break
        if j >= len(lines2):
            while i < len(lines1):
                highlighted = f'<span class="highlight">{escape_and_preserve(lines1[i])}</span>'
                aligned_lines.append((highlighted, ''))
                i += 1
            break

        line1 = lines1[i]
        line2 = lines2[j]

        if line1 == line2:
            # Exact match, add as equal
            escaped = escape_and_preserve(line1)
            aligned_lines.append((escaped, escaped))
            i += 1
            j += 1
        else:
            # Search in text2 within window for best match to current line1 (skip empty lines)
            best_j = -1
            best_ratio = 0
            max_j = min(j + window_size, len(lines2))
            for candidate_j in range(j, max_j):
                current_line = lines2[candidate_j]
                if current_line.strip() == '':  # Skip empty lines during search
                    continue
                seq = difflib.SequenceMatcher(None, line1, current_line)
                ratio = seq.ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_j = candidate_j

            # Search in text1 within window for best match to current line2 (skip empty lines)
            best_i = -1
            best_ratio_i = 0
            max_i = min(i + window_size, len(lines1))
            for candidate_i in range(i, max_i):
                current_line = lines1[candidate_i]
                if current_line.strip() == '':  # Skip empty lines during search
                    continue
                seq = difflib.SequenceMatcher(None, line2, current_line)
                ratio = seq.ratio()
                if ratio > best_ratio_i:
                    best_ratio_i = ratio
                    best_i = candidate_i

            # Determine which potential match is better
            if best_ratio >= threshold or best_ratio_i >= threshold:
                if best_ratio >= best_ratio_i:
                    # Insert lines from j to best_j-1 as additions
                    for insert_j in range(j, best_j):
                        highlighted = f'<span class="highlight">{escape_and_preserve(lines2[insert_j])}</span>'
                        aligned_lines.append(('', highlighted))
                    # Align line1 with lines2[best_j] and compare
                    diff_line1, diff_line2 = compare_characters(line1, lines2[best_j])
                    aligned_lines.append((diff_line1, diff_line2))
                    i += 1
                    j = best_j + 1
                else:
                    # Delete lines from i to best_i-1 as removals
                    for delete_i in range(i, best_i):
                        highlighted = f'<span class="highlight">{escape_and_preserve(lines1[delete_i])}</span>'
                        aligned_lines.append((highlighted, ''))
                    # Align lines1[best_i] with line2 and compare
                    diff_line1, diff_line2 = compare_characters(lines1[best_i], line2)
                    aligned_lines.append((diff_line1, diff_line2))
                    i = best_i + 1
                    j += 1
            else:
                # No good match, treat as character-level replacement
                diff_line1, diff_line2 = compare_characters(line1, line2)
                aligned_lines.append((diff_line1, diff_line2))
                i += 1
                j += 1

    # Generate HTML table rows
    html_diff = []
    for left, right in aligned_lines:
        html_diff.append(f'''
            <tr>
                <td class="result-text">{left}</td>
                <td class="result-text">{right}</td>
            </tr>
        ''')
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
