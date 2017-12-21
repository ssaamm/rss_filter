import datetime as dt
import logging
import time
from collections import namedtuple

import PyRSS2Gen as rss
import feedparser
from flask import Flask, abort

FilteredFeed = namedtuple('FilteredFeed', 'url title_disqualifiers')

app = Flask(__name__)


def remove_items(entries, title_includes=[]):
    for entry in entries:
        if any(phrase.lower() in entry['title'].lower() for phrase in title_includes):
            logging.info('filtered out %s', entry['title'])
            continue

        yield entry


def datetime_from_struct_time(st: time.struct_time):
    return dt.datetime(year=st.tm_year, month=st.tm_mon, day=st.tm_mday, hour=st.tm_hour, minute=st.tm_min,
                       second=st.tm_sec)

def build_rss_item(feedparser_item):
    description = feedparser_item['summary']
    if 'content' in feedparser_item:
        if len(feedparser_item['content']) > 1:
            logging.warning('more content than expected')
        description = '<br>'.join(c['value'] for c in feedparser_item['content'] if c['type'] == 'text/html')

    return rss.RSSItem(title=feedparser_item['title'],
                       link=feedparser_item['link'],
                       description=description,
                       author=feedparser_item['author'],
                       categories=[tag['term'] for tag in feedparser_item.get('tags', [])],
                       guid=feedparser_item['id'],
                       pubDate=datetime_from_struct_time(feedparser_item['published_parsed']),
                       source=None)

known_feeds = {
    'highscalability': FilteredFeed(url='https://feeds.feedburner.com/HighScalability?format=xml',
                                    title_disqualifiers=['Sponsored Post']),
    'ourdailybears': FilteredFeed(url='http://www.ourdailybears.com/rss/current',
                                  title_disqualifiers=['Game Thread', 'Podcast Episode', 'Open Thread',
                                                       'Facebook Live']),
    'dappered': FilteredFeed(url='https://dappered.com/feed/',
                             title_disqualifiers=["thanks to Dappered's advertisers"])
}

feed_cache = {}


@app.route('/feed/<name>')
def filter_feed(name):
    try:
        feed = known_feeds[name]
    except KeyError:
        return abort(404)

    fifteen_minutes_ago = dt.datetime.utcnow() - dt.timedelta(minutes=15)
    if name not in feed_cache or feed_cache[name].lastBuildDate < fifteen_minutes_ago:
        logging.info('feed_cache miss')
        input_feed = feedparser.parse(feed.url)
        output_feed = rss.RSS2(
            title=input_feed['feed']['title'],
            link=input_feed['feed']['link'],
            description=input_feed['feed']['subtitle'],
            lastBuildDate=dt.datetime.utcnow(),
            items=[build_rss_item(entry) for entry in
                   remove_items(input_feed['entries'], title_includes=feed.title_disqualifiers)],
        )

        feed_cache[name] = output_feed
    else:
        logging.info('feed_cache hit')

    return feed_cache[name].to_xml()


if __name__ == '__main__':
    app.run(debug=True)
