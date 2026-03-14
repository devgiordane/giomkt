"""Natural language parser for task strings (Portuguese).

Usage:
    from app.services.nlp_task import parse_task_text
    result = parse_task_text("Reunião com cliente p1 @marketing amanhã")

Returns a dict:
    {
        "title": str,
        "priority": int,          # 1-4, default 4
        "label_names": list[str], # e.g. ["marketing", "email"]
        "due_date": date | None,
        "deadline": date | None,
        "recurrence": str,        # e.g. "weekly:1" or ""
        "section": str | None,
        "start_time": str | None, # "HH:MM" e.g. "10:00"
        "duration_minutes": int | None,  # e.g. 60
    }
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Optional


# ---------------------------------------------------------------------------
# Weekday helpers
# ---------------------------------------------------------------------------

_WEEKDAY_PT = {
    "segunda": 0,
    "terça": 1,
    "terca": 1,
    "quarta": 2,
    "quinta": 3,
    "sexta": 4,
    "sábado": 5,
    "sabado": 5,
    "domingo": 6,
}

_MONTH_PT = {
    "janeiro": 1,
    "fevereiro": 2,
    "março": 3,
    "marco": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}


def _next_weekday(wd: int, from_date: Optional[date] = None) -> date:
    """Return the next occurrence of weekday wd (0=Mon..6=Sun) after from_date."""
    today = from_date or date.today()
    days_ahead = wd - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return today + timedelta(days=days_ahead)


def _next_business_day(from_date: Optional[date] = None) -> date:
    today = from_date or date.today()
    d = today
    if d.weekday() >= 5:  # today is weekend, find next weekday
        days = 7 - d.weekday()
        d = d + timedelta(days=days)
    return d


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------

def parse_task_text(text: str) -> dict:
    """Parse a task string and extract structured fields."""
    today = date.today()

    result: dict = {
        "title": "",
        "priority": 4,
        "label_names": [],
        "due_date": None,
        "deadline": None,
        "recurrence": "",
        "section": None,
        "start_time": None,
        "duration_minutes": None,
    }

    # Work on a mutable copy; we'll remove tokens as we identify them.
    remaining = text.strip()

    # ------------------------------------------------------------------
    # 1. Deadline: text inside curly braces {30 de março} / {30/03} / {30/03/2026}
    # ------------------------------------------------------------------
    deadline_pattern = re.compile(r'\{([^}]+)\}')
    deadline_match = deadline_pattern.search(remaining)
    if deadline_match:
        deadline_str = deadline_match.group(1).strip()
        result["deadline"] = _parse_date_str(deadline_str, today)
        remaining = deadline_pattern.sub("", remaining)

    # ------------------------------------------------------------------
    # 2. Section: /SectionName or /Multi Word Section
    #    Stops before: @label, p1/p2/p3, {deadline}, date keywords, end
    # ------------------------------------------------------------------
    # Section stops before: @label, p1/p2/p3, {deadline}, date/recurrence keywords, or EOL.
    # We match one or more words separated by single spaces, with a negative-lookahead
    # at each word boundary so we stop as soon as we hit a reserved word.
    _SECTION_STOP = (
        r'p[123]\b|@|\{|'
        r'hoje|amanh[aã]|depois|diariamente|mensalmente|'
        r'toda?\s|pr[oó]xim[ao]\s|'
        r'segunda|ter[cç]a|quarta|quinta|sexta|s[aá]bado|domingo|'
        r'\d{1,2}/\d{1,2}'
    )
    section_match = re.search(
        rf'/([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9]*'
        rf'(?:\s+(?!(?:{_SECTION_STOP}))[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9]*)*)'
        rf'(?=\s|$)',
        remaining, re.IGNORECASE
    )
    if section_match:
        result["section"] = section_match.group(1).strip()
        remaining = remaining[:section_match.start()] + remaining[section_match.end():]

    # ------------------------------------------------------------------
    # 3. Priority: p1, p2, p3 (standalone word, case-insensitive)
    # ------------------------------------------------------------------
    priority_pattern = re.compile(r'\bp([123])\b', re.IGNORECASE)
    prio_match = priority_pattern.search(remaining)
    if prio_match:
        result["priority"] = int(prio_match.group(1))
        remaining = priority_pattern.sub("", remaining, count=1)

    # ------------------------------------------------------------------
    # 4. Labels: @labelname
    # ------------------------------------------------------------------
    label_pattern = re.compile(r'@([A-Za-zÀ-ÿ0-9_\-]+)')
    labels = label_pattern.findall(remaining)
    result["label_names"] = [lbl.lower() for lbl in labels]
    remaining = label_pattern.sub("", remaining)

    # ------------------------------------------------------------------
    # 5. Date / recurrence tokens (Portuguese natural language)
    #    Process from most-specific to least-specific.
    # ------------------------------------------------------------------

    # 5a. "depois de amanhã" → today + 2
    if re.search(r'\bdepois\s+de\s+amanh[aã]\b', remaining, re.IGNORECASE):
        result["due_date"] = today + timedelta(days=2)
        remaining = re.sub(r'\bdepois\s+de\s+amanh[aã]\b', '', remaining, flags=re.IGNORECASE)

    # 5b. "amanhã" / "amanha"
    elif re.search(r'\bamanh[aã]\b', remaining, re.IGNORECASE):
        result["due_date"] = today + timedelta(days=1)
        remaining = re.sub(r'\bamanh[aã]\b', '', remaining, flags=re.IGNORECASE)

    # 5c. "hoje"
    elif re.search(r'\bhoje\b', remaining, re.IGNORECASE):
        result["due_date"] = today
        remaining = re.sub(r'\bhoje\b', '', remaining, flags=re.IGNORECASE)

    # 5d. "diariamente" / "todo dia"
    if re.search(r'\b(diariamente|todo\s+dia)\b', remaining, re.IGNORECASE):
        result["recurrence"] = "daily"
        if result["due_date"] is None:
            result["due_date"] = today
        remaining = re.sub(r'\b(diariamente|todo\s+dia)\b', '', remaining, flags=re.IGNORECASE)

    # 5e. "dias úteis" / "dias uteis"
    elif re.search(r'\bdias\s+[uú]teis\b', remaining, re.IGNORECASE):
        result["recurrence"] = "weekdays"
        if result["due_date"] is None:
            result["due_date"] = _next_business_day(today)
        remaining = re.sub(r'\bdias\s+[uú]teis\b', '', remaining, flags=re.IGNORECASE)

    # 5f. "mensalmente" / "todo mês" / "todo mes"
    elif re.search(r'\b(mensalmente|todo\s+m[eê]s)\b', remaining, re.IGNORECASE):
        result["recurrence"] = "monthly"
        if result["due_date"] is None:
            result["due_date"] = today
        remaining = re.sub(r'\b(mensalmente|todo\s+m[eê]s)\b', '', remaining, flags=re.IGNORECASE)

    # 5g. "toda segunda/terça/..." → weekly recurrence on that weekday
    toda_match = re.search(
        r'\btoda\s+(segunda|ter[cç]a|quarta|quinta|sexta|s[aá]bado|domingo)\b',
        remaining, re.IGNORECASE
    )
    if toda_match:
        wd_name = toda_match.group(1).lower()
        # normalise accents
        wd_name = wd_name.replace("ç", "c").replace("á", "a")
        wd_idx = _WEEKDAY_PT.get(wd_name, 0)
        result["recurrence"] = f"weekly:{wd_idx}"
        if result["due_date"] is None:
            result["due_date"] = _next_weekday(wd_idx, today)
        remaining = re.sub(
            r'\btoda\s+(segunda|ter[cç]a|quarta|quinta|sexta|s[aá]bado|domingo)\b',
            '', remaining, flags=re.IGNORECASE, count=1
        )

    # 5h. "próxima/próximo segunda/..." → next occurrence of weekday
    proxima_match = re.search(
        r'\br?pr[oó]xim[ao]\s+(segunda|ter[cç]a|quarta|quinta|sexta|s[aá]bado|domingo)\b',
        remaining, re.IGNORECASE
    )
    if proxima_match and result["due_date"] is None:
        wd_name = proxima_match.group(1).lower()
        wd_name_norm = wd_name.replace("ç", "c").replace("á", "a")
        wd_idx = _WEEKDAY_PT.get(wd_name_norm, _WEEKDAY_PT.get(wd_name, 0))
        result["due_date"] = _next_weekday(wd_idx, today)
        remaining = re.sub(
            r'\bpr[oó]xim[ao]\s+(segunda|ter[cç]a|quarta|quinta|sexta|s[aá]bado|domingo)\b',
            '', remaining, flags=re.IGNORECASE, count=1
        )

    # 5i. Bare weekday names (e.g. "segunda", "terça") → next occurrence
    weekday_bare_match = re.search(
        r'\b(segunda|ter[cç]a|quarta|quinta|sexta|s[aá]bado|domingo)\b',
        remaining, re.IGNORECASE
    )
    if weekday_bare_match and result["due_date"] is None:
        wd_name = weekday_bare_match.group(1).lower()
        wd_name_norm = wd_name.replace("ç", "c").replace("á", "a")
        wd_idx = _WEEKDAY_PT.get(wd_name_norm, _WEEKDAY_PT.get(wd_name, 0))
        result["due_date"] = _next_weekday(wd_idx, today)
        remaining = re.sub(
            r'\b(segunda|ter[cç]a|quarta|quinta|sexta|s[aá]bado|domingo)\b',
            '', remaining, flags=re.IGNORECASE, count=1
        )

    # 5j. "dia 15" → day 15 of current or next month
    dia_num_match = re.search(r'\bdia\s+(\d{1,2})\b', remaining, re.IGNORECASE)
    if dia_num_match and result["due_date"] is None:
        day_num = int(dia_num_match.group(1))
        result["due_date"] = _resolve_day_of_month(day_num, today)
        remaining = re.sub(r'\bdia\s+\d{1,2}\b', '', remaining, flags=re.IGNORECASE, count=1)

    # 5k. Full date formats: "15/03", "15/03/2026"
    date_slash_match = re.search(r'\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b', remaining)
    if date_slash_match and result["due_date"] is None:
        d, m = int(date_slash_match.group(1)), int(date_slash_match.group(2))
        y_raw = date_slash_match.group(3)
        y = _parse_year(y_raw, today.year, m, d, today)
        try:
            result["due_date"] = date(y, m, d)
        except ValueError:
            pass
        remaining = remaining[:date_slash_match.start()] + remaining[date_slash_match.end():]

    # 5l. "30 de março" style inline (not inside braces — those were handled above)
    month_text_match = re.search(
        r'\b(\d{1,2})\s+de\s+(' + '|'.join(_MONTH_PT.keys()) + r')\b',
        remaining, re.IGNORECASE
    )
    if month_text_match and result["due_date"] is None:
        d = int(month_text_match.group(1))
        m = _MONTH_PT[month_text_match.group(2).lower()]
        y = today.year if (m > today.month or (m == today.month and d >= today.day)) else today.year + 1
        try:
            result["due_date"] = date(y, m, d)
        except ValueError:
            pass
        remaining = remaining[:month_text_match.start()] + remaining[month_text_match.end():]

    # ------------------------------------------------------------------
    # 5m. Duration: "por 1h", "por 2h", "por 30min", "por 1h30", "por 1h30min", "por 90 min"
    # ------------------------------------------------------------------
    dur_match = re.search(
        r'\bpor\s+(?:(\d+)h\s*(?:(\d+)\s*min)?|(\d+)\s*min(?:utos?)?)\b',
        remaining, re.IGNORECASE
    )
    if dur_match:
        if dur_match.group(1) is not None:
            hours = int(dur_match.group(1))
            mins = int(dur_match.group(2)) if dur_match.group(2) else 0
            result["duration_minutes"] = hours * 60 + mins
        else:
            result["duration_minutes"] = int(dur_match.group(3))
        remaining = remaining[:dur_match.start()] + remaining[dur_match.end():]

    # ------------------------------------------------------------------
    # 5n. Start time: "10h", "10h30", "10:30", "14h", "às 10h", "as 10h"
    # ------------------------------------------------------------------
    time_match = re.search(
        r'\b(?:[aà]s?\s+)?(\d{1,2})(?:[h:](\d{2})?)\b',
        remaining, re.IGNORECASE
    )
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2)) if time_match.group(2) else 0
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            result["start_time"] = f"{hour:02d}:{minute:02d}"
        remaining = remaining[:time_match.start()] + remaining[time_match.end():]

    # ------------------------------------------------------------------
    # 6. Clean up and set title
    # ------------------------------------------------------------------
    # Remove extra whitespace
    title = re.sub(r'\s{2,}', ' ', remaining).strip()
    # Remove stray leading/trailing punctuation
    title = title.strip(".,;:!?-–—")
    result["title"] = title

    return result


# ---------------------------------------------------------------------------
# Date string helpers
# ---------------------------------------------------------------------------

def _parse_date_str(s: str, today: date) -> Optional[date]:
    """Parse a date string like '30 de março', '30/03', '30/03/2026'."""
    s = s.strip()

    # "30/03" or "30/03/2026"
    m = re.match(r'^(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?$', s)
    if m:
        d, mo = int(m.group(1)), int(m.group(2))
        y_raw = m.group(3)
        y = _parse_year(y_raw, today.year, mo, d, today)
        try:
            return date(y, mo, d)
        except ValueError:
            return None

    # "30 de março"
    mo_pattern = '|'.join(_MONTH_PT.keys())
    m2 = re.match(rf'^(\d{{1,2}})\s+de\s+({mo_pattern})$', s, re.IGNORECASE)
    if m2:
        d = int(m2.group(1))
        mo = _MONTH_PT[m2.group(2).lower()]
        y = today.year if (mo > today.month or (mo == today.month and d >= today.day)) else today.year + 1
        try:
            return date(y, mo, d)
        except ValueError:
            return None

    return None


def _parse_year(y_raw: Optional[str], default_year: int, month: int, day: int, today: date) -> int:
    if y_raw is None:
        # Pick current or next year so the date is not in the past
        if month > today.month or (month == today.month and day >= today.day):
            return today.year
        return today.year + 1
    y = int(y_raw)
    if y < 100:
        y += 2000
    return y


def _resolve_day_of_month(day: int, today: date) -> date:
    """Return the date for 'dia N' — current month if still in the future, else next month."""
    try:
        candidate = date(today.year, today.month, day)
    except ValueError:
        candidate = None

    if candidate and candidate >= today:
        return candidate

    # Move to next month
    if today.month == 12:
        y, m = today.year + 1, 1
    else:
        y, m = today.year, today.month + 1

    import calendar as _cal
    last = _cal.monthrange(y, m)[1]
    day = min(day, last)
    return date(y, m, day)
