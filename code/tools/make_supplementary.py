# -*- coding: utf-8 -*-
"""Tek dosyalik LaTeX ek materyali uretir: manuscript/supplementary.tex

CSV'ler longtable'a, markdown notlar LaTeX bolumlerine cevrilir.
Kullanim: python code/tools/make_supplementary.py
"""
import csv
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parents[2]
SUP = ROOT / 'submission_assets' / 'supplementary'
OUT = ROOT / 'manuscript' / 'supplementary.tex'

# --------------------------------------------------------------- kacis -----
ESC = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$',
       '#': r'\#', '_': r'\_', '{': r'\{', '}': r'\}',
       '~': r'\textasciitilde{}', '^': r'\textasciicircum{}'}

UNI = {'₁': r'\textsubscript{1}', '₂': r'\textsubscript{2}', '₃': r'\textsubscript{3}',
       '²': r'\textsuperscript{2}', '³': r'\textsuperscript{3}',
       '⁶': r'\textsuperscript{6}', '⁹': r'\textsuperscript{9}',
       '→': r'$\rightarrow$', '–': '--', '—': '---', '−': '$-$',
       '≥': r'$\ge$', '≤': r'$\le$', '×': r'$\times$', '±': r'$\pm$',
       '÷': r'$\div$', '≈': r'$\approx$', '·': r'$\cdot$', '°': r'\textdegree{}',
       'Σ': r'$\Sigma$', 'η': r'$\eta$', 'γ': r'$\gamma$', 'δ': r'$\delta$',
       'λ': r'$\lambda$', 'α': r'$\alpha$', 'β': r'$\beta$', 'φ': r'$\phi$',
       'ε': r'$\varepsilon$', 'μ': r'$\mu$', 'ν': r'$\nu$', 'π': r'$\pi$',
       '✓': r'$\checkmark$', '✗': r'$\times$', '″': r'\textquotedbl{}',
       '£': r'\pounds{}', '€': r'\euro{}',
       ' ': '~', ' ': r'\,', ' ': r'\,',
       '“': "``", '”': "''", '‘': '`', '’': "'"}

# inputenc + T1 ile sorunsuz basilan harfler; denetimde uyari verilmez
GUVENLI = set('ğüşıöçĞÜŞİÖÇâîûÂÎÛéèáàóòãñåæøÅÆØßÿœŒ')


def esc(s):
    """Duz metni LaTeX icin guvenli hale getirir."""
    s = str(s)
    s = ''.join(ESC.get(c, c) for c in s)
    for k, v in UNI.items():
        s = s.replace(k, v)
    # uzun URL'ler satir sonunda kirilabilsin
    s = re.sub(r'(https?://\S+)', lambda m: r'\url{' + m.group(1)
               .replace(r'\%', '%').replace(r'\_', '_').replace(r'\&', '&')
               .replace(r'\#', '#').replace(r'\textasciitilde{}', '~') + '}', s)
    return s


def inline_md(s):
    """**kalin**, *egik*, `kod` ve markdown kacislarini isler; sonra esc()."""
    parts, out = re.split(r'(\*\*[^*]+\*\*|`[^`]+`|\*[^*\n]+\*)', s), []
    for p in parts:
        if p.startswith('**') and p.endswith('**'):
            out.append(r'\textbf{' + esc(p[2:-2]) + '}')
        elif p.startswith('*') and p.endswith('*') and len(p) > 2:
            out.append(r'\textit{' + esc(p[1:-1]) + '}')
        elif p.startswith('`') and p.endswith('`'):
            out.append(r'\texttt{' + esc(p[1:-1]) + '}')
        else:
            out.append(esc(p.replace(r'\*', '*')))
    return ''.join(out)


URL_RE = re.compile(r'(\\url\{[^}]*\})')


def kir(s):
    """Tablo hucrelerinde URL disindaki '/' sonrasina satir sonu izni koyar.

    'Technical/environmental' gibi bolunemez diziler aksi halde komsu
    sutunun uzerine tasiyor.
    """
    parts = URL_RE.split(s)
    for i in range(0, len(parts), 2):
        parts[i] = (parts[i].replace('/', r'/\allowbreak{}')
                            .replace(r'\_', r'\_\allowbreak{}'))
        # Uzun, bolunemez buyuk harf dizileri (TR_HUB_HYSOUTHMARMARA'nin son
        # parcasi gibi) sutun disina tasiyor; her 8 harfte kirilma izni ver.
        parts[i] = re.sub(r'[A-Z]{10,}',
                          lambda m: r'\allowbreak{}'.join(
                              m.group(0)[j:j + 8] for j in range(0, len(m.group(0)), 8)),
                          parts[i])
    return ''.join(parts)


