from __future__ import print_function
from __future__ import unicode_literals

from builtins import str, bytes, dict, int
from builtins import range

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pattern.web import VK, plaintext
from pattern.web import SEARCH


# This example retrieves data from VKontakte social network.

# VKontakte has API which allows users to collect different types of data from the network.
# To use this API you should have an access_token, which can be obtained from vk website.


########################## The instruction to get access_token: #################################

# We will consider the authorization method in the social network VKontakte by a direct link through
# the VKontakte API (based on the OAuth protocol), called Implicit flow. Authorization by this method
# is performed through the VKontakte application specified in the form of an ID. This is the most
# secure method of authorization.

# The method of obtaining a token is to go through a special link containing the ID of created VKontakte application:
# https://oauth.vk.com/authorize?client_id=APP_ID&scope=notify,photos,friends,audio,video,notes,pages,docs,status,questions,offers,wall,groups,messages,notifications,stats,ads,offline&redirect_uri=http://api.vk.com/blank.html&display=page&response_type=token

# So, where to get the APP_ID?

######################### Receiving a token through its own application: ########################

# 1)register in VK - https://vk.com

# 2)go to the application manage: https://vk.com/apps?act=manage

# 3)create new application (chose standalone application)

# 4)next, you need to approve the application by getting a confirmation code on your phone and typing it
# in a special field. Also, during the application approval process, you can link your mobile device
# to the VKontakte account. To do this, click the «Link Device» button. Otherwise, just click on the
# «Confirm via SMS» link without attaching the device to the page.
#
# 5)After confirmation, you will see a page with information about the created application. In the left menu,
# click on the "Settings" item. There you can find the client_id, that is, the ID of your VKontakte application.
#
# 6)This ID needs to be copied and pasted into our link instead of APP_ID. It should look something like this:
#
# https://oauth.vk.com/authorize?
# client_id=123456&scope=notify,photos,friends,audio,video,notes,pages,docs,status,questions,offers,wall,groups,messages,notifications,stats,ads,offline&redirect_uri=http://api.vk.com/blank.html&display=page&response_type=token
#
# 7)Next, if you need to get the access key, you just need to go to this link.
# The link with access token will look like:
#
# http://api.vk.com/blank.html#access_token=*****&expires_in=0&user_id=*****


############################################ Limits: ################################################
# The VKontakte API methods with the user access key can be accessed no more often than 3 times per second
#
# Number of requests limits:
#
# newsfeed.search — 1000 per day;
# wall.search — 1000 per day;
# wall.get — 5000 per day.



# Methods:
# 1. retrieving a user's profile description
# 2. retrieving user's posts from the profile wall
# 3. retrieving posts from the newsfeed for a search keyword

access_token = None

def test_vk_api(access_token):

    if access_token is None:
        print("No access_token")
        return

    engine = VK(lisense=access_token, language='en')

    # 1. retrieving a user's profile description

    # - uid
    # - first_name
    # - last_name
    #
    # Additional fields:
    # - sex
    # - bdate
    # - city
    # - country
    # - nickname
    # - status
    # - followers_count
    # - photo_max_orig
    # - screen_name
    # - counters (number of different items):
    #        'albums',
    #        'videos',
    #        'audios',
    #        'notes',
    #        'photos',
    #        'friends',
    #        'online_friends',
    #        'mutual_friends',
    #        'followers',
    #        'subscriptions',
    #        'pages'

    users_info = engine.get_users_info([1, 34692281, "neolai"])
    print("Collected info of {} users".format(len(users_info)))
    print(users_info[0])
    print("")

    # 2. retrieving user's posts from the profile wall

    wall_posts = engine.get_user_posts(user_id=1, count=100, posts_type="others")
    print("Collected {} posts from the wall".format(len(wall_posts)))
    print(wall_posts[0])
    print("")

    # 3. retrieving posts from the newsfeed for a search keyword

    newsfeed_posts = engine.get_newsfeed_posts(query="FIFA", count=100)
    print("Collected {} posts from the newsfeed".format(len(newsfeed_posts)))
    print(newsfeed_posts[0])
    print("")

test_vk_api(access_token)


