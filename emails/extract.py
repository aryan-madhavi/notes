import os
import email
from email import policy
from email.header import decode_header
import quopri
import re
from bs4 import BeautifulSoup
from datetime import datetime

DIR = "sent"
OUTPUT_FILE = "emails.md"


def decode_header_value(value):
    """Decode email header values like Subject, Date, etc."""
    if not value:
        return ""
    decoded_parts = decode_header(value)
    result = ""
    for text, encoding in decoded_parts:
        if isinstance(text, bytes):
            result += text.decode(encoding or "utf-8", errors="ignore")
        else:
            result += text
    return result


# ---------------------------------------------------------
#  HTML → Markdown LIST CONVERSION
# ---------------------------------------------------------

def html_list_to_markdown(soup, level=0):
    """Recursively convert HTML <ul><li> lists to Markdown."""
    output = []
    indent = "  " * level

    for li in soup.find_all("li", recursive=False):
        # Get li text
        text = " ".join(li.get_text(strip=True).split())

        output.append(f"{indent}- {text}")

        # If <li> has nested <ul>, process recursively
        nested_ul = li.find("ul", recursive=False)
        if nested_ul:
            output.extend(html_list_to_markdown(nested_ul, level + 1))

    return output


def html_to_markdown(html):
    """Convert HTML to Markdown, including nested lists."""

    soup = BeautifulSoup(html, "html.parser")

    # Convert all <ul> structures into markdown lists
    for ul in soup.find_all("ul"):
        md_list = html_list_to_markdown(ul)
        ul.replace_with("\n".join(md_list))

    # Convert <br> → newlines
    for br in soup.find_all("br"):
        br.replace_with("\n")

    # Get plain text
    text = soup.get_text("\n")

    # Clean extra spaces
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ---------------------------------------------------------
#   OUTLOOK-STYLE PLAIN TEXT BULLET FIXER
# ---------------------------------------------------------

def fix_bullets(body):
    """
    Convert Outlook-style weird bullets (including indented bullets)
    into proper Markdown nested bullets.
    """

    lines = body.splitlines()
    fixed = []
    pending_bullet = None

    for line in lines:
        stripped = line.strip()

        # Case 1: "*" alone on a line → next line contains text
        if stripped == "*" or stripped == "-":
            pending_bullet = line
            continue

        # Case 2: Proper bullet with indentation
        bullet_match = re.match(r"^(\s*)[\*\-]\s*(.*)$", line)
        if bullet_match:
            indent = len(bullet_match.group(1))
            text = bullet_match.group(2).strip()

            level = indent // 3
            md_indent = "  " * level

            fixed.append(f"{md_indent}- {text}")
            continue

        # Case 3: Previous line was "*" and this line is the actual text
        if pending_bullet is not None:
            indent = len(pending_bullet) - len(pending_bullet.lstrip())
            level = indent // 3
            md_indent = "  " * level
            fixed.append(f"{md_indent}- {stripped}")
            pending_bullet = None
            continue

        fixed.append(stripped)

    return "\n".join(fixed).strip()


# ---------------------------------------------------------
#   BODY EXTRACTOR
# ---------------------------------------------------------

def extract_body(msg):
    """Extract best body (plain preferred, HTML fallback)."""

    # 1. Try plain text first
    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            payload = part.get_payload(decode=True)
            if payload:
                decoded = quopri.decodestring(payload).decode("utf-8", errors="ignore")
                return fix_bullets(decoded)

    # 2. Fallback: HTML conversion
    for part in msg.walk():
        if part.get_content_type() == "text/html":
            payload = part.get_payload(decode=True)
            if payload:
                html = payload.decode("utf-8", errors="ignore")
                md = html_to_markdown(html)
                return fix_bullets(md)

    return ""


# ---------------------------------------------------------
#   DATE PARSER
# ---------------------------------------------------------

def parse_date(date_str):
    """Convert Date header to datetime for sorting."""
    try:
        return datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
    except:
        return datetime.min


# ---------------------------------------------------------
#   MAIN
# ---------------------------------------------------------

def main():
    emails = []

    # Read emails
    for file in os.listdir(DIR):
        if not file.lower().endswith(".eml"):
            continue

        path = os.path.join(DIR, file)

        with open(path, "rb") as f:
            msg = email.message_from_binary_file(f, policy=policy.default)

        subject = decode_header_value(msg.get("Subject", "No Subject"))
        date_raw = decode_header_value(msg.get("Date", "Unknown"))
        body = extract_body(msg)

        emails.append({
            "subject": subject,
            "date_raw": date_raw,
            "date_obj": parse_date(date_raw),
            "body": body
        })

    # Sort by date
    emails.sort(key=lambda x: x["date_obj"])

    # Write all emails to Markdown file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        for e in emails:
            out.write(f"**Subject:** {e['subject']}\n")
            out.write(f"**Date:** {e['date_raw']}\n\n")
            out.write("**Body:**\n\n")
            out.write(e["body"])
            out.write("\n\n---\n\n")

    print(f"Done! Emails processed and saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
