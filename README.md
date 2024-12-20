# Parkrun map

![Example usage](demo.gif)

Like to parkrun? This project helps you to visualize where you've been running, and where you could go next.
Simply run the app locally with Python, and enter an athlete ID (e.g. your own one). 

We use Plotly Dash to render parkrun participation on a map for a given athlete.
The map initially starts out centred on your home parkrun course - the one you've visited most - just zoom out if you've gone farther afield.

_Warning: Running this project will programmatically visit the athlete's results page for each athlete ID that you submit._

## Installation

Set up this python project using a virtual environment, then installing the dependencies with `pip`:

```bash
mkvirtualenv parkrun-map
pip install -r requirements.txt
```

## Run it

You can use the `waitress` WSGI server to run `map_app.py` as follows:

```bash
PORT=2070
waitress-serve --port=$PORT parkrun_map.map_app:map_app.server
echo "paste http://0.0.0.0:$PORT into your browser"
```

## A-Z Mode <sup>[NEW]</sup>

This mode shows you how far progressed you are through the "parkrun A-Z", accessible via the "A-Z mode" checkbox.
At a minimum it shows which letters the athlete has achieved (and which ones are still missing) by looking at the first
letters of each event you have participated in. If "Show missing events" is also ticked, then A-Z mode filters it to
show only those missing events that would give you a new letter (with the closest one for each remaining letter highlighted
by being a bit bigger).

Hopefully this mode will provide renewed focus for hungry parkrun conquistador(a)s - enjoy!


![Example from the author](https://user-images.githubusercontent.com/13883308/263394817-581c9ff0-f14e-43db-92e9-c3f97ef7c523.png)

## About

_Disclaimer: The author is in no way affiliated to parkrun Limited, except for being an avid fan of this great event._

[parkrun](https://www.parkrun.com) is a volunteer-led health and well-being project that runs every Saturday morning in many parks around the world
(Sundays for junior events). Start your weekend by turning up to a nearby park then walk, jog, or run 5km with dozens - if not hundreds - of other people of all different
speeds and abilities. When finished, pat yourself on the back, feel the endorphin boost and grab a coffee with other like-minded participants. 

It's free, and always will be. Find out more info on the website. 

<a href="https://www.parkrun.com" target="_blank"><img src="http://www.eynshamroadrunners.org.uk/wp-content/uploads/2015/09/Parkrun_32.jpg" alt="Parkrun logo" width="200"/></a>