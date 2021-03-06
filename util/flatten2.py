#!/usr/bin/python3

import os
import re
import shutil
import subprocess
import sys
import time


utilDir = os.path.split(os.path.realpath(__file__))[0]
srcDir = os.path.realpath(os.path.join(utilDir, '..'))
buildPDFDir = os.path.realpath(os.path.join(utilDir, '..', 'buildPDF'))


def copyNames(srcDir, dstDir, nameLst):
    """Okopíruje jména z nameLst z adresáře srcDir do dstDir.

    Pokud destDir neexistuje, bude nejdříve vytvořen. Pokud jméno
    z nameLst odpovídá podadresáři, bude případný existující cílový
    podadresář nejdříve smazán a okopírován celý zdrojový znovu.
    """
    # Pokud neexistuje cílový adresář, vyrobíme jej.
    if not os.path.isdir(dstDir):
        os.makedirs(dstDir)

    for name in nameLst:
        src = os.path.join(srcDir, name)
        dst = os.path.join(dstDir, name)

        # Podadresáře kopírujeme celé, soubory taky :)
        if os.path.isdir(src):
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        elif os.path.isfile(src):
            shutil.copy2(src, dst)


# Set list of chapters in the order defined by the index.html. Append also
# the files that are not there (about, colophon).
chapters = [
    'index.html',
    'table-of-contents.html',
    'whats-new.html',
    'installing-python.html',
    'your-first-python-program.html',
    'native-datatypes.html',
    'comprehensions.html',
    'strings.html',
    'regular-expressions.html',
    'generators.html',
    'iterators.html',
    'advanced-iterators.html',
    'unit-testing.html',
    'refactoring.html',
    'files.html',
    'xml.html',
    'serializing.html',
    'http-web-services.html',
    'case-study-porting-chardet-to-python-3.html',
    'packaging.html',
    'porting-code-to-python-3-with-2to3.html',
    'special-method-names.html',
    'where-to-go-from-here.html',
    'troubleshooting.html',
    'changelog.html',
    'about.html',
    'colophon.html',
    ]

# Připravíme cílové adresáře pro HTML a PDF (kopie potřebného).
copyNames(utilDir, buildPDFDir, ['dip3.css', 'prince.css'])
copyNames(srcDir, buildPDFDir, ['i', 'examples'])

# construct regexes used to fix internal xrefs
chapter_href = re.compile(r'<a href="({0})">'.format("|".join(chapters)))
chapter_fragment_href = re.compile(r'<a href="({0})#(.*?)">'.format("|".join(chapters)))
same_chapter_fragment_href = re.compile(r'<a href="#(.*?)"')
id_munge = re.compile(r'\s+id=(.*?)\s*>')

# munge and combine chapter-specific styles
fname = os.path.join(utilDir, 'single-header.html')
with open(fname, encoding='utf-8') as f:
    stamp = time.strftime('%Y-%m-%d', time.localtime())
    contentTpl = f.read()
    header = contentTpl.replace('%%DATE%%', stamp)

fname = os.path.join(utilDir, 'single-header2.html')
with open(fname, encoding='utf-8') as f:
    header2 = f.read()

fname = os.path.join(utilDir, 'single-footer.html')
with open(fname, encoding='utf-8') as f:
    footer = f.read()

singleName = os.path.join(buildPDFDir, 'single.html')
with open(singleName, 'w', encoding='utf-8') as out:
    out.write(header)           # Header before the style definitions.
    out.write('<style>\n')
    for fname in chapters:
        include = False
        id_suffix = os.path.splitext(fname)[0]
        chapter_id = "chapter-" + id_suffix
        filename = os.path.join(srcDir, fname)
        with open(filename, encoding='utf-8') as f:
            for line in f:
                if line.count('</style>'):
                    include = False
                if include and not line.count('counter-reset'):
                    line = '#{0} {1}'.format(chapter_id, line)
                    line = line.replace(',', ', #{0} '.format(chapter_id))
                    out.write(line)
                if line.count('<style>'):
                    include = True
    out.write("</style>\n")
    out.write(header2)          # Header after the style definitions.

    # munge and combine chapters
    for fname in chapters:
        include = False
        id_suffix = os.path.splitext(fname)[0]
        chapter_id = "chapter-" + id_suffix
        filename = os.path.join(srcDir, fname)
        out.write("<div id={0}>\n".format(chapter_id))
        with open(filename, encoding='utf-8') as f:
            for line in f:
                if line.startswith('<body id='):
                    line = line.replace('<body id=', '<div id=')
                    out.write(line)
                elif line.startswith('</body>'):
                    line = line.replace('</body>', '</div>')
                    out.write(line)

                if line.count('<h1>'):
                    include = True
                if line.count('<p class=v') or line.count('<p class=c>&copy;') or line.count('<p class=c>©'):
                    include = False
                if line.count('<p id=toc'):
                    line = line.replace(' id=toc', '')
                if include:
                    # fix cross-references
                    line = id_munge.sub(lambda x: " id={0}-{1}>".format(id_suffix, x.group(1)), line)
                    line = same_chapter_fragment_href.sub(lambda x: "<a href=#{0}-{1}".format(id_suffix, x.group(1)), line)
                    line = chapter_href.sub(lambda x: "<a href=#chapter-" + x.group(1).replace('.html', '') + ">", line)
                    line = chapter_fragment_href.sub(lambda x: "<a href=#{0}-{1}>".format(x.group(1).replace('.html', ''), x.group(2)) , line)
                    out.write(line)
        out.write("</div>\n")


    out.write(footer)
    out.close()


# Vygenerujeme PDF spuštěním Prince.exe s parametry.
programFiles = os.getenv('ProgramFiles(x86)')
if programFiles is None:
    programFiles = os.getenv('ProgramFiles')

prince = os.path.join(programFiles, 'Prince', 'Engine', 'bin', 'Prince.exe')
prince = os.path.normpath(prince)

cmd = '"{}" -s prince.css single.html -o PonormeSeDoPythonu3.pdf'.format(prince)

cwdsaved = os.getcwd()
os.chdir(buildPDFDir)
subprocess.call(cmd)  # Prince
os.chdir(cwdsaved)
