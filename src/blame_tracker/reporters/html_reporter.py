"""HTML report generator with syntax highlighting."""

from datetime import datetime
from pathlib import Path
from typing import List

from jinja2 import Environment, Template
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.lexers.special import TextLexer

from blame_tracker.models import BlameAnalysis, BlameLineGroup, BlameResult


class HtmlReporter:
    """Generate professional HTML reports."""

    def __init__(self, output_path: str) -> None:
        """Initialize HTML reporter.

        Args:
            output_path: Path where to write the HTML report
        """
        self.output_path = Path(output_path)

    def generate(self, analysis: BlameAnalysis) -> None:
        """Generate HTML report from blame analysis.

        Args:
            analysis: BlameAnalysis object with results
        """
        html_content = self._render_html(analysis)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(html_content, encoding="utf-8")

    def _render_html(self, analysis: BlameAnalysis) -> str:
        """Render complete HTML report.

        Args:
            analysis: BlameAnalysis object

        Returns:
            HTML string
        """
        template = self._get_template()
        return template.render(
            analysis=analysis,
            generation_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            results=analysis.results,
            top_culprits=analysis.get_top_culprits(),
            render_code_lines=self._render_code_lines,
        )

    def _get_template(self) -> Template:
        """Get Jinja2 template for HTML report."""
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Code Coverage Analysis Report</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
        }

        header {
            background: #1a1a2e;
            color: white;
            padding: 30px 40px;
            border-bottom: 3px solid #0084d4;
        }

        header h1 {
            font-size: 2em;
            margin-bottom: 5px;
            font-weight: 600;
        }

        header p {
            font-size: 0.95em;
            opacity: 0.9;
        }

        .metrics-section {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            padding: 25px 40px;
            background: #f9f9f9;
            border-bottom: 1px solid #e5e5e5;
        }

        .metric-card {
            background: white;
            padding: 15px;
            border-radius: 4px;
            border-left: 3px solid #0084d4;
        }

        .metric-card h3 {
            font-size: 0.75em;
            text-transform: uppercase;
            color: #666;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
            font-weight: 600;
        }

        .metric-card .value {
            font-size: 2em;
            font-weight: bold;
            color: #1a1a2e;
            margin-bottom: 5px;
        }

        .metric-card .unit {
            font-size: 0.85em;
            color: #999;
        }

        .content {
            padding: 40px;
        }

        .section {
            margin-bottom: 35px;
        }

        .section h2 {
            font-size: 1.5em;
            color: #1a1a2e;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid #e5e5e5;
            font-weight: 600;
        }

        .files-grid {
            display: grid;
            gap: 20px;
        }

        .file-card {
            background: white;
            border: 1px solid #e5e5e5;
            border-radius: 4px;
            overflow: hidden;
        }

        .file-header {
            background: #f9f9f9;
            padding: 15px 20px;
            border-bottom: 1px solid #e5e5e5;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            user-select: none;
        }

        .file-header:hover {
            background: #f0f0f0;
        }

        .file-name {
            font-weight: 600;
            color: #1a1a2e;
            font-size: 0.95em;
        }

        .file-stats {
            display: flex;
            gap: 20px;
            font-size: 0.85em;
        }

        .file-stat {
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .stat-label {
            color: #666;
        }

        .stat-value {
            font-weight: 600;
            color: #1a1a2e;
        }

        .toggle-icon {
            font-size: 0.8em;
            color: #999;
            transition: transform 0.2s;
        }

        .toggle-icon.expanded {
            transform: rotate(180deg);
        }

        .file-content {
            display: none;
            padding: 20px;
        }

        .file-content.expanded {
            display: block;
        }

        .blame-group {
            background: #f9f9f9;
            border: 1px solid #e5e5e5;
            border-radius: 4px;
            margin-bottom: 15px;
            overflow: hidden;
        }

        .blame-info {
            padding: 12px 15px;
            background: white;
            border-bottom: 1px solid #e5e5e5;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
            font-size: 0.85em;
        }

        .blame-info-item {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .blame-info-label {
            font-weight: 600;
            color: #666;
            text-transform: uppercase;
            font-size: 0.75em;
            letter-spacing: 0.5px;
        }

        .blame-info-value {
            color: #1a1a2e;
            font-family: monospace;
            font-size: 0.9em;
        }

        .code-viewer {
            position: relative;
        }

        .code-tabs {
            display: flex;
            background: #f9f9f9;
            border-bottom: 1px solid #e5e5e5;
            padding: 0 15px;
            gap: 0;
        }

        .code-tab {
            padding: 10px 15px;
            background: transparent;
            border: none;
            cursor: pointer;
            font-size: 0.85em;
            color: #666;
            border-bottom: 2px solid transparent;
            transition: all 0.2s;
        }

        .code-tab:hover {
            color: #0084d4;
        }

        .code-tab.active {
            color: #0084d4;
            border-bottom-color: #0084d4;
        }

        .code-content {
            display: none;
        }

        .code-content.active {
            display: block;
        }

        .code-block {
            background: #1a1a2e;
            padding: 15px;
            overflow-x: auto;
            font-family: "Courier New", monospace;
            font-size: 0.85em;
            color: #e5e5e5;
        }

        .code-line {
            display: flex;
            gap: 0;
            min-height: 1.4em;
        }

        .line-number {
            color: #666;
            padding-right: 20px;
            text-align: right;
            min-width: 50px;
            user-select: none;
            flex-shrink: 0;
            background: #0f0f1e;
        }

        .line-indicator {
            min-width: 25px;
            text-align: center;
            padding-right: 10px;
            user-select: none;
            flex-shrink: 0;
            background: #0f0f1e;
            color: #666;
        }

        .line-indicator.added {
            color: #4caf50;
            font-weight: bold;
        }

        .line-indicator.removed {
            color: #f44336;
            font-weight: bold;
        }

        .line-content {
            flex: 1;
            white-space: pre-wrap;
            word-break: break-word;
            color: #e5e5e5;
        }

        .line-content.added {
            background: rgba(76, 175, 80, 0.1);
            color: #81c784;
        }

        .line-content.removed {
            background: rgba(244, 67, 54, 0.1);
            color: #e57373;
        }

        .line-content.context {
            color: #b0bec5;
        }

        .diff-view {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0;
            background: #1a1a2e;
        }

        .diff-side {
            border-right: 1px solid #0f0f1e;
        }

        .diff-side:last-child {
            border-right: none;
        }

        .diff-title {
            padding: 10px 15px;
            background: #0f0f1e;
            color: #999;
            font-size: 0.8em;
            font-weight: 600;
            border-bottom: 1px solid #333;
        }

        .no-results {
            text-align: center;
            padding: 40px;
            color: #999;
        }

        .no-results p {
            font-size: 1em;
            margin-bottom: 5px;
        }

        footer {
            background: #f9f9f9;
            padding: 20px 40px;
            text-align: center;
            color: #999;
            border-top: 1px solid #e5e5e5;
            font-size: 0.85em;
        }

        @media (max-width: 768px) {
            .metrics-section {
                grid-template-columns: 1fr 1fr;
                padding: 15px 20px;
            }

            .file-stats {
                flex-wrap: wrap;
                gap: 10px;
            }

            .diff-view {
                grid-template-columns: 1fr;
            }

            .diff-side {
                border-right: none;
                border-bottom: 1px solid #0f0f1e;
            }

            .diff-side:last-child {
                border-bottom: none;
            }

            header {
                padding: 20px;
            }

            .content {
                padding: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Code Coverage Analysis</h1>
            <p>Recently modified covered code in version control</p>
        </header>

        <div class="metrics-section">
            <div class="metric-card">
                <h3>Total Covered Lines</h3>
                <div class="value">{{ analysis.total_uncovered }}</div>
                <div class="unit">across all files</div>
            </div>
            <div class="metric-card">
                <h3>Recently Changed</h3>
                <div class="value">{{ analysis.total_culprit }}</div>
                <div class="unit">lines modified</div>
            </div>
            <div class="metric-card">
                <h3>Change Density</h3>
                <div class="value">{{ "%.1f"|format(analysis.culprit_percentage) }}%</div>
                <div class="unit">of covered code</div>
            </div>
            <div class="metric-card">
                <h3>Analysis Details</h3>
                <div class="unit">Last {{ analysis.days_lookback }} days</div>
                <div class="unit">{{ analysis.results|length }} files analyzed</div>
            </div>
        </div>

        <div class="content">
            {% if analysis.results %}
            <div class="section">
                <h2>Modified Files</h2>
                <div class="files-grid">
                    {% for result in results %}
                    <div class="file-card">
                        <div class="file-header" onclick="toggleFileContent(this)">
                            <div>
                                <div class="file-name">{{ result.file_path }}</div>
                            </div>
                            <div class="file-stats">
                                <div class="file-stat">
                                    <span class="stat-label">Covered:</span>
                                    <span class="stat-value">{{ result.total_uncovered_lines }}</span>
                                </div>
                                <div class="file-stat">
                                    <span class="stat-label">Recently Changed:</span>
                                    <span class="stat-value">{{ result.uncovered_in_changes }}</span>
                                </div>
                                <div class="file-stat">
                                    <span class="stat-label">Coverage:</span>
                                    <span class="stat-value">{{ "%.1f"|format(result.culprit_percentage) }}%</span>
                                </div>
                                <span class="toggle-icon">▼</span>
                            </div>
                        </div>

                        <div class="file-content">
                            {% for group in result.blame_groups %}
                            <div class="blame-group">
                                <div class="blame-info">
                                    <div class="blame-info-item">
                                        <span class="blame-info-label">Lines</span>
                                        <span class="blame-info-value">{{ group.start_line }}-{{ group.end_line }}</span>
                                    </div>
                                    {% for change in group.git_changes %}
                                    <div class="blame-info-item">
                                        <span class="blame-info-label">Author</span>
                                        <span class="blame-info-value">{{ change.author }}</span>
                                    </div>
                                    <div class="blame-info-item">
                                        <span class="blame-info-label">Commit</span>
                                        <span class="blame-info-value">{{ change.commit_hash }}</span>
                                    </div>
                                    <div class="blame-info-item">
                                        <span class="blame-info-label">Date</span>
                                        <span class="blame-info-value">{{ change.commit_date[:10] }}</span>
                                    </div>
                                    <div class="blame-info-item">
                                        <span class="blame-info-label">Message</span>
                                        <span class="blame-info-value">{{ change.commit_message }}</span>
                                    </div>
                                    {% endfor %}
                                </div>

                                <div class="code-viewer">
                                    <div class="code-tabs">
                                        <button class="code-tab active" onclick="switchCodeView(this, 'unified')">Unified View</button>
                                        <button class="code-tab" onclick="switchCodeView(this, 'diff')">Side by Side</button>
                                    </div>

                                    <div class="code-content active" id="unified-view">
                                        <div class="code-block">
                                            {{ render_code_lines(group) }}
                                        </div>
                                    </div>

                                    <div class="code-content" id="diff-view">
                                        <div class="code-block">
                                            <div class="diff-view">
                                                <div class="diff-side">
                                                    <div class="diff-title">Before</div>
                                                    <div>
                                                        {% for line in group.context_before %}
                                                        <div class="code-line">
                                                            <div class="line-number"></div>
                                                            <div class="line-indicator"></div>
                                                            <div class="line-content context">{{ line }}</div>
                                                        </div>
                                                        {% endfor %}
                                                    </div>
                                                </div>
                                                <div class="diff-side">
                                                    <div class="diff-title">After</div>
                                                    <div>
                                                        {% for line in group.context_before %}
                                                        <div class="code-line">
                                                            <div class="line-number"></div>
                                                            <div class="line-indicator"></div>
                                                            <div class="line-content context">{{ line }}</div>
                                                        </div>
                                                        {% endfor %}
                                                        {% for line in group.culprit_lines %}
                                                        <div class="code-line">
                                                            <div class="line-number"></div>
                                                            <div class="line-indicator added">+</div>
                                                            <div class="line-content added">{{ line }}</div>
                                                        </div>
                                                        {% endfor %}
                                                        {% for line in group.context_after %}
                                                        <div class="code-line">
                                                            <div class="line-number"></div>
                                                            <div class="line-indicator"></div>
                                                            <div class="line-content context">{{ line }}</div>
                                                        </div>
                                                        {% endfor %}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% else %}
            <div class="no-results">
                <p>No covered lines found in recent changes</p>
                <p style="font-size: 0.9em;">No covered code was modified in recent commits.</p>
            </div>
            {% endif %}
        </div>

        <footer>
            <p>Generated: {{ generation_date }}</p>
            <p>Lookback period: {{ analysis.days_lookback }} days | Files analyzed: {{ analysis.results|length }}</p>
        </footer>
    </div>

    <script>
        function toggleFileContent(header) {
            const content = header.nextElementSibling;
            const icon = header.querySelector('.toggle-icon');
            content.classList.toggle('expanded');
            icon.classList.toggle('expanded');
        }

        function switchCodeView(button, view) {
            // Get the parent code-viewer
            const viewer = button.closest('.code-viewer');

            // Update active tab
            viewer.querySelectorAll('.code-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            button.classList.add('active');

            // Update active content
            viewer.querySelectorAll('.code-content').forEach(content => {
                content.classList.remove('active');
            });

            const viewId = view === 'unified' ? 'unified-view' : 'diff-view';
            viewer.querySelector('#' + viewId).classList.add('active');
        }
    </script>
</body>
</html>
"""
        return Environment().from_string(html_template)

    def _render_code_lines(self, group: BlameLineGroup) -> str:
        """Render code lines with syntax highlighting.

        Args:
            group: BlameLineGroup with code lines

        Returns:
            HTML string with formatted code
        """
        # Determine language
        language = group.language if group.language else "text"

        # Combine all lines
        all_lines = []

        # Add context before
        for line in group.context_before:
            all_lines.append(("context", line))

        # Add culprit lines
        for line in group.culprit_lines:
            all_lines.append(("culprit", line))

        # Add context after
        for line in group.context_after:
            all_lines.append(("context", line))

        # Render each line
        html_lines = []
        line_num = max(1, group.start_line - len(group.context_before))

        for line_type, line_content in all_lines:
            indicator = "+" if line_type == "culprit" else ""
            indicator_class = "added" if line_type == "culprit" else ""
            content_class = line_type

            html_lines.append(
                f'<div class="code-line">'
                f'<div class="line-number">{line_num}</div>'
                f'<div class="line-indicator {indicator_class}">{indicator}</div>'
                f'<div class="line-content {content_class}">{line_content}</div>'
                f'</div>'
            )
            line_num += 1

        return "\n".join(html_lines)
