set /p PUBLISH_TOKEN=<publish_token.txt
echo %PUBLISH_TOKEN%
uv publish --token %PUBLISH_TOKEN%