# ------------------------------------------------------------ tablolar -----
def read_csv(name):
    rows = list(csv.reader((SUP / name).read_text(encoding='utf-8-sig').splitlines()))
    return [r for r in rows if any(c.strip() for c in r)]


# Yazi tipi -> yaklasik punto; sutun genisligi bundan hesaplanir.
PUNTO = {r'\tiny': 6, r'\scriptsize': 8, r'\footnotesize': 9,
         r'\small': 10, '': 11}


def sutun_spec(rows, n, fontsize, width):
    """Sutun genisliklerini icerige gore hesaplar (cm cinsinden metin alani).

    Elle verilen p{..} degerleri tasmaya yol aciyordu; burada her sutunun
    en uzun hucresi ve en uzun bolunemez kelimesi olculup kalan genislik
    orantili dagitilir.
    """
    pt = PUNTO.get(fontsize, 9)
    em = pt * 0.03515                              # 1 em -> cm
    pad = 0.43                                     # 2 x tabcolsep

    def gen(s):
        """Metnin yaklasik genisligi (cm). Buyuk harf ve rakam genistir."""
        t = 0.0
        for c in str(s):
            if c.isupper() or c.isdigit():
                t += 0.72
            elif c == ' ':
                t += 0.33
            elif c.isalpha():
                t += 0.50
            else:
                t += 0.44
        return t * em

    def hucre(i, r):
        return str(r[i]) if i < len(r) else ''

    nat = [max(gen(hucre(i, r)) for r in rows) for i in range(n)]
    # Bolunemez en uzun kelime; URL'ler \url{} icinde her yerden kirilabildigi
    # icin tabana dahil edilmez, yoksa tek sutun butun genisligi yutuyor.
    # Hucrelerde '_' ve '/' sonrasina satir sonu izni verildigi icin taban
    # bu parcalar uzerinden olculur, yoksa sutun gereksiz genis kaliyor.
    def parcala(s):
        return [p for p in re.split(r'[\s_/]+', s) if p]

    mn = [max(max((gen(w) for w in parcala(hucre(i, r))
                   if not w.lower().startswith(('http', 'www'))), default=0.0)
              for r in rows) + 0.12 for i in range(n)]
    avail = width - n * pad
    mn = [min(m, 0.28 * avail) for m in mn]

    # Pay birakmadan 'l' secilirse tahmin hatasi dogrudan tasmaya donuyor.
    if sum(nat) <= 0.70 * avail:
        return ''.join('c' if i and nat[i] <= 1.6 * em + 0.05 else 'l'
                       for i in range(n))

    sabit = [i for i in range(n) if nat[i] <= 1.0]
    esnek = [i for i in range(n) if i not in sabit]
    # 'l' sutunlari dogal genisliginde basilir; tahmin hatasina pay birak.
    kalan = avail - 1.3 * sum(nat[i] for i in sabit)
    tot = sum(nat[i] for i in esnek) or 1.0
    w = {i: max(kalan * nat[i] / tot, mn[i], 0.9) for i in esnek}

    for _ in range(12):                            # mn tabani asarsa yeniden dagit
        fazla = sum(w.values()) - kalan
        if fazla <= 0.01:
            break
        kisilabilir = [i for i in esnek if w[i] > mn[i] + 0.05]
        if not kisilabilir:
            break
        pay = sum(w[i] for i in kisilabilir)
        for i in kisilabilir:
            w[i] = max(mn[i], w[i] - fazla * w[i] / pay)

    spec = ''.join('l' if i in sabit else
                   r'>{\raggedright\arraybackslash}p{' + f'{w[i]:.2f}' + 'cm}'
                   for i in range(n))
    return spec, sum(w.values()) - kalan          # artan genislik (cm)


# Kucukten buyuge yazi tipi merdiveni
MERDIVEN = [r'\footnotesize', r'\scriptsize', r'\tiny']


def spec_ve_punto(rows, n, fontsize, width):
    """Tabloyu sigdiran ilk yazi tipini ve sutun spec'ini dondurur.

    Bolunemez kelimelerin toplam tabani butceyi asiyorsa tek care yaziyi
    kucultmek; aksi halde longtable sayfadan tasiyor.
    """
    try:
        bas = MERDIVEN.index(fontsize)
    except ValueError:
        bas = 0
        fontsize = MERDIVEN[0]
    for fs in MERDIVEN[bas:]:
        r = sutun_spec(rows, n, fs, width)
        if isinstance(r, str):                     # dogal genislige sigdi
            return r, fs
        spec, artan = r
        if artan <= 0.05:
            return spec, fs
    return spec, MERDIVEN[-1]


