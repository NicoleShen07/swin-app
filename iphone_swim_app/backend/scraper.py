import requests
from bs4 import BeautifulSoup

def fetch_results_from_url(url, swimmer_name=None):
    results = []

    try:
        res = requests.get(url, timeout=10)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, "html.parser")

        tables = soup.find_all("table")

        for table in tables:
            rows = table.find_all("tr")

            for row in rows:
                cols = [c.get_text(strip=True) for c in row.find_all("td")]

                if len(cols) < 3:
                    continue

                text = " ".join(cols)

                # 如果有指定選手名稱，只抓該選手
                if swimmer_name and swimmer_name not in text:
                    continue

                # 過濾無效資料
                if "棄權" in text or "未" in text:
                    continue

                result = {
                    "event": cols[0] if len(cols) > 0 else "",
                    "time": cols[1] if len(cols) > 1 else "",
                    "rank": cols[2] if len(cols) > 2 else "",
                    "date": ""
                }

                results.append(result)

        return results

    except Exception as e:
        print("抓取錯誤:", e)
        return []
