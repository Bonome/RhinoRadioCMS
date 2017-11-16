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
from .partial_content import partial_content_decorator
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
                            styles = getStyles(),
                            scripts = getScripts(),
                            podcasts = Podcast.list(),
                            blog_posts = BlogPost.list(),
                            events = Event.list(),
                            content = request.path
                          )

partial_content = partial_content_decorator(base)

@main.route('/')
@partial_content
def index():
    return [ 'displayMain',
           { "content": render_template("index.html",
                                        podcasts = Podcast.list(),
                                        blog_posts = BlogPost.list(),
                                        events = Event.list()) } ]


#########################
#  About                #
#########################

@main.route('/about')
@partial_content
def about():
    page = Page.query.filter_by(name='À propos').first_or_404()
    return [ 'displayMain',
           { "content": render_template("main_pages/about.html",
                                        page=page) } ]

@main.route('/blogs')
@partial_content
def blogs():
    return [ 'displayMain',
             { "content": render_template("main_pages/blogs.html",
                                          blog_posts = BlogPost.list(number=10) )} ]

@main.route('/agendas')
@partial_content
def agenda():
    return [ 'displayMain',
             { "content": render_template("main_pages/agendas.html",
                                          events = Event.list(number=10)) } ]

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

@main.route('/podcasts/', methods=['GET', 'POST'])
@partial_content
def podcasts():
    page = request.args.get('page', type=int)
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

    return [ "player.load.bind(player)",
             { "link" : podcast.link,
               "title" : podcast.name } ]


#########################
#  Contributors         #
#########################

@main.route('/contributors/')
@partial_content
def contributors():
    #collectives = Channel.query.filter(Channel.type=="collective").all()
    return [ 'displayMain',
             { "content": render_template("main_pages/contributors.html",
                                          contributors=Contributor.list())}]


@main.route('/contributor/<contrib>')
@partial_content
def contributor(contrib):
    #podcasts = Podcast.list(filter = contrib + "in Podcast.contributors")
    #podcasts = Podcast.query.filter_by(contributor_id = Contributor.query.filter_by(name = contrib).first()).all()
    return [ 'displayMain',
             { "content": render_template("notimplemented.html") }]


#########################
#  Collectives          #
#########################

@main.route('/collectives')
@partial_content
def collectives():
    """ Return list of all the collectives """
    return [ 'displayMain',
             { "content": render_template("notimplemented.html",
                                          collectives=Collectives.list()) }]

@main.route('/collective/<id>')
@partial_content
def collective(id):
    """ Return home template for collective coll """
    collective = Collective.query.filter(Collective.id==id).first()
    #podcasts = getPodcasts(filter='Podcast.channel_id==channel_id'),
    return [ 'displayMain',
             { "content": render_template("notimplemented.html",
                                          collective=collective) }]

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

    return jsonify({ "next_live_in": next_live_in })


#########################
#  Static stuff         #
#########################

def getStyles():
     return [ url_for('static',
                      filename=file.replace('app/static/', ''),
                      #_scheme='https',
                      _external=True)
             for file in glob("app/static/css/*.css") ]

def getScripts():
     return [ url_for('static',
                      filename=file.replace('app/static/', ''),
                      #_scheme='https',
                      _external=True)
             for file in glob("app/static/js/*.js") ]