def longtable(rows, caption, label, fontsize=r'\scriptsize',
              head_bold=True, cols=None, width=16.6):
    """CSV satirlarindan longtable uretir. cols: tutulacak sutun indeksleri.

    width: kullanilabilir metin genisligi (cm). Dikey sayfa 16.6,
    landscape 25.3.
    """
    if cols is not None:
        rows = [[r[i] if i < len(r) else '' for i in cols] for r in rows]
    head, body = rows[0], rows[1:]
    n = len(head)
    spec, fontsize = spec_ve_punto(rows, n, fontsize, width)
    h = ' & '.join(kir((r'\textbf{' + inline_md(c) + '}') if head_bold
                       else inline_md(c)) for c in head)
    # Yazi tipi komutu longtable'in DISINDA olmali; caption ile toprule
    # arasina konursa LaTeX "Misplaced \noalign" verir.
    L = ['{' + fontsize,
         r'\begin{longtable}{' + spec + '}',
         r'\caption{' + caption + r'}\label{' + label + r'}\\',
         r'\toprule', h + r' \\', r'\midrule', r'\endfirsthead',
         r'\multicolumn{' + str(n) + r'}{l}{\footnotesize\itshape '
         + caption.split('.')[0] + r' (continued)}\\',
         r'\toprule', h + r' \\', r'\midrule', r'\endhead',
         r'\midrule\multicolumn{' + str(n)
         + r'}{r}{\footnotesize\itshape continued on next page}\\', r'\endfoot',
         r'\bottomrule', r'\endlastfoot']
    for r in body:
        cells = [kir(inline_md(c)) for c in (r + [''] * (n - len(r)))[:n]]
        if all(not c.strip() for c in cells[1:]):          # grup basligi satiri
            L.append(r'\multicolumn{' + str(n) + r'}{l}{\textbf{'
                     + cells[0] + r'}} \\')
        else:
            L.append(' & '.join(cells) + r' \\')
    L += [r'\end{longtable}', '}']
    return '\n'.join(L)


# --------------------------------------------------- markdown -> LaTeX -----
def md_block(text, base=r'\subsection'):
    """Notlari LaTeX'e cevirir: basliklar, tablolar, listeler, paragraflar."""
    out, lines, i = [], text.splitlines(), 0
    lv = {2: base, 3: base + 'section'} if base == r'\subsection' else \
         {2: r'\subsubsection', 3: r'\paragraph'}
    while i < len(lines):
        s = lines[i].rstrip()
        if not s.strip():
            i += 1
            continue
        m = re.match(r'^(#{1,4})\s+(.*)$', s)
        if m:
            d = len(m.group(1))
            cmd = lv.get(max(2, min(3, d)), base)
            out.append(cmd + '{' + inline_md(m.group(2)) + '}')
            i += 1
            continue
        if s.lstrip().startswith('|'):                      # markdown tablo
            blk = []
            while i < len(lines) and lines[i].lstrip().startswith('|'):
                blk.append(lines[i])
                i += 1
            out.append(md_table(blk))
            continue
        if re.match(r'^\s*[-*]\s+', s):                     # madde listesi
            items = []
            while i < len(lines) and re.match(r'^\s*[-*]\s+', lines[i] or ' '):
                items.append(re.sub(r'^\s*[-*]\s+', '', lines[i]).rstrip())
                i += 1
            out.append(r'\begin{itemize}\setlength\itemsep{1pt}')
            out += [r'  \item ' + inline_md(x) for x in items]
            out.append(r'\end{itemize}')
            continue
        if re.match(r'^\s*\d+\.\s+', s):                    # numarali liste
            items = []
            while i < len(lines) and re.match(r'^\s*\d+\.\s+', lines[i] or ' '):
                items.append(re.sub(r'^\s*\d+\.\s+', '', lines[i]).rstrip())
                i += 1
            out.append(r'\begin{enumerate}\setlength\itemsep{1pt}')
            out += [r'  \item ' + inline_md(x) for x in items]
            out.append(r'\end{enumerate}')
            continue
        par = []
        while i < len(lines) and lines[i].strip() and \
                not lines[i].lstrip().startswith(('|', '#')) and \
                not re.match(r'^\s*([-*]|\d+\.)\s+', lines[i]):
            par.append(lines[i].strip())
            i += 1
        out.append(inline_md(' '.join(par)))
    return '\n\n'.join(out)


