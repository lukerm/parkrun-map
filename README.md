```
$ mkvirtualenv parkrun-map
$ pip install -r requirements.txt
$ PORT=2070
$ waitress-serve --port=$PORT parkrun_map.map_app:map_app.server
$ echo "paste http://0.0.0.0:$PORT into browser"
```
