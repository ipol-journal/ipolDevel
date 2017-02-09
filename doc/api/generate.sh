#!/bin/bash
./docstring_scanner.py > docstrings.tex
pdflatex api.tex
