#!/usr/bin/env python3
"""AS-IS / TO-BE 화면 확인 보고서 생성기.

사용법:
  python3 build_report.py <manifest.json> <출력.html>

manifest.json 형식 (경로는 manifest 파일 기준 상대경로 또는 절대경로):
{
  "title": "브라우저 탭 제목 (2~4단어)",
  "heading": "본문 H1 제목",
  "lang": "ko",                 # 생략 가능. "en"이면 화면 고정 문구(플랫폼, 정리, 목록)를 영어로 쓴다
  "labels": {"asis": "AS-IS", "tobe": "TO-BE"},   # 생략 가능 (칸 이름을 바꿀 때만)
  "notes": [                    # 생략 가능. 항목 뒤에 붙는 정리 상자 (task-plan의 태스크 목록, 자료끼리 다른 곳 등)
    {"id": "tasks", "title": "태스크 목록", "items": ["문장", "문장"]}
  ],
  "merge": true,                # 생략 가능. 플랫폼들의 항목 id 순서가 같으면 자동으로 true:
                                # 항목을 한 번만 두고 iOS/Android 전환 토글로 캡처와 설명을 바꿔 보여 준다.
                                # 플랫폼마다 항목이 다르면 false(플랫폼별로 나열).
  "platforms": [
    {
      "id": "ios",                # 앵커용 영문 id
      "name": "iOS",              # 화면에 보일 이름 (iOS, Android, 데스크톱, 모바일 웹 등)
      "wide": false,              # 데스크톱 웹처럼 가로가 긴 캡처면 true (이미지를 칸 너비까지 표시)
      "items": [
        {
          "id": "T1-1",           # 태스크 식별자 (목차와 제목 앞에 표시)
          "title": "로그인 정보 입력 단계",
          "lead": "무엇이 어떻게 바뀌었는지 설명하는 문장",
          "asis": [ {"img": "shots/ios/asis-01.png", "alt": "...", "caption": "...",
                     # 생략 가능. 화면에 보이는 변경점에 번호를 단다 (화면 기획서 방식)
                     # x, y, w, h는 이미지 크기 대비 퍼센트. 같은 번호의 AS-IS 문제와 TO-BE 개선이 짝이다.
                     "marks": [ {"n": 1, "x": 8, "y": 17, "w": 84, "h": 6, "text": "번호 설명"} ]
                     # 또는 web_capture.mjs가 저장한 좌표 파일 경로: "marks": "shots/desktop/asis-01.marks.json"
                   } ],
          "tobe": [ {"text": "해당 화면 없음."} ]
        }
      ]
    }
  ]
}

이미지는 JPEG로 줄여 HTML 안에 넣는다 (단일 파일로 전달하기 위함).
macOS에서는 sips, 그 밖에서는 Pillow가 있으면 사용하고, 둘 다 없으면 원본을 그대로 넣는다.
"""
import base64
import html
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, '..', 'assets', 'report-template.html')
MAX_EDGE = 900

# 보고서 틀의 고정 문구 (manifest의 lang으로 고른다)
UI_TEXT = {
    'ko': {'platform': '플랫폼', 'platform_switch': '플랫폼 전환', 'notes': '정리', 'nav': '항목 목록'},
    'en': {'platform': 'Platform', 'platform_switch': 'Switch platform', 'notes': 'Notes', 'nav': 'Items'},
}


def to_jpeg_bytes(path):
    ext = os.path.splitext(path)[1].lower()
    if shutil.which('sips'):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, 'img.jpg')
            subprocess.run(
                ['sips', '-s', 'format', 'jpeg', '-s', 'formatOptions', '72',
                 '-Z', str(MAX_EDGE), path, '--out', out],
                check=True, capture_output=True)
            return open(out, 'rb').read(), 'image/jpeg'
    try:
        from PIL import Image  # type: ignore
        import io
        im = Image.open(path).convert('RGB')
        im.thumbnail((MAX_EDGE, MAX_EDGE))
        buf = io.BytesIO()
        im.save(buf, 'JPEG', quality=72)
        return buf.getvalue(), 'image/jpeg'
    except ImportError:
        mime = 'image/png' if ext == '.png' else 'image/jpeg'
        return open(path, 'rb').read(), mime


