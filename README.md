![Parkrun logo](https://en.wikipedia.org/wiki/Parkrun#/media/File:Parkrun_Logo.svg)

# Parkrun mapper

![Example usage](demo.gif)

Like to parkrun? This project helps you to visualize where you've been running, and where you could run next.
Simply run the app locally, and enter an athlete ID (e.g. your own one). 

We use Plotly Dash to render parkrun participation on a map for a given athlete.
The map initially starts out centred on your home parkrun course - the one you've visited most - just zoom out if you've gone farther afield.


_Warning: Running this project will programmatically visit the athlete's home results page for each athlete ID that you submit._

_Disclaimer: The author is in no way affiliated to parkrun Limited, except for being an avid enthusiast for this great event._

## Installation

Set up this python project using a virtual environment, then installing the dependencies with `pip`:

```bash
$ mkvirtualenv parkrun-map
$ pip install -r requirements.txt
```

## Run it

You can use the `waitress` WSGI server to run `map_app.py` as follows:

```bash
$ PORT=2070
$ waitress-serve --port=$PORT parkrun_map.map_app:map_app.server
$ echo "paste http://0.0.0.0:$PORT into your browser"
```