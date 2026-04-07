import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile Safari/604.1'
}

TIME_RE = re.compile(r'\b(?:\d+:)?\d{1,2}\.\d{2}\b')
DATE_RE = re.compile(r'(20\d{2}[\-/]\d{1,2}[\-/]\d{1,2})')


def fetch_results_from_url(url: str):
    res = requests.get(url, headers=HEADERS, timeout=20)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, 'html.parser')

    page_title = soup.title.text.strip() if soup.title else '游泳成績頁'
    tables = soup.find_all('table')
    rows_out = []

    for table in tables:
        headers = [th.get_text(' ', strip=True) for th in table.find_all('th')]
        tr_list = table.find_all('tr')
        for tr in tr_list[1:] if len(tr_list) > 1 else []:
            cells = [td.get_text(' ', strip=True) for td in tr.find_all(['td', 'th'])]
            if not cells or len(cells) < 2:
                continue
            joined = ' | '.join(cells)
            time_match = TIME_RE.search(joined)
            if not time_match:
                continue
            meet_date = ''
            date_match = DATE_RE.search(res.text)
            if date_match:
                meet_date = date_match.group(1).replace('/', '-')

            event_name = ''
            rank_text = ''
            course = ''

            if headers:
                lower_headers = [h.lower() for h in headers]
                for idx, header in enumerate(lower_headers):
                    if idx >= len(cells):
                        continue
                    val = cells[idx]
                    if any(k in header for k in ['項目', 'event', 'distance']):
                        event_name = val
                    elif any(k in header for k in ['名次', 'rank']):
                        rank_text = val
                    elif any(k in header for k in ['池', 'course', '場地']):
                        course = val
            if not event_name:
                event_name = cells[1] if len(cells) > 1 else '未辨識項目'
            if not rank_text and cells:
                rank_text = cells[0]

            rows_out.append({
                'meet_name': page_title,
                'event_name': event_name,
                'course': course,
                'time_text': time_match.group(0),
                'rank_text': rank_text,
                'meet_date': meet_date,
            })

    return rows_out