def md_table(block):
    """Markdown tablosunu tabularx'e cevirir; sutun genisligi icerige gore."""
    rows = [[c.strip() for c in l.strip().strip('|').split('|')] for l in block]
    rows = [r for r in rows if not all(set(c) <= set('-: ') for c in r)]
    n = max(len(r) for r in rows)
    rows = [(r + [''] * (n - len(r)))[:n] for r in rows]

    # Sutun basina en uzun hucre: kisa olanlar sabit (l), uzunlar esnek (X).
    w = [max(len(r[i]) for r in rows) for i in range(n)]
    esnek = [i for i in range(n) if w[i] > 14]
    if not esnek:                                   # hepsi kisa -> duz tabular
        spec = 'l' * n
        env, arg = 'tabular', ''
    else:
        tot = sum(w[i] for i in esnek)
        k = len(esnek)
        f = {i: k * w[i] / tot for i in esnek}      # ortalamasi 1 olacak agirlik
        # Kirpma toplami bozar; tabularx'in toplam = sutun sayisi kurali
        # bozulursa tablo \textwidth'i asar. Kirptiktan sonra yeniden olcekle.
        for _ in range(8):
            f = {i: min(max(v, 0.45), 2.6) for i, v in f.items()}
            s = sum(f.values())
            if abs(s - k) < 1e-6:
                break
            f = {i: v * k / s for i, v in f.items()}
        spec = ''.join(
            (r'>{\hsize=' + f'{f[i]:.3f}' + r'\hsize\raggedright\arraybackslash}X')
            if i in esnek else 'l' for i in range(n))
        env, arg = 'tabularx', r'{\textwidth}'

    # Toplam metin yogunlugu yuksekse yazi tipini kucult.
    yogun = sum(sum(len(c) for c in r) for r in rows)
    fs = r'\scriptsize' if yogun > 1800 else r'\footnotesize'

    L = [r'\begin{center}' + fs,
         r'\begin{' + env + '}' + arg + '{' + spec + '}', r'\toprule']
    for k, r in enumerate(rows):
        cells = [kir(inline_md(c)) for c in r]
        if k == 0:
            cells = [r'\textbf{' + c + '}' for c in cells]
        L.append(' & '.join(cells) + r' \\')
        if k == 0:
            L.append(r'\midrule')
    L += [r'\bottomrule', r'\end{' + env + '}', r'\end{center}']
    return '\n'.join(L)


def notes(name, base=r'\subsection'):
    t = (SUP / name).read_text(encoding='utf-8-sig')
    t = re.sub(r'^#\s+.*$', '', t, count=1, flags=re.M)     # ust basligi at
    # "--- Baslik ---" satirlari ayri bir kalin paragraf olsun; duz metin olarak
    # birakilirsa izleyen metne yapisip sag marja tasiyor.
    t = re.sub(r'^---\s*(\S.*?\S)\s*---\s*$', r'\n**\1**\n', t, flags=re.M)
    t = re.sub(r'^---\s*$', '', t, flags=re.M)
    return md_block(t.strip(), base)


