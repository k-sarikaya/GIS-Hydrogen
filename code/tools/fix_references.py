# -*- coding: utf-8 -*-
"""Dogrulanmis kaynakca duzeltmelerini manuscript.tex'e uygular.

Her kayit yayinci sayfasindan (citation_* metadata) veya indeksli kayittan okundu.
Her blok anahtarina gore bulunur ve butun olarak degistirilir; bir anahtar
bulunamazsa veya birden fazla eslesirse HICBIR degisiklik yazilmaz.

Kullanim:  python code/tools/fix_references.py [--dry-run]
"""
import argparse
import re
import sys
from pathlib import Path

TEX = Path(__file__).resolve().parents[2] / 'manuscript' / 'manuscript.tex'

# anahtar -> (yeni etiket, yeni govde)
FIXES = {
    'akhlaghi2020design': (
        r'Fazli-Khalaf et~al.(2020)',
        r'Fazli-Khalaf, M., Naderi, B., Mohammadi, M., Pishvaee, M.S., 2020. Design of a sustainable and reliable hydrogen supply chain network under mixed uncertainties: A case study. International Journal of Hydrogen Energy 45~(59), 34503--34531. https://doi.org/10.1016/j.ijhydene.2020.05.276'),
    'camelo2025milp': (
        r'Camelo et~al.(2025)',
        r'Camelo, M.M., de~Andrade, C.F., de~Athayde Prata, B.A., 2025. A mixed-integer linear programming model for optimizing green hydrogen supply chain networks. International Journal of Hydrogen Energy 118, 134--145. https://doi.org/10.1016/j.ijhydene.2025.02.138'),
    'gassert2025gis': (
        r'Gargi et~al.(2026)',
        r'Gargi, Elberry, A.M., J{\"a}rvinen, M., Adolfsson, A., Thakur, J., 2026. GIS-based multi-criteria site suitability analysis of green hydrogen for decarbonisation of the iron \& steel industry in Sweden. Energy 360 5, 100071. https://doi.org/10.1016/j.energ.2026.100071'),
    'haase2025techno': (
        r'Scheffler et~al.(2025)',
        r'Scheffler, F., Imdahl, C., Zellmer, S., Herrmann, C., 2025. Techno-economic and environmental assessment of renewable hydrogen import routes from overseas in 2030. Applied Energy 380, 125073. https://doi.org/10.1016/j.apenergy.2024.125073'),
    'janzen2025quantifying': (
        r'Frischmuth et~al.(2024)',
        r'Frischmuth, F., Berghoff, M., Braun, M., H{\"a}rtel, P., 2024. Quantifying seasonal hydrogen storage demands under cost and market uptake uncertainties in energy system transformation pathways. Applied Energy 375, 123991. https://doi.org/10.1016/j.apenergy.2024.123991'),
    'wang2025designing': (
        r'Jin et~al.(2025)',
        r'Jin, L., Rossi, M., Monforti Ferrario, A., Mennilli, F., Comodi, G., 2025. Designing hybrid energy storage systems for steady green hydrogen production in residential areas: A GIS-based framework. Applied Energy 389, 125765. https://doi.org/10.1016/j.apenergy.2025.125765'),
    'zhao2026robust': (
        r'Shao et~al.(2026)',
        r'Shao, Z., Lu, X., Ren, Z., Zhou, Y., Yan, L., 2026. Robust hydrogen supply chain network design for transport sector under demand uncertainty: A case study. Results in Engineering 29, 109178. https://doi.org/10.1016/j.rineng.2026.109178'),
    'zhou2025optimization': (
        r'Yu et~al.(2025)',
        r'Yu, Z., Wu, X., Wei, B., Sun, Y., Wang, H., 2025. Optimization of the future hydrogen supply chain for China: A new design of hydrogen storage and transportation. International Journal of Hydrogen Energy 105, 701--718. https://doi.org/10.1016/j.ijhydene.2024.12.149'),
    'qadrdan2024great': (
        r'Dergunova and Lyden(2024)',
        r"Dergunova, T., Lyden, A., 2024. Great Britain's hydrogen infrastructure development --- Investment priorities and locational flexibility. Applied Energy 375, 124017. https://doi.org/10.1016/j.apenergy.2024.124017"),
    'zhang2024optimizing': (
        r'Park et~al.(2024)',
        r'Park, J., Kang, S., Kim, S., Kim, H., Kim, S.-K., Lee, J.H., 2024. Optimizing green hydrogen systems: Balancing economic viability and reliability in the face of supply-demand volatility. Applied Energy 368, 123492. https://doi.org/10.1016/j.apenergy.2024.123492'),
    'solomon2024techno': (
        r'Kim et~al.(2024)',
        r'Kim, S., Park, J., Chung, W., Adams, D., Lee, J.H., 2024. Techno-economic analysis for design and management of international green hydrogen supply chain under uncertainty: An integrated temporal planning approach. Energy Conversion and Management 301, 118010. https://doi.org/10.1016/j.enconman.2023.118010'),
    'solomon2024cost': (
        r'Solomon et~al.(2024)',
        r'Solomon, M.D., Heineken, W., Scheffler, M., Birth-Reichert, T., 2024. Cost optimization of compressed hydrogen gas transport via trucks and pipelines. Energy Technology 12~(1), 2300785. https://doi.org/10.1002/ente.202300785'),
    'li2023hydrogen': (
        r'Monteiro and Brito(2023)',
        r'Monteiro, E., Brito, P.S.D., 2023. Hydrogen supply chain: Current status and prospects. Energy Storage 5~(7), e466. https://doi.org/10.1002/est2.466'),
    'fan2024large': (
        r'Ma et~al.(2024)',
        r'Ma, N., Zhao, W., Wang, W., Li, X., Zhou, H., 2024. Large scale of green hydrogen storage: Opportunities and challenges. International Journal of Hydrogen Energy 50, 379--396. https://doi.org/10.1016/j.ijhydene.2023.09.021'),
    'gul2023pv': (
        r'G{\"u}l and Aky{\"u}z(2023)',
        r'G{\"u}l, M., Aky{\"u}z, E., 2023. Techno-economic viability and future price projections of photovoltaic-powered green hydrogen production in strategic regions of Turkey. Journal of Cleaner Production 430, 139627. https://doi.org/10.1016/j.jclepro.2023.139627'),
    'dagistanli2024facility': (
        r'Da{\u{g}}{\i}stanl{\i} and Kurtay(2024)',
        r'Da{\u{g}}{\i}stanl{\i}, H.A., Kurtay, K.G., 2024. Facility location selection for ammunition depots based on GIS and Pythagorean Fuzzy WASPAS. Journal of Operations Intelligence 2~(1), 36--49. https://doi.org/10.31181/jopi2120247'),
    'rekik2024spatial': (
        r'Rekik and El~Alimi(2024)',
        r'Rekik, S., El~Alimi, S., 2024. A spatial ranking of optimal sites for solar-driven green hydrogen production using GIS and multi-criteria decision-making approach: A case of Tunisia. Energy Exploration \& Exploitation 42~(6), 2150--2190. https://doi.org/10.1177/01445987241268072'),
    'karayel2023green': (
        r'Karayel et~al.(2023)',
        r'Karayel, G.K., Javani, N., Dincer, I., 2023. Green hydrogen production potential in Turkey with wind power. International Journal of Green Energy 20~(2), 129--138. https://doi.org/10.1080/15435075.2021.2023882'),
    'ajanovic2024future': (
        r'Ajanovic et~al.(2024)',
        r'Ajanovic, A., Sayer, M., Haas, R., 2024. On the future relevance of green hydrogen in Europe. Applied Energy 358, 122586. https://doi.org/10.1016/j.apenergy.2023.122586'),

    # --- 2. parti: DOI eksik klasikler + bir yazar duzeltmesi -----------------
    'atanassov1986intuitionistic': (
        r'Atanassov(1986)',
        r'Atanassov, K.T., 1986. Intuitionistic fuzzy sets. Fuzzy Sets and Systems 20~(1), 87--96. https://doi.org/10.1016/S0165-0114(86)80034-3'),
    'diakoulaki1995determining': (
        r'Diakoulaki et~al.(1995)',
        r'Diakoulaki, D., Mavrotas, G., Papayannakis, L., 1995. Determining objective weights in multiple criteria problems: The critic method. Computers \& Operations Research 22~(7), 763--770. https://doi.org/10.1016/0305-0548(94)00059-H'),
    'mulvey1995robust': (
        r'Mulvey et~al.(1995)',
        r'Mulvey, J.M., Vanderbei, R.J., Zenios, S.A., 1995. Robust optimization of large-scale systems. Operations Research 43~(2), 264--281. https://doi.org/10.1287/opre.43.2.264'),
    'triantaphyllou1997sensitivity': (
        r'Triantaphyllou and S{\'a}nchez(1997)',
        r"Triantaphyllou, E., S{\'a}nchez, A., 1997. A sensitivity analysis approach for some deterministic multi-criteria decision-making methods. Decision Sciences 28~(1), 151--194. https://doi.org/10.1111/j.1540-5915.1997.tb01306.x"),
    'inuiguchi2000possibilistic': (
        r"Inuiguchi and Ram{\'\i}k(2000)",
        r"Inuiguchi, M., Ram{\'\i}k, J., 2000. Possibilistic linear programming: A brief review of fuzzy mathematical programming and a comparison with stochastic programming in portfolio selection problem. Fuzzy Sets and Systems 111~(1), 3--28. https://doi.org/10.1016/S0165-0114(98)00449-7"),
    'pishvaee2010possibilistic': (
        r'Pishvaee and Torabi(2010)',
        r'Pishvaee, M.S., Torabi, S.A., 2010. A possibilistic programming approach for closed-loop supply chain network design under uncertainty. Fuzzy Sets and Systems 161~(20), 2668--2683. https://doi.org/10.1016/j.fss.2010.04.010'),
    # YAZAR DUZELTMESI: bu makale Pishvaee, Razmi & Torabi'nin degil.
    'pishvaee2016multi': (
        r'Bairamzadeh et~al.(2016)',
        r'Bairamzadeh, S., Pishvaee, M.S., Saidi-Mehrabad, M., 2016. Multiobjective robust possibilistic programming approach to sustainable bioethanol supply chain design under multiple uncertainties. Industrial \& Engineering Chemistry Research 55~(1), 237--256. https://doi.org/10.1021/acs.iecr.5b02875'),
    'zavadskas2012optimization': (
        r'Zavadskas et~al.(2012)',
        r'Zavadskas, E.K., Turskis, Z., Antucheviciene, J., Zakarevicius, A., 2012. Optimization of weighted aggregated sum product assessment. Elektronika ir Elektrotechnika 122~(6), 3--6. https://doi.org/10.5755/j01.eee.122.6.1810'),
    # YIL DUZELTMESI: cilt/sayi Agustos 2014 sayisina ait; 2013 erken erisim tarihi.
    'yager2013pythagorean': (
        r'Yager(2014)',
        r'Yager, R.R., 2014. Pythagorean membership grades in multicriteria decision making. IEEE Transactions on Fuzzy Systems 22~(4), 958--965. https://doi.org/10.1109/TFUZZ.2013.2278989'),
    'rezaei2016best': (
        r'Rezaei(2016)',
        r'Rezaei, J., 2016. Best-worst multi-criteria decision-making method: Some properties and a linear model. Omega 64, 126--130. https://doi.org/10.1016/j.omega.2015.12.001'),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    text = TEX.read_text(encoding='utf-8')
    out, applied, problems = text, [], []

    for key, (label, body) in FIXES.items():
        pat = re.compile(r'\\bibitem\[[^\]]*\]\{' + re.escape(key) + r'\}\n.*?(?=\n\n)', re.S)
        hits = pat.findall(out)
        if len(hits) != 1:
            problems.append(f'{key}: {len(hits)} eslesme')
            continue
        new = '\\bibitem[' + label + ']{' + key + '}\n' + body
        out = pat.sub(lambda _m, n=new: n, out, count=1)
        applied.append(key)

    if problems:
        print('DEGISIKLIK YAZILMADI. Sorunlu anahtarlar:')
        for p in problems:
            print('  ', p)
        sys.exit(1)

    for key in applied:
        print(f'duzeltildi: {key}')
    print(f'\n{len(applied)}/{len(FIXES)} kayit duzeltildi.')

    if a.dry_run:
        print('(dry-run: dosya yazilmadi)')
        return
    TEX.write_text(out, encoding='utf-8')
    print(f'yazildi: {TEX}')


if __name__ == '__main__':
    main()
