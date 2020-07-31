import tweepy
from datetime import datetime, timedelta
import secret  # file to hold keys & tokens

auth = tweepy.OAuthHandler(secret.twitter_API_key, secret.twitter_API_secret_key)
auth.set_access_token(secret.twitter_Access_token, secret.twitter_Access_secret_token)

# The central account doing all the posting/sending
id_aka_handle = "AlbumMerchBot"  # no @ needed
user_id = "Album/Merch Bot"

api = tweepy.API(auth, wait_on_rate_limit=True)  # will wait if we stream too many tweets quickly


# after entering json of an user:
# 1. 'url' returns the link in bio(none if empty), all links will be shortened & start with https://t.co
# 2. 'screen_name' returns twitter handle (no @, unique)
# 3. name is the username above twitter handle (can have multiple same names across users)

def get_user_tweets(handle, count=5):  # at most can get 200 most recent tweets
    """
    :param handle:  string of a certain twitter handle (ie: @BBBonk_)
    :return: list of that handle's most recent tweets tweets after processing/cleaning
    """
    tweets = api.user_timeline(handle, count=count)
    cleaned_tweets = []
    for i in range(count):
        tweet = tweets[i]._json['text']
        cleaned_tweets.append(tweet)
    return cleaned_tweets


def links_in_bio(handles):
    """
    :param handles: list of Users that we want to get links in bio from
    :return: dict mapping artist to their link in bio
    """
    bio_links = {handle._json['screen_name']: handle._json['url'] for handle in handles if handle._json['url'] is not None}
    return bio_links


def send_biolinks(link_dict, rec_handle):
    """
    :param link_dict: dict mapping artist to their link in bio
    :param rec_handle: handle of account intended to receive the links
    :return: None, should just send each artist/link to rec_handle
    """
    rec_id = api.get_user(rec_handle)._json['id']
    message = ''
    for artist, link in link_dict.items():
        message += str(artist) + '\'s bio link: ' + link + '\n'

    api.send_direct_message(recipient_id=rec_id, text=message)  # send the dm to handle provided thru bot


def check_tweets(rec_handle, num=7):
    """
    :param rec_handle: the twitter user that is getting the notifications
    :param num: number of tweets we will pull from each artist
    :return: num of tweets sent thru dm, after sending
    """
    tweets_sent = 0
    artists = api.friends(id_aka_handle)  # returns all accounts the bot is following as User Objects
    cur_time = datetime.now()
    two_wks_ago = cur_time - timedelta(days=14)
    for artist in artists:
        artist_tweets = api.user_timeline(artist.screen_name, count=num)
        print('Now checking...'+ artist.screen_name)
        for tweet in artist_tweets:
            if tweet.created_at <= two_wks_ago:  # if the tweet is older than two weeks then move on to next tweet (we only care about recent drops)
                continue
            message = ''
            if tweet.entities['urls'] and not tweet.is_quote_status:  # if the tweet contains a url and is not a quoted tweet
                if not tweet.entities['urls'][0]['display_url'].startswith('twitter.com'): # ensures the url is not just another twitter link (retweet or photo)
                    message += 'https://twitter.com/' +artist.screen_name+ '/status/' + tweet.id_str
                    api.send_direct_message(api.get_user(rec_handle).id, message)
                    tweets_sent += 1
    return tweets_sent


if __name__ == '__main__':
    print('Hello, Welcome to AlbumMerchBot...')
    username = input('What is the account handle (no @) that will be receiving notifications? ')
    link_bool = input('Would you like to also receive bio links? [y/n] ')
    print()

    if link_bool.lower() == 'y' or link_bool.lower() == 'yes':
        send_biolinks(links_in_bio(api.friends(id_aka_handle)), rec_handle=username)
        print('BioLinks sent. Check dms \n')

    num_sent = check_tweets(rec_handle=username)
    print('done checking. '+str(num_sent)+' tweets have been sent to your dms.')