def figure(entry, base):
    if 'text' in entry:
        return f'<ul><li>{html.escape(entry["text"])}</li></ul>'
    path = entry['img']
    if not os.path.isabs(path):
        path = os.path.join(base, path)
    data, mime = to_jpeg_bytes(path)
    b64 = base64.b64encode(data).decode()
    alt = html.escape(entry.get('alt', ''))
    cap = html.escape(entry.get('caption', ''))
    marks = entry.get('marks', [])
    if isinstance(marks, str):
        # web_capture.mjs가 저장한 좌표 파일
        mp = marks if os.path.isabs(marks) else os.path.join(base, marks)
        marks = json.load(open(mp, encoding='utf-8'))
    if not marks:
        return (f'<figure><img src="data:{mime};base64,{b64}" alt="{alt}">'
                f'<figcaption>{cap}</figcaption></figure>')
    # 화면 기획서처럼 바뀌는 부분에 번호 박스를 겹치고, 캡처 아래 같은 번호로 설명한다
    boxes = ''.join(
        f'<span class="mark" style="left:{mk["x"]}%;top:{mk["y"]}%;width:{mk["w"]}%;height:{mk["h"]}%">'
        f'<span class="badge">{mk["n"]}</span></span>' for mk in marks)
    notes = ''.join(
        f'<li><span class="badge">{mk["n"]}</span><span>{html.escape(mk["text"])}</span></li>'
        for mk in marks if mk.get('text'))
    notes_html = f'<ol class="mark-notes">{notes}</ol>' if notes else ''
    return (f'<figure><div class="shot"><img src="data:{mime};base64,{b64}" alt="{alt}">{boxes}</div>'
            f'<figcaption>{cap}</figcaption>{notes_html}</figure>')


def column(tag, entries, base, labels):
    label = html.escape(labels.get(tag, 'AS-IS' if tag == 'asis' else 'TO-BE'))
    body = ''.join(figure(e, base) for e in entries)
    return f'<div class="col"><span class="tag {tag}">{label}</span>{body}</div>'


TOGGLE_CSS = """
<style>
  .pf-bar { position: sticky; top: 0; z-index: 5; background: var(--bg); padding: 10px 0; margin-bottom: -16px;
    display: flex; align-items: center; gap: 12px; border-bottom: 2px solid var(--fg); }
  .pf-bar .pf-label { font-size: 13px; color: var(--muted); }
  .pf-toggle { display: inline-flex; border: 1px solid var(--line); border-radius: 999px; padding: 3px; background: var(--surface); }
  .pf-toggle button { font: inherit; font-size: 14px; font-weight: 500; border: 0; background: transparent; color: var(--muted);
    padding: 6px 16px; border-radius: 999px; cursor: pointer; min-height: 36px; }
  .pf-toggle button[aria-pressed="true"] { background: var(--accent); color: #fff; }
%RULES%
</style>
"""

TOGGLE_JS = """
<script>
(function(){
  var ids = %IDS%, key = 'asis-tobe-platform', cur = ids[0];
  try { var saved = localStorage.getItem(key); if (ids.indexOf(saved) >= 0) cur = saved; } catch (e) {}
  var btns = [].slice.call(document.querySelectorAll('.pf-toggle button'));
  function set(id){
    document.documentElement.setAttribute('data-pf', id);
    btns.forEach(function(b){ b.setAttribute('aria-pressed', b.dataset.pf === id ? 'true' : 'false'); });
    try { localStorage.setItem(key, id); } catch (e) {}
  }
  btns.forEach(function(b){ b.addEventListener('click', function(){ set(b.dataset.pf); }); });
  set(cur);
})();
</script>
"""


def can_merge(platforms):
    """플랫폼이 둘 이상이고 항목 id 순서가 모두 같으면 토글로 합친다."""
    if len(platforms) < 2:
        return False
    first = [it['id'] for it in platforms[0]['items']]
    return all([it['id'] for it in p['items']] == first for p in platforms[1:])


def per_platform(values, render):
    """플랫폼별 값이 모두 같으면 한 번만, 다르면 플랫폼별로 감싸서 낸다."""
    rendered = [(pid, render(v)) for pid, v in values]
    if len({r for _, r in rendered}) == 1:
        return rendered[0][1]
    return ''.join(f'<div class="pf" data-platform="{pid}">{r}</div>' for pid, r in rendered)


