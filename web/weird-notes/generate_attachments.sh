#!/bin/bash

rm -rf attachments
mkdir attachments
cp -r src/* attachments
cd attachments

rm -rf node_modules
rm -rf db.sqlite
rm -rf src/db.sqlite

zip -r ../weird-notes.zip *
rm -rf *
mv ../weird-notes.zip .