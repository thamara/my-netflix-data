import argparse
import csv
import jinja2
import json
import math
import os
import re

# 0:01:05 -> 65
def durationTimeToSeconds(duration):
    try:
        [hour, minutes, seconds] = duration.split(':')
        return int(hour)*3600 + int(minutes)*60 + int(seconds)
    except:
        return 0

# 65 -> 00:01:05
def secondsToDurantion(seconds):
    hours = math.floor(seconds/3600)
    remainingSeconds = seconds - (hours*3600)
    minutes = math.floor(remainingSeconds/60)
    remainingSeconds = remainingSeconds - (minutes*60)
    return '{:02d}:{:02d}:{:02d}'.format(hours, minutes, remainingSeconds)


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-input", help="Viewing activity CSV file location")
    parser.add_argument("-output", help="Path for the output files")
    return parser.parse_args()


def parseNetflixData(inputFileName):
    # CSV headers:
    # Profile Name,Start Time,Duration,Attributes,Title,Supplemental Video Type,Device Type,Bookmark,Latest Bookmark,Country
    netflixData = []
    with open(inputFileName) as netflixCSV:
        for row in csv.reader(netflixCSV):
            supplementalVideoType = row[5]
            if len(supplementalVideoType):
                continue

            profile = row[0]
            date = row[1]
            duration = row[2]
            title = row[4]
            serieMatching = re.search(
                r'(.*): (Season|Part|Vol\.|Series|Chapter|Temporada|Parte|Universo|Capítulo) ([ a-zA-Záéíê\d]*( Remix)*): (.*)', title)
            if serieMatching:
                netflixData.append({'movie': '',
                                    'serie': serieMatching.group(1),
                                    'season': 'Season {}'.format(serieMatching.group(3)),
                                    'episode': '{}'.format(serieMatching.group(5)),
                                    'date': date,
                                    'profile': profile,
                                    'duration': durationTimeToSeconds(duration)})
            else:
                netflixData.append({'movie': title,
                                    'serie': '',
                                    'season': '',
                                    'episode': '',
                                    'date': date,
                                    'profile': profile,
                                    'duration': durationTimeToSeconds(duration)})
        # Drop first as it's the header
        netflixData.pop(0)
    return netflixData


def getMoviesAndSeriesObj(data):
    moviesWatchedTimes = {}
    seriesWatchedTime = {}
    profiles = set()
    for item in data:
        profile = item['profile']
        profiles.add(profile)
        if not profile in moviesWatchedTimes:
            moviesWatchedTimes[profile] = {}
        if not profile in seriesWatchedTime:
            seriesWatchedTime[profile] = {}

        if item['movie']:
            movie = item['movie']
            if not movie in moviesWatchedTimes[profile]:
                moviesWatchedTimes[profile][movie] = 0
            moviesWatchedTimes[profile][movie] += item['duration']
        if item['serie']:
            serie = item['serie']
            if not serie in seriesWatchedTime[profile]:
                seriesWatchedTime[profile][serie] = {}

            season = item['season']
            if not season in seriesWatchedTime[profile][serie]:
                seriesWatchedTime[profile][serie][season] = {}

            episode = item['episode']
            if not episode in seriesWatchedTime[profile][serie][season]:
                seriesWatchedTime[profile][serie][season][episode] = 0

            seriesWatchedTime[profile][serie][season][episode] += item['duration']
    return [profiles, moviesWatchedTimes, seriesWatchedTime]


def getOutputFilePath(outputDir, fileName):
    if not os.path.isdir(outputDir):
        try:
            os.mkdir(outputDir)
        except:
            return None
    return os.path.join(outputDir, fileName)


def generateHTMLPage(outputDir, profiles, moviesWatchedTimes, seriesWatchedTime):
    # Datatable
    watchedTableInfo = []
    for profile in moviesWatchedTimes:
        for item in moviesWatchedTimes[profile]:
            watchedTableInfo.append(dict(profile=profile, movie=item, type='Movie',
                                         total_seconds=moviesWatchedTimes[profile][item], count=secondsToDurantion(moviesWatchedTimes[profile][item])))

    for profile in seriesWatchedTime:
        for item in seriesWatchedTime[profile]:
            totalWatchedTime = 0
            seasons = seriesWatchedTime[profile][item]
            for season in seasons:
                for episode in seasons[season]:
                    totalWatchedTime += seriesWatchedTime[profile][item][season][episode]
            watchedTableInfo.append(dict(profile=profile, title=item, type='Series',
                                         total_seconds=totalWatchedTime, total_time=secondsToDurantion(totalWatchedTime)))

    loader = jinja2.FileSystemLoader('netflix-data-template.html')
    env = jinja2.Environment(loader=loader)
    with open(getOutputFilePath(outputDir, 'index.html'), 'w') as output:
        output.write(env.get_template('').render(
            watched_table=watchedTableInfo))


def generateJsonForVisualization(outputDir, profiles, moviesWatchedTimes, seriesWatchedTime):
    visualizationJson = {"name": "Profiles", "children": []}
    for profile in profiles:
        profiledMovieItems = []
        for item in moviesWatchedTimes[profile]:
            profiledMovieItems.append({"name": item,
                                       "value": moviesWatchedTimes[profile][item]})
        profileMovies = {"name": "Movies", "children": profiledMovieItems}

        profiledSeriesItems = []
        for item in seriesWatchedTime[profile]:
            seasons = seriesWatchedTime[profile][item]
            allSeasons = []
            for season in seasons:
                episodes = seasons[season]
                totalTimeForEpisodes = 0
                for episode in episodes:
                    totalTimeForEpisodes += seriesWatchedTime[profile][item][season][episode]
                allSeasons.append({"name": '{}'.format(season),
                                   "value": totalTimeForEpisodes})
            profiledSeriesItems.append({"name": item, "children": allSeasons})
        profileSeries = {"name": "Series", "children": profiledSeriesItems}

        profileMoviesAndSeries = {"name": profile,
                                  "children": [profileMovies, profileSeries]}
        visualizationJson["children"].append(profileMoviesAndSeries)

    with open(getOutputFilePath(outputDir, 'netflix-data-to-visualize.json'), 'w') as output:
        output.write(json.dumps(visualizationJson, indent=2))


def main():
    args = get_arguments()
    data = parseNetflixData(args.input)
    [profiles, movies, series] = getMoviesAndSeriesObj(data)
    print(series)
    generateJsonForVisualization(args.output, profiles, movies, series)
    generateHTMLPage(args.output, profiles, movies, series)


if __name__ == "__main__":
    main()
