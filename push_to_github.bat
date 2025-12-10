@echo off
echo Adding all changes...
git add .

echo Committing changes...
git commit -m "Update project files"

echo Pushing to GitHub...
git push origin main

echo Done!
