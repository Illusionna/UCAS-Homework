ifeq ($(OS), Windows_NT)
	REMOVE = cmd /c rmdir /s /q
	MAKEDIR = cmd /c mkdir documents
	BBL = documents\main.aux
else
	REMOVE = rm -rf
	MAKEDIR = mkdir -p documents
	BBL = documents/main.aux
endif

build:
	-$(MAKEDIR)
	xelatex -synctex=1 -interaction=nonstopmode -file-line-error -output-directory=documents main.tex

all:
	-$(MAKEDIR)
	xelatex -synctex=1 -interaction=nonstopmode -file-line-error -output-directory=documents main.tex
	bibtex $(BBL)
	xelatex -synctex=1 -interaction=nonstopmode -file-line-error -output-directory=documents main.tex
	xelatex -synctex=1 -interaction=nonstopmode -file-line-error -output-directory=documents main.tex

clean:
	-$(REMOVE) documents

count:
	texcount main.tex