def main():
    manifest_path, out_path = sys.argv[1], sys.argv[2]
    base = os.path.dirname(os.path.abspath(manifest_path))
    m = json.load(open(manifest_path, encoding='utf-8'))
    tpl = open(TEMPLATE, encoding='utf-8').read()
    labels = m.get('labels', {})
    lang = m.get('lang', 'ko')
    ui = UI_TEXT.get(lang, UI_TEXT['ko'])
    platforms = m['platforms']
    merge = m.get('merge', can_merge(platforms))

    nav, body, extra = [], [], ''
    if merge:
        # 같은 항목은 한 번만 두고, 플랫폼 전환 토글로 캡처와 설명을 바꿔 보여 준다
        ids = [p['id'] for p in platforms]
        buttons = ''.join(f'<button type="button" data-pf="{p["id"]}" aria-pressed="false">'
                          f'{html.escape(p["name"])}</button>' for p in platforms)
        body.append(f'<div class="pf-bar"><span class="pf-label">{ui["platform"]}</span>'
                    f'<div class="pf-toggle" role="group" aria-label="{ui["platform_switch"]}">{buttons}</div></div>')
        cache = {}

        def fig(e):
            k = json.dumps(e, sort_keys=True, ensure_ascii=False)
            if k not in cache:
                cache[k] = figure(e, base)
            return cache[k]

        for idx, it0 in enumerate(platforms[0]['items']):
            items = [(p['id'], p['items'][idx]) for p in platforms]
            wide = any(p.get('wide') for p in platforms)
            anchor = it0['id']
            nav.append(f'    <a href="#{anchor}"><span class="id">{html.escape(it0["id"])}</span>'
                       f'<span>{html.escape(it0["title"])}</span></a>')
            lead = per_platform([(pid, it['lead']) for pid, it in items],
                                lambda v: f'<p class="lead">{html.escape(v)}</p>')
            cols = ''
            for tag in ('asis', 'tobe'):
                label = html.escape(labels.get(tag, 'AS-IS' if tag == 'asis' else 'TO-BE'))
                inner = per_platform([(pid, it[tag]) for pid, it in items],
                                     lambda entries: ''.join(fig(e) for e in entries))
                cols += f'<div class="col"><span class="tag {tag}">{label}</span>{inner}</div>'
            body.append(
                f'<section class="item{" wide" if wide else ""}" id="{anchor}">'
                f'<h2><span class="id">{html.escape(it0["id"])}</span>{html.escape(it0["title"])}</h2>'
                f'{lead}<div class="compare">{cols}</div></section>')
        rules = '\n'.join(f'  :root[data-pf="{pid}"] .pf:not([data-platform="{pid}"]) {{ display: none; }}'
                          for pid in ids)
        rules += f'\n  :root:not([data-pf]) .pf:not([data-platform="{ids[0]}"]) {{ display: none; }}'
        extra = TOGGLE_CSS.replace('%RULES%', rules) + TOGGLE_JS.replace('%IDS%', json.dumps(ids))
    else:
        multi = len(platforms) > 1
        for p in platforms:
            if multi:
                nav.append(f'    <div class="nav-group">{html.escape(p["name"])}</div>')
                body.append(f'<h2 class="platform" id="{p["id"]}">{html.escape(p["name"])}</h2>')
            for it in p['items']:
                anchor = f'{p["id"]}-{it["id"]}'
                nav.append(f'    <a href="#{anchor}"><span class="id">{html.escape(it["id"])}</span>'
                           f'<span>{html.escape(it["title"])}</span></a>')
                body.append(
                    f'<section class="item{" wide" if p.get("wide") else ""}" id="{anchor}">'
                    f'<h2><span class="id">{html.escape(it["id"])}</span>{html.escape(it["title"])}</h2>'
                    f'<p class="lead">{html.escape(it["lead"])}</p>'
                    f'<div class="compare">{column("asis", it["asis"], base, labels)}'
                    f'{column("tobe", it["tobe"], base, labels)}</div></section>')

    for n in m.get('notes', []):
        nid = n.get('id', 'note')
        nav.append(f'    <a href="#{nid}"><span class="id">{ui["notes"]}</span><span>{html.escape(n["title"])}</span></a>')
        lis = ''.join(f'<li>{html.escape(x)}</li>' for x in n['items'])
        body.append(f'<section class="item" id="{nid}"><h2>{html.escape(n["title"])}</h2>'
                    f'<div class="col"><ul>{lis}</ul></div></section>')

    doc = (tpl.replace('{{TITLE}}', html.escape(m['title']))
              .replace('{{LANG}}', html.escape(lang))
              .replace('{{NAV_LABEL}}', ui['nav'])
              .replace('{{HEADING}}', html.escape(m['heading']))
              .replace('{{NAV}}', '\n'.join(nav))
              .replace('{{BODY}}', '\n'.join(body)))
    doc += extra
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(doc)
    print(f'{out_path} ({len(doc) // 1024} KB, {"플랫폼 토글" if merge else "플랫폼별 나열"})')


if __name__ == '__main__':
    main()
