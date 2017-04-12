#!/usr/bin/env bash
find . -name "thumbnail_*" -exec rename s/thumbnail_// * {} \;