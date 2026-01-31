ifeq ($(OS), Windows_NT)
	MAKEDIR := cmd /c mkdir documents
	BBL = documents\main.aux
else
	MAKEDIR := mkdir -p documents
	BBL = documents/main.aux
endif

build:
	-$(MAKEDIR)
	xelatex -synctex=1 -interaction=nonstopmode -file-line-error -output-directory=documents main.tex
	bibtex $(BBL)
	xelatex -synctex=1 -interaction=nonstopmode -file-line-error -output-directory=documents main.tex
	xelatex -synctex=1 -interaction=nonstopmode -file-line-error -output-directory=documents main.tex