PRE = r"""\documentclass[11pt,a4paper]{article}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage[margin=2.2cm]{geometry}
\usepackage{amsmath,booktabs,longtable,array,tabularx,pdflscape,url,eurosym,amssymb}
\usepackage{ragged2e}
\usepackage[hidelinks]{hyperref}
\usepackage{textcomp}
% Uzun kaynak adresleri satir sonunda her karakterden bolunebilsin.
\Urlmuskip=0mu plus 1mu\relax
\def\UrlBreaks{\do\/\do\-\do\_\do\.\do\:\do\?\do\=\do\&\do\%\do\~\do\+\do\,%
\do\;\do\#\do\a\do\b\do\c\do\d\do\e\do\f\do\g\do\h\do\i\do\j\do\k\do\l\do\m%
\do\n\do\o\do\p\do\q\do\r\do\s\do\t\do\u\do\v\do\w\do\x\do\y\do\z\do\A\do\B%
\do\C\do\D\do\E\do\F\do\G\do\H\do\I\do\J\do\K\do\L\do\M\do\N\do\O\do\P\do\Q%
\do\R\do\S\do\T\do\U\do\V\do\W\do\X\do\Y\do\Z\do\0\do\1\do\2\do\3\do\4\do\5%
\do\6\do\7\do\8\do\9}
\urlstyle{same}
% pdflscape sayfayi dondurur ama \textwidth'i degistirmez; genis tablolarin
% dogru olculmesi icin landscape icinde metin alanini elle genisletiyoruz.
\newcommand{\genisle}{%
  \setlength{\textwidth}{25.3cm}\hsize=\textwidth
  \linewidth=\textwidth \columnwidth=\textwidth
  \setlength{\LTcapwidth}{\textwidth}}
\setlength{\LTcapwidth}{\textwidth}
\renewcommand{\arraystretch}{1.12}
\setcounter{secnumdepth}{0}
\title{Supplementary material\\[2mm]
\large From Land Eligibility to Pipeline Corridors: An Integrated
GIS--Spherical-Fuzzy--Robust-Possibilistic Design of T\"urkiye's Green
Hydrogen Supply Chain}
\author{Kadir Sarıkaya}
\date{}
\begin{document}
\maketitle
\noindent This document provides supporting material for the main-text model:
the industrial hydrogen demand inventory (Table~S1), the techno-economic
parameter set and derivations (Table~S2), the siting studies coded for Stage~II
criterion selection (Table~S3), Stage~I screening detail (Table~S4), the Stage~II method comparison (Table~S5),
the register of Stage~III runs (Table~S6) and the Stage~II weight-blend sensitivity (Table~S13).
\tableofcontents
\newpage
"""


def main():
    P = [PRE]

    # ---------------------------------------------------------- S1 --------
    P.append(r'\section{Supplementary Table S1. Demand node inventory}')
    P.append(esc((SUP / 'Supplementary_Table_S1_Caption.txt')
                 .read_text(encoding='utf-8-sig').strip()
                 .replace('Supplementary Table S1. ', '')))
    s1 = read_csv('Supplementary_Table_S1_Demand_Inventory.csv')
    P.append(r'\begin{landscape}\genisle')
    P.append(longtable(
        s1,
        'Supplementary Table S1a. Demand nodes: identity, location and capacity.',
        'tab:s1a', cols=[0, 1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 13][:9], width=25.3))
    P.append(longtable(
        s1,
        'Supplementary Table S1b. Demand nodes: estimated hydrogen demand, '
        'status and selection flags.',
        'tab:s1b', cols=[0, 14, 15, 16, 17, 19, 20, 22, 23, 24], width=25.3))
    P.append(longtable(
        s1,
        'Supplementary Table S1c. Demand nodes: estimation basis and coordinate '
        'provenance.',
        'tab:s1c', cols=[0, 18, 21, 8], fontsize=r'\tiny', width=25.3))
    P.append(r'\end{landscape}')
    P.append(r'\subsection{Notes to Table S1}')
    P.append(notes('Supplementary_Table_S1_Source_Notes.txt', r'\subsubsection'))

    # ---------------------------------------------------------- S2 --------
    P.append(r'\newpage\section{Supplementary Table S2. Techno-economic parameter set}')
    P.append(esc((SUP / 'Supplementary_Table_S2_Caption.txt')
                 .read_text(encoding='utf-8-sig').strip()
                 .replace('Supplementary Table S2. ', '')))
    P.append(r'\begin{landscape}\genisle')
    P.append(longtable(
        read_csv('Supplementary_Table_S2_Parameter_Sources.csv'),
        'Supplementary Table S2. Stage~III techno-economic parameters, with '
        'sources and evidence levels.',
        'tab:s2', fontsize=r'\tiny', width=25.3))
    P.append(r'\end{landscape}')
    P.append(r'\subsection{Notes to Table S2}')
    P.append(notes('Supplementary_Table_S2_Source_Notes.txt', r'\subsubsection'))

    # ---------------------------------------------------------- S3 --------
    P.append(r'\newpage\section{Supplementary Table S3. Coded siting studies}')
    P.append(esc((SUP / 'Supplementary_Table_S3_Caption.txt')
                 .read_text(encoding='utf-8-sig').strip()
                 .replace('Supplementary Table S3. ', '')))
    P.append(longtable(
        read_csv('Supplementary_Table_S3_Coded_Studies.csv'),
        'Supplementary Table S3a. The 22 siting studies coded for Stage~II '
        'criterion selection.', 'tab:s3a', fontsize=r'\footnotesize'))
    P.append(r'\begin{landscape}\genisle')
    P.append(longtable(
        read_csv('Supplementary_Table_S3_Criterion_Frequency.csv'),
        'Supplementary Table S3b. Criterion-by-study matrix. Mode codes are '
        'given in the notes below.', 'tab:s3b', fontsize=r'\footnotesize',
        width=25.3))
    P.append(r'\end{landscape}')
    P.append(r'\subsection{Notes to Table S3}')
    P.append(notes('Supplementary_Table_S3_Notes.txt', r'\subsubsection'))

    TASINAN = [('Note', 'S7', 'Stage~III mathematical model',
                ['Moved_S7_Stage_III_Notation.tex', 'Stage_III_Mathematical_Model.tex']),
               ('Table', 'S8', 'Stage~I exclusion and suitability criteria',
                ['Moved_S8_Stage_I_Criteria.tex']),
               ('Table', 'S9', 'Stage~II preference criteria',
                ['Moved_S9_Stage_II_Criteria.tex']),
               ('Note', 'S10', 'Comparison with published cost estimates',
                ['Moved_S10_Cost_Benchmark.tex']),
               ('Note', 'S11', 'Reconciling the Monte Carlo and Me valuations',
                ['Moved_S11_MC_Reading.tex']),
               ('Note', 'S12', 'Stage~II standard formulations',
                ['Moved_S12_Stage_II_Formulations.tex'])]

