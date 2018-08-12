#!/usr/bin/python3

import getpass
import os
import requests
import ssl
import sys
import shutil
import time
import vk_api
from vk_api.audio import VkAudio


try:
    folder_name = sys.argv[2]
except IndexError:
    folder_name = '/tmp/Music'


def captcha_handler(captcha):
    url = captcha.get_url()
    key = input("Enter captcha code {0}: ".format(url)).strip()
    webbrowser.open(url, new=2, autoraise=True)
    return captcha.try_again(key)

def auth_handler():
    key = input("Enter authentication code: ")
    remember_device = True
    return key, remember_device

def get(self, owner_id, offset=0):
    response = self._vk.http.get(
      'https://m.vk.com/audios{}'.format(owner_id),
      params={'offset': offset},
      allow_redirects=False
    )
    if not response.text:
        raise AccessDenied('You don\'t have permissions to browse {0}\'s audio'.format(owner_id))
    return scrap_data(response.text)

def scrap_data(html):
    soup = BeautifulSoup(html, 'html.parser')
    tracks = []
    for audio in soup.find_all('div', {'class': 'audio_item ai_has_btn'}):
        ai_artist = audio.select('.ai_artist')
        artist = ai_artist[0].text
        link = audio.select('.ai_body')[0].input['value']
        if 'audio_api_unavailable' in link: link = decode_audio_url(link)
        tracks.append({
            'artist': artist,
            'title': audio.select('.ai_title')[0].text,
            'dur': audio.select('.ai_dur')[0]['data-dur'],
            'url': link
        })
    return tracks

def save(url, filename):
    response = requests.get(url, stream=True)
    with open(filename, 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)
    del response

def auth_vk():
    print('Log in to vk.com')
    vk_session = vk_api.VkApi(
        input('Enter login: '),
        getpass.getpass('Enter password: '),
        captcha_handler=captcha_handler,
        auth_handler=auth_handler
    )
    try:
        vk_session.auth()
    except vk_api.AuthError as error_msg:
        print(error_msg)
        sys.exit(1)
    #user_id = vk_session.get_api().users.get()[0]['id']
    user_id = str(sys.argv[1])
    print('Downloading audios from ' + user_id)
    return VkAudio(vk_session), user_id


def main():
    if len(sys.argv) < 2:
        print('Usage: {0} <vk-user-id> [path-to-folder]'.format(sys.argv[0]))
        sys.exit(2)
    vkaudio, user_id = auth_vk()
    progress = 0
    audios = vkaudio.get(user_id, None)
    total = len(audios)
    print('Will be downloaded {0} audio files'.format(total))
    #print(audios)
    print('Music will be saved in {0}'.format(folder_name))
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)
    for i, track in enumerate(audios[::-1]):
        if progress and i < progress - 1: continue
        filename = track['artist'] + ' - ' + track['title']
        escaped_filename = filename.replace("/", "_")
        file_path = folder_name + '/' + escaped_filename +'.mp3'
        print('Downloading [' + str(i + 1) + '/' + str(total) + ']')
        try:
            save(track['url'], file_path)
        except HTTPError:
            print('ERROR: ' + escaped_filename)
        except Exception:
            print('ERROR: ' + escaped_filename + ', launching again...')
            try:
              save(track['url'], escaped_filename +'.mp3')
            except:
              print('Failed to save track after 2 tries [' + str(i + 1) + '/' + str(total) + ']')
              exit()
        sys.stdout.flush()


if __name__ == '__main__':
    main()
