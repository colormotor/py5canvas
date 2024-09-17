#!/usr/bin/env sh


python -m build
twine upload dist/*