# ---------------------------------------------------------- S4 --------
    P.append(r'\newpage\section{Supplementary Table S4. Stage~I screening detail}')
    P.append(esc((SUP / 'Supplementary_Table_S4_Caption.txt')
                 .read_text(encoding='utf-8-sig').strip()
                 .replace('Supplementary Table S4. ', '')))
    P.append(notes('Supplementary_Table_S4_Notes.txt', r'\subsection'))

    # ---------------------------------------------------------- S5, S6 (V4) --------
    for code, title, csvname in [('S5', 'Stage~II method comparison', 'Supplementary_Table_S5_Method_Comparison.csv'),
                                 ('S6', 'Stage~III run register', 'Supplementary_Table_S6_Run_Register.csv')]:
        cap = SUP / f'Supplementary_Table_{code}_Caption.txt'
        if not (SUP / csvname).exists():
            continue
        P.append(r'\newpage\section{Supplementary Table ' + code + '. ' + title + '}')
        ctext = esc(cap.read_text(encoding='utf-8-sig').strip().replace(f'Supplementary Table {code}. ', ''))
        P.append(longtable(read_csv(csvname), 'Supplementary Table ' + code + '. ' + title + '.', 'tab:' + code.lower()))
        P.append(ctext)

    # ---------------------------------------------------------- tasinan notlar (V5) --------
    for kind, code, title, fnames in TASINAN:
        parts = [(SUP / f).read_text(encoding='utf-8') for f in fnames if (SUP / f).exists()]
        if not parts:
            continue
        P.append(r'\newpage\section{Supplementary ' + kind + ' ' + code + '. ' + title + '}')
        P.extend(parts)

    # ---------------------------------------------------------- S13 alpha taramasi (V5) --------
    s13_csv = 'Supplementary_Table_S13_Alpha_Sweep.csv'
    s13_cap = SUP / 'Supplementary_Table_S13_Caption.txt'
    if (SUP / s13_csv).exists() and s13_cap.exists():
        baslik = 'Stage~II weight-blend sensitivity'
        P.append(r'\newpage\section{Supplementary Table S13. ' + baslik + '}')
        P.append(longtable(read_csv(s13_csv), 'Supplementary Table S13. ' + baslik + '.', 'tab:s13'))
        P.append(esc(s13_cap.read_text(encoding='utf-8-sig').strip()
                     .replace('Supplementary Table S13. ', '')))

    P.append(r'\end{document}')
    OUT.write_text('\n\n'.join(P) + '\n', encoding='utf-8')
    t = OUT.read_text(encoding='utf-8')
    print(f'yazildi: {OUT}  ({len(t.splitlines())} satir)')

    # --- denetim: eslenmemis Unicode kaldi mi ---
    from collections import Counter
    kalan = Counter(ch for ch in t if ord(ch) > 127 and ch not in GUVENLI)
    if kalan:
        print('\nUYARI - eslenmemis Unicode (UNI haritasina eklenmeli):')
        for ch, k in kalan.most_common():
            print(f'   U+{ord(ch):04X}  {k:5d}  {ch!r}')
        return 1
    print('Unicode denetimi: temiz')
    return 0


if __name__ == '__main__':
    sys.exit(main())
