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
    """Generate beautiful HTML reports."""

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
        )

    def _get_template(self) -> Template:
        """Get Jinja2 template for HTML report."""
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blame Tracker Report</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            line-height: 1.6;
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            overflow: hidden;
        }

        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
        }

        header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 30px 20px;
            background: #f8f9fa;
            border-bottom: 2px solid #e9ecef;
        }

        .summary-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            text-align: center;
        }

        .summary-card h3 {
            color: #667eea;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }

        .summary-card .value {
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }

        .summary-card .unit {
            color: #999;
            font-size: 0.9em;
            margin-top: 5px;
        }

        .progress-bar {
            width: 100%;
            height: 8px;
            background: #e9ecef;
            border-radius: 4px;
            margin-top: 10px;
            overflow: hidden;
        }

        .progress-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 4px;
        }

        .content {
            padding: 30px 20px;
        }

        .section {
            margin-bottom: 40px;
        }

        .section h2 {
            color: #667eea;
            font-size: 1.8em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }

        .file-result {
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 4px;
        }

        .file-result h3 {
            color: #333;
            margin-bottom: 10px;
            font-size: 1.1em;
        }

        .file-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 15px;
        }

        .stat {
            padding: 10px;
            background: white;
            border-radius: 4px;
            border-left: 3px solid #764ba2;
        }

        .stat-label {
            font-size: 0.85em;
            color: #999;
            text-transform: uppercase;
            margin-bottom: 5px;
        }

        .stat-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #333;
        }

        .blame-group {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            margin-top: 15px;
            overflow: hidden;
        }

        .blame-header {
            background: #f8f9fa;
            padding: 15px;
            border-bottom: 1px solid #e9ecef;
        }

        .blame-header h4 {
            color: #333;
            margin-bottom: 8px;
            font-size: 0.95em;
        }

        .blame-info {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            font-size: 0.85em;
            color: #666;
        }

        .blame-info-item {
            display: flex;
            gap: 5px;
        }

        .blame-info-label {
            font-weight: bold;
            color: #333;
            min-width: 80px;
        }

        .code-block {
            overflow-x: auto;
            background: #f5f5f5;
        }

        .code-block pre {
            margin: 0;
            padding: 15px;
            background: #f5f5f5;
            font-family: "Courier New", monospace;
            font-size: 0.9em;
            line-height: 1.4;
        }

        .code-line {
            display: flex;
            align-items: baseline;
        }

        .line-number {
            color: #999;
            padding-right: 15px;
            text-align: right;
            min-width: 50px;
            user-select: none;
        }

        .line-content {
            flex: 1;
            word-break: break-word;
            white-space: pre-wrap;
        }

        .context-before .code-line,
        .context-after .code-line {
            opacity: 0.7;
        }

        .culprit-lines {
            background: #fff5f5;
            border-left: 3px solid #dc3545;
        }

        .culprit-lines .code-line {
            background: #fff5f5;
        }

        .culprit-lines .line-number {
            color: #dc3545;
            font-weight: bold;
        }

        /* Syntax highlighting styles */
        .highlight {
            background: transparent;
            padding: 0;
        }

        footer {
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #999;
            border-top: 1px solid #e9ecef;
            font-size: 0.9em;
        }

        .meta-info {
            color: #666;
            font-size: 0.95em;
            margin-bottom: 5px;
        }

        .metric {
            display: inline-block;
            margin-right: 20px;
        }

        .metric-value {
            font-weight: bold;
            color: #667eea;
        }

        .no-results {
            text-align: center;
            padding: 40px;
            color: #999;
        }

        .no-results p {
            font-size: 1.1em;
            margin-bottom: 10px;
        }

        @media (max-width: 768px) {
            header h1 {
                font-size: 1.8em;
            }

            .summary-grid {
                grid-template-columns: 1fr;
            }

            .file-stats {
                grid-template-columns: 1fr;
            }

            .blame-info {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Blame Tracker Report</h1>
            <p>Coverage gaps intersected with recent changes</p>
        </header>

        <div class="summary-grid">
            <div class="summary-card">
                <h3>Total Uncovered Lines</h3>
                <div class="value">{{ analysis.total_uncovered }}</div>
                <div class="unit">lines</div>
            </div>
            <div class="summary-card">
                <h3>Culprit Lines</h3>
                <div class="value">{{ analysis.total_culprit }}</div>
                <div class="unit">lines</div>
                <div class="progress-bar">
                    <div class="progress-bar-fill" style="width: {{ analysis.culprit_percentage }}%"></div>
                </div>
            </div>
            <div class="summary-card">
                <h3>Culprit Percentage</h3>
                <div class="value">{{ "%.1f"|format(analysis.culprit_percentage) }}%</div>
                <div class="unit">of uncovered</div>
            </div>
            <div class="summary-card">
                <h3>Analysis Parameters</h3>
                <div class="unit">Last {{ analysis.days_lookback }} days</div>
                <div class="unit">{{ analysis.results|length }} files analyzed</div>
            </div>
        </div>

        <div class="content">
            {% if analysis.results %}
            <div class="section">
                <h2>📍 Top Culprits</h2>
                {% for result in top_culprits[:10] %}
                <div class="file-result">
                    <h3>{{ result.file_path }}</h3>
                    <div class="file-stats">
                        <div class="stat">
                            <div class="stat-label">Uncovered</div>
                            <div class="stat-value">{{ result.total_uncovered_lines }}</div>
                        </div>
                        <div class="stat">
                            <div class="stat-label">Culprits</div>
                            <div class="stat-value">{{ result.uncovered_in_changes }}</div>
                        </div>
                        <div class="stat">
                            <div class="stat-label">Percentage</div>
                            <div class="stat-value">{{ "%.1f"|format(result.culprit_percentage) }}%</div>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>

            <div class="section">
                <h2>🔍 Detailed Analysis</h2>
                {% for result in results %}
                <div class="file-result">
                    <h3>{{ result.file_path }}</h3>
                    <div class="file-stats">
                        <div class="stat">
                            <div class="stat-label">Total Uncovered</div>
                            <div class="stat-value">{{ result.total_uncovered_lines }}</div>
                        </div>
                        <div class="stat">
                            <div class="stat-label">In Recent Changes</div>
                            <div class="stat-value">{{ result.uncovered_in_changes }}</div>
                        </div>
                        <div class="stat">
                            <div class="stat-label">Percentage</div>
                            <div class="stat-value">{{ "%.1f"|format(result.culprit_percentage) }}%</div>
                        </div>
                    </div>

                    {% for group in result.blame_groups %}
                    <div class="blame-group">
                        <div class="blame-header">
                            <h4>Lines {{ group.start_line }}-{{ group.end_line }}</h4>
                            <div class="blame-info">
                                {% for change in group.git_changes %}
                                <div class="blame-info-item">
                                    <span class="blame-info-label">Author:</span>
                                    <span>{{ change.author }}</span>
                                </div>
                                <div class="blame-info-item">
                                    <span class="blame-info-label">Commit:</span>
                                    <span>{{ change.commit_hash }}</span>
                                </div>
                                <div class="blame-info-item">
                                    <span class="blame-info-label">Date:</span>
                                    <span>{{ change.commit_date[:10] }}</span>
                                </div>
                                <div class="blame-info-item">
                                    <span class="blame-info-label">Message:</span>
                                    <span>{{ change.commit_message }}</span>
                                </div>
                                {% endfor %}
                            </div>
                        </div>
                        <div class="code-block">
                            <pre>{{ self._render_code_lines(group) }}</pre>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% endfor %}
            </div>
            {% else %}
            <div class="no-results">
                <p>✓ No coverage gaps found in recent changes!</p>
                <p>All newly added code is properly covered by tests.</p>
            </div>
            {% endif %}
        </div>

        <footer>
            <div class="meta-info">
                <p>Generated: {{ generation_date }}</p>
                <p>
                    <span class="metric">Lookback period: <span class="metric-value">{{ analysis.days_lookback }} days</span></span>
                    <span class="metric">Files analyzed: <span class="metric-value">{{ results|length }}</span></span>
                </p>
            </div>
        </footer>
    </div>
</body>
</html>
        """

        env = Environment()
        template = env.from_string(html_template)

        # Add custom filter for rendering code
        template.globals["self"] = self

        return template

    def _render_code_lines(self, group: BlameLineGroup) -> str:
        """Render code lines with syntax highlighting.

        Args:
            group: BlameLineGroup with code

        Returns:
            HTML string with highlighted code
        """
        try:
            lexer = get_lexer_by_name(group.language)
        except Exception:
            lexer = TextLexer()

        formatter = HtmlFormatter(
            style="monokai",
            noclasses=True,
            nobackground=True,
        )

        result_html = ""

        # Context before
        for i, line in enumerate(group.context_before):
            line_num = group.start_line - len(group.context_before) + i
            result_html += self._format_code_line(
                line,
                line_num,
                "context-before",
            )

        # Culprit lines
        for i, line in enumerate(group.culprit_lines):
            line_num = group.start_line + i
            result_html += self._format_code_line(
                line,
                line_num,
                "culprit-lines",
            )

        # Context after
        for i, line in enumerate(group.context_after):
            line_num = group.end_line + 1 + i
            result_html += self._format_code_line(
                line,
                line_num,
                "context-after",
            )

        return result_html

    def _format_code_line(
        self,
        content: str,
        line_num: int,
        css_class: str,
    ) -> str:
        """Format a single code line with line number.

        Args:
            content: Line content
            line_num: Line number
            css_class: CSS class for styling

        Returns:
            HTML string
        """
        # Escape HTML
        content = (
            content.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

        return f'<div class="code-line {css_class}"><span class="line-number">{line_num}</span><span class="line-content">{content}</span></div>\n'
