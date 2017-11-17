# "Standard libs" imports
import os
import json
from glob import glob
from config import config, LIQUIDSOAP_TOKEN
from uuid import uuid4                 # FIXME no longer needed i think
from datetime import date              # same

# Flask stuff
from flask import (Flask,
                   render_template,
                   url_for,
                   jsonify,
                   request,
                   redirect,
                   flash)

# Specific app stuff
from . import main
from .forms import SubscribeForm
from .partial_content import *
from .jinja_custom_filters import *
from .. import db                      # FIXME no longer needed i think
from app.models.admin import *
from app.models.event import Event
from app.models.podcast import Podcast
from app.models.section import Section
from app.models.contributor import Contributor
from app.models.blog import BlogPost
from app.models.event import Event
from app.models.channel import Channel
from app.models.tag import Tag
from app.models.page import Page

app = Flask(__name__)


#########################
#  Main pages           #
#########################

def base():
    return render_template( 'base.html',
                            podcasts = Podcast.list(),
                            blog_posts = BlogPost.list(),
                            events = Event.list(),
                            content = request.path
                          )

partial_content = partial_content_decorator(base)
partial_content_no_history = partial_content_no_history_decorator(base)

@main.route('/')
@partial_content
def index():
    return [ 'displayMain',
           { "content": render_template("index.html",
                                        podcasts = Podcast.list(),
                                        blog_posts = BlogPost.list(),
                                        events = Event.list()) } ]


#########################
#  Pages                #
#########################

@main.route('/about')
@partial_content
def about():
    page = Page.query.filter_by(name='À propos').first_or_404()
    return [ 'displayMain',
           { "content": render_template("main_pages/about.html",
                                        page=page) } ]

@main.route('/contrib')
@partial_content
def contribute():
    # create a real "contribute" page
    page = Page.query.filter_by(name='Contribuer').first_or_404()
    return [ 'displayMain',
             { "content": render_template("main_pages/contribute.html",
                                          page=page) } ]

#########################
#  Podcasts             #
#########################

@main.route('/podcasts')
@partial_content
def podcasts():
    page = request.args.get('page', 1, type=int)
    pagination = Podcast.query                         \
        .join(Channel, Channel.id==Podcast.channel_id) \
        .order_by(Podcast.timestamp.desc())            \
        .paginate(page, per_page=10, error_out=False)
    podcasts = pagination.items

    return [ 'displayMain',
             { "content": render_template("main_pages/podcasts.html",
                                          podcasts=podcasts,
                                          pagination=pagination) } ]

@main.route('/podcasts/<id>')
@partial_content
def podcast(id):
    podcast = Podcast.query.filter_by(id = id).first()
    return [ 'displayMain',
             { "content": render_template("elem_pages/podcast.html",
                                          elem=podcast) }]

@main.route('/podcasts/<id>/play')
@partial_content_no_history
def play(id):
    podcast = Podcast.query.filter_by(id = id).first()
    return [ "player.load.bind(player)",
             { "link" : podcast.link,
               "title" : podcast.name } ]

##############################
#  Contributors/Collectives  #
##############################

@main.route('/contributors')
@main.route('/collectives')
@partial_content
def contributors():
    return [ 'displayMain',
             { "content": render_template("main_pages/contributors.html",
                                          contributors=Contributor.list(),
                                          collectives=Collective.list(),
                                         )}]

@main.route('/contributors/<id>')
@partial_content
def contributor(id):
    contributor = Contributor.query.filter_by(id = id).first()
    return [ 'displayMain',
             { "content": render_template("elem_pages/contributor.html",
                                          elem=contributor) }]

@main.route('/collectives/<id>')
@partial_content
def collective(id):
    collective = Collective.query.filter_by(id = id).first()
    return [ 'displayMain',
             { "content": render_template("elem_pages/contributor.html",
                                          elem=collective) }]

#########################
#  Blogs                #
#########################

@main.route('/blogs')
@partial_content
def blogs():
    return [ 'displayMain',
             { "content": render_template("main_pages/blogs.html",
                                          blog_posts = BlogPost.list(number=10) )} ]

@main.route('/blogs/<id>')
@partial_content
def blog(id):
    return [ 'displayMain',
             { "content": render_template("notimplemented.html") }]

#########################
#  Agendas              #
#########################

@main.route('/agendas')
@partial_content
def agendas():
    return [ 'displayMain',
             { "content": render_template("main_pages/agendas.html",
                                          events = Event.list(number=10)) } ]

@main.route('/agendas/<id>')
@partial_content
def agenda(id):
    return [ 'displayMain',
             { "content": render_template("notimplemented.html") }]

#########################
#  Static stuff         #
#########################

@main.route('/on_air', methods=['POST'])
def on_air():

    # Check we're authorized to do this
    # Security Nazi : a simple string comparison is probably not secure against
    # time attack, but that's good enough ;)
    # FIXME : use real token in prod
    #if request.args.get('token') != LIQUIDSOAP_TOKEN:
    print(request.form["token"])
    if request.form['token'] != 'lol':
        return ('INVALIDTOKEN', 401) # Unauthorized

    stream_url = request.args.get('stream')
    return Event.start_live(stream_url)


@main.route('/next_live')
def next_live():

    live, next_live_in = Event.closest_live()

    # FIXME: use Airtime API response to on_air_light (see )
    on_air_light = json.loads(
        "http://airtime.radiorhino.eu/api/on-air-light/format/json/api-key/"
        + AIRTIME_API_KEY)
    print(on_air_light)
    return jsonify({ "next_live_in": next_live_in,
                     "on_air_light": on_air_light["on_air_light"]})


