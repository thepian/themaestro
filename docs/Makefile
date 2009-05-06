# Makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD = /Sites/themaestro/bin/sphinx-build
PAPER         =

# Internal variables.
PAPEROPT_a4     = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS   = -d /Sites/themaestro/docs/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) /Sites/themaestro/parts/sphinx

.PHONY: help clean html web pickle htmlhelp latex changes linkcheck

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  html      to make standalone HTML files"
	@echo "  pickle    to make pickle files"
	@echo "  json      to make JSON files"
	@echo "  htmlhelp  to make HTML files and a HTML help project"
	@echo "  latex     to make LaTeX files, you can set PAPER=a4 or PAPER=letter"
	@echo "  changes   to make an overview over all changed/added/deprecated items"
	@echo "  linkcheck to check all external links for integrity"

clean:
	-rm -rf /Sites/themaestro/docs/*

html:
	mkdir -p /Sites/themaestro/docs/html /Sites/themaestro/docs/doctrees
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) /Sites/themaestro/docs/html
	@echo
	@echo "Build finished. The HTML pages are in /Sites/themaestro/docs/html."

pickle:
	mkdir -p /Sites/themaestro/docs/pickle /Sites/themaestro/docs/doctrees
	$(SPHINXBUILD) -b pickle $(ALLSPHINXOPTS) /Sites/themaestro/docs/pickle
	@echo
	@echo "Build finished; now you can process the pickle files."

web: pickle

json:
	mkdir -p /Sites/themaestro/docs/json /Sites/themaestro/docs/doctrees
	$(SPHINXBUILD) -b json $(ALLSPHINXOPTS) /Sites/themaestro/docs/json
	@echo
	@echo "Build finished; now you can process the JSON files."

htmlhelp:
	mkdir -p /Sites/themaestro/docs/htmlhelp /Sites/themaestro/docs/doctrees
	$(SPHINXBUILD) -b htmlhelp $(ALLSPHINXOPTS) /Sites/themaestro/docs/htmlhelp
	@echo
	@echo "Build finished; now you can run HTML Help Workshop with the" \
	      ".hhp project file in /Sites/themaestro/docs/htmlhelp."

latex:
	mkdir -p /Sites/themaestro/docs/latex /Sites/themaestro/docs/doctrees
	$(SPHINXBUILD) -b latex $(ALLSPHINXOPTS) /Sites/themaestro/docs/latex
	@echo
	@echo "Build finished; the LaTeX files are in /Sites/themaestro/docs/latex."
	@echo "Run \`make all-pdf' or \`make all-ps' in that directory to" \
	      "run these through (pdf)latex."

changes:
	mkdir -p /Sites/themaestro/docs/changes /Sites/themaestro/docs/doctrees
	$(SPHINXBUILD) -b changes $(ALLSPHINXOPTS) /Sites/themaestro/docs/changes
	@echo
	@echo "The overview file is in /Sites/themaestro/docs/changes."

linkcheck:
	mkdir -p /Sites/themaestro/docs/linkcheck /Sites/themaestro/docs/doctrees
	$(SPHINXBUILD) -b linkcheck $(ALLSPHINXOPTS) /Sites/themaestro/docs/linkcheck
	@echo
	@echo "Link check complete; look for any errors in the above output " \
	      "or in /Sites/themaestro/docs/linkcheck/output.txt."
