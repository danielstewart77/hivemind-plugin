#!/usr/bin/env python3
"""Convert documents to PDF."""

import sys
import pathlib

def md_to_pdf(input_path: str, output_path: str) -> None:
    import markdown
    from weasyprint import HTML

    source = pathlib.Path(input_path).read_text(encoding="utf-8")
    html_body = markdown.markdown(source, extensions=["tables", "fenced_code"])
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: Georgia, serif; max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.6; color: #222; }}
  h1, h2, h3, h4, h5, h6 {{ font-family: Arial, sans-serif; color: #111; margin-top: 1.4em; }}
  code {{ background: #f4f4f4; padding: 2px 5px; border-radius: 3px; font-size: 0.9em; }}
  pre {{ background: #f4f4f4; padding: 12px; border-radius: 4px; overflow-x: auto; }}
  pre code {{ background: none; padding: 0; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border: 1px solid #ccc; padding: 6px 12px; }}
  th {{ background: #f0f0f0; }}
  blockquote {{ border-left: 4px solid #ccc; margin: 0; padding-left: 16px; color: #555; }}
</style>
</head>
<body>
{html_body}
</body>
</html>"""
    HTML(string=html, base_url=str(pathlib.Path(input_path).parent.resolve())).write_pdf(output_path)

def main():
    if len(sys.argv) < 3:
        print("Usage: convert_to_pdf.py <input> <output>", file=sys.stderr)
        sys.exit(1)

    input_path, output_path = sys.argv[1], sys.argv[2]
    ext = pathlib.Path(input_path).suffix.lower()

    if ext == ".md":
        md_to_pdf(input_path, output_path)
    else:
        print(f"Unsupported format: {ext}", file=sys.stderr)
        sys.exit(1)

    print(f"Saved: {output_path}")

if __name__ == "__main__":
    main()
