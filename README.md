# My Netflix Data

See how much time are you spending in a given show.

You can check an example page [here](https://thamara-my-netflix-data.netlify.app/).

![screencapture-my-netflix-data.png]

## Instructions

1. Have Python 3.8 installed
2. Install Jinja: ```pip3 install Jinja2```
3. Request and download your data from [Netlix](https://www.netflix.com/account/getmyinfo). The important file is ```Content_Interaction/ViewingActitivity.csv```.
4. Run script: ```python3 analyze-netflix-data.py -input data/ViewingActivity.csv -output output```
5. Open file in ```output/index.html``` in your browser.

## Improvements to come:
- Filter by date
- Filter watched items with less than X minutes watched
- Include episodes listing
- More visualizations (what time do you usually watch Netflix)
- More...

## Credits
- Uses modified version of [Zoomable Sunburst with Labels](https://bl.ocks.org/vasturiano/12da9071095fbd4df434e60d52d2d58d)