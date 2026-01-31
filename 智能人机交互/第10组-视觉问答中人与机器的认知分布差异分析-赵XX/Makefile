build:
	xelatex -output-directory=documents progress.tex
	xelatex -shell-escape -output-directory=documents -synctex=1 -interaction=nonstopmode -file-line-error main.tex
	xelatex -shell-escape -output-directory=documents -synctex=1 -interaction=nonstopmode -file-line-error main.tex