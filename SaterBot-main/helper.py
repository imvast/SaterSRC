# Imports
import discord
import os
import urllib.parse as parse
from googleapiclient.discovery import build


# Create embed
def create_embed(text):
    embed = discord.Embed(
        description=text,
        colour=discord.Colour.from_rgb(182,7,7),
    )
    return embed


def youtube_get_id_and_plid(url):
    if url.startswith(('youtu', 'www')):
        url = 'https://'+url
    q = parse.urlparse(url)
    # print(q)
    if 'youtu.be' in q.netloc:
        vid_id = q.path.lstrip('/')
        if q.query.startswith('list='):
            i = q.query.find('&t=')
            if i != -1:
                pl_id = q.query[5:i]
                return(vid_id, pl_id)
            else:
                pl_id = q.query[5:]
                return(vid_id, pl_id)
        else:
            return (vid_id,)
    elif 'youtube' in q.netloc:
        i, j = q.query.find('v='), q.query.find('list=')
        vid_id = ''
        if i != -1:
            for a in range(i+2, len(q.query)):
                if q.query[a] != '&':
                    vid_id += q.query[a]
                else:
                    break
        else:
            return None
        pl_id = ''
        if j != -1:
            for a in range(j+5, len(q.query)):
                if q.query[a] != '&':
                    pl_id += q.query[a]
                else:
                    break
            return (vid_id, pl_id)
        else:
            return (vid_id,)
    else:
        return None


def API_SEARCH(str):
    search_str = ''
    youtube_service = build('youtube', 'v3',
                            developerKey=os.environ.get('Youtube_API'))
    if str.startswith(('https://youtu', 'youtu', 'www.youtu', 'https://www.youtu')):
        search_str = youtube_get_id_and_plid(str)
        if search_str != None:
            if len(search_str) == 2:
                request = youtube_service.playlistItems().list(
                    part='snippet', playlistId=search_str[1], maxResults=50)
                response = request.execute()
                result = [video['snippet']['resourceId']['videoId']
                          for video in response['items']]
                while 'nextPageToken' in response:
                    page = response['nextPageToken']
                    request = youtube_service.playlistItems().list(
                        part='snippet', playlistId=search_str[1], maxResults=50, pageToken=page)
                    response = request.execute()
                    for video in response['items']:
                        result.append(video['snippet']
                                      ['resourceId']['videoId'])
                return result
            else:
                return [search_str[0], ]
        else:
            return None
    else:
        request = youtube_service.search().list(
            part='snippet', q=str, type='video', maxResults=1)
        response = request.execute()
        if response['items'] != []:
            return [response['items'][0]['id']['videoId'], ]
        else:
            return None


