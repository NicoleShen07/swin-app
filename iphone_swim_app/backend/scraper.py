import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile Safari/604.1"
}

TIME_RE = re.compile(r'^(?:\d+:)?\d{1,2}\.\d{2}$')
FULL_DATE_RE = re.compile(r'(20\d{2})[\-/](\d{1,2})[\-/](\d{1,2})')
ROC_PATH_YEAR_RE = re.compile(r'/CTSA_(\d{2,3})/')
CTSA_ROW_RE = re.compile(
    r'^(?P<serial>\d+)\s+(?P<schedule>\d+)\s+(?P<mmdd>\d{2}/\d{2})\s+(?P<hhmm>\d{2}:\d{2})\s+'
    r'(?P<event>.+?)\s+(?P<race_type>預賽|決賽|計時決賽|慢組計時決賽|快組計時決賽)\s+(?P<rest>.+)$'
)


def normalize_space(text: str) -> str:
    return re.sub(r'\s+', ' ', (text or '')).strip()


def detect_course(text: str) -> str:
    text = text or ''
    if '短水道' in text:
        return '短水道'
    if '長水道' in text:
        return '長水道'
    return ''


def infer_year_from_url(url: str):
    m = ROC_PATH_YEAR_RE.search(url)
    if not m:
        return None
    roc = int(m.group(1))
    if 1 <= roc <= 199:
        return roc + 1911
    return None


def parse_mmdd_to_date(mmdd: str, year_hint: int | None) -> str:
    if not mmdd:
        return ''
    if not year_hint:
        return mmdd.replace('/', '-')
    month, day = mmdd.split('/')
    return f"{year_hint:04d}-{int(month):02d}-{int(day):02d}"


def parse_ctsa_text_lines(text: str, swimmer_name: str = '', url: str = ''):
    lines = [normalize_space(x) for x in text.splitlines()]
    lines = [x for x in lines if x]

    meet_name = '中華民國游泳協會成績頁'
    for line in lines:
        if '年' in line and ('游泳錦標賽' in line or '全中運' in line or '分齡' in line or '青年盃' in line or '排名賽' in line):
            meet_name = line
            break

    year_hint = infer_year_from_url(url)
    page_course = detect_course(' '.join(lines[:80]))
    rows_out = []
    in_results = False

    for line in lines:
        if '序號 賽程編號 時間 項目名稱 賽別 單位 參賽者 成績 名次 狀態 組次 水道' in line:
            in_results = True
            continue
        if not in_results:
            continue
        if line.startswith('即時成績僅供參考') or line.startswith('中華民國游泳協會') or line.startswith('聯絡我們'):
            break

        m = CTSA_ROW_RE.match(line)
        if not m:
            continue

        rest_tokens = m.group('rest').split()
        if len(rest_tokens) < 2:
            continue

        team_name = rest_tokens[0]
        participant = rest_tokens[1]
        tail = rest_tokens[2:]

        if swimmer_name and swimmer_name.strip() and participant != swimmer_name.strip():
            continue

        time_text = ''
        rank_text = ''
        status_text = ''
        if tail:
            if TIME_RE.match(tail[0]):
                time_text = tail[0]
                tail = tail[1:]
            elif tail[0] in {'未檢錄', '請假', 'DQ', 'DNS', 'DNF'}:
                status_text = tail[0]
                tail = tail[1:]

        if tail:
            if tail[0].isdigit():
                rank_text = tail[0]
                tail = tail[1:]
            elif not status_text:
                status_text = tail[0]
                tail = tail[1:]

        if not time_text:
            # 不把未檢錄/請假匯入成績，以免造成 PB 混亂
            continue

        event_name = f"{m.group('event')} {m.group('race_type')}".strip()
        rows_out.append({
            'meet_name': meet_name,
            'event_name': event_name,
            'course': page_course,
            'time_text': time_text,
            'rank_text': rank_text,
            'meet_date': parse_mmdd_to_date(m.group('mmdd'), year_hint),
            'team_name': team_name,
            'participant': participant,
            'raw_status': status_text,
        })
    return rows_out


TABLE_KEYWORDS = ['項目', '賽別', '參賽者', '成績']


def parse_html_tables(html: str, swimmer_name: str = '', url: str = ''):
    soup = BeautifulSoup(html, 'html.parser')
    page_title = normalize_space(soup.title.get_text()) if soup.title else '游泳成績頁'
    page_text = normalize_space(soup.get_text('\n', strip=True))
    meet_date = ''
    date_match = FULL_DATE_RE.search(page_text)
    if date_match:
        y, m, d = date_match.groups()
        meet_date = f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
    page_course = detect_course(page_title + ' ' + page_text)

    rows_out = []
    for table in soup.find_all('table'):
        header_cells = [normalize_space(th.get_text(' ', strip=True)) for th in table.find_all('th')]
        if header_cells and not any(any(k in h for k in TABLE_KEYWORDS) for h in header_cells):
            continue
        tr_list = table.find_all('tr')
        if not tr_list:
            continue
        for tr in tr_list[1:] if len(tr_list) > 1 else []:
            cells = [normalize_space(td.get_text(' ', strip=True)) for td in tr.find_all(['td', 'th'])]
            if len(cells) < 4:
                continue
            joined = ' | '.join(cells)
            times = [c for c in cells if TIME_RE.match(c)]
            if not times:
                continue
            if swimmer_name and swimmer_name.strip() and swimmer_name.strip() not in joined:
                continue

            event_name = ''
            rank_text = ''
            for idx, header in enumerate(header_cells):
                if idx >= len(cells):
                    continue
                if '項目' in header:
                    event_name = cells[idx]
                if '名次' in header:
                    rank_text = cells[idx]
            if not event_name:
                event_name = cells[1] if len(cells) > 1 else '未辨識項目'

            rows_out.append({
                'meet_name': page_title,
                'event_name': event_name,
                'course': page_course,
                'time_text': times[0],
                'rank_text': rank_text,
                'meet_date': meet_date,
            })
    return rows_out


def dedupe_rows(rows):
    seen = set()
    out = []
    for row in rows:
        key = (
            row.get('meet_name', ''),
            row.get('event_name', ''),
            row.get('time_text', ''),
            row.get('rank_text', ''),
            row.get('meet_date', ''),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def fetch_results_from_url(url: str, swimmer_name: str = ''):
    res = requests.get(url, headers=HEADERS, timeout=25)
    res.raise_for_status()
    html = res.text

    hostname = urlparse(url).netloc.lower()
    page_text = BeautifulSoup(html, 'html.parser').get_text('\n', strip=True)

    rows = []
    if 'ctsa.utk.com.tw' in hostname or 'swimming.org.tw' in hostname or '中華民國游泳協會' in page_text:
        rows.extend(parse_ctsa_text_lines(page_text, swimmer_name=swimmer_name, url=url))
    rows.extend(parse_html_tables(html, swimmer_name=swimmer_name, url=url))
    return dedupe_rows(rows)
