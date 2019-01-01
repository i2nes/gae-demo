import logging
from flask import Flask, jsonify, request
from google.appengine.ext import ndb
from datetime import datetime
from werkzeug.http import HTTP_STATUS_CODES


class Movie(ndb.Model):

    title = ndb.StringProperty()
    year = ndb.IntegerProperty()
    modified = ndb.DateTimeProperty(auto_now=True)

    def to_dict(self):
        d = {
            'id': self.key.id(),
            'title': self.title,
            'year': self.year,
            'modified': self.modified.isoformat(' ')
        }
        return d


def handle_http_error(e):

    response = {
        'meta': {
            'http_code': e.code,
            'message': HTTP_STATUS_CODES.get(e.code),
        },
    }
    
    return jsonify(response), e.code


app = Flask(__name__)
app.register_error_handler(404, handle_http_error)


@app.route('/movie/list', methods=['GET'])
def get_movies():
    """
    curl -X GET http://localhost:8080/movie/list
    """

    try:
        offset = int(request.args.get('offset'))
    except:
        offset = 0

    try:
        limit = int(request.args.get('limit'))
    except:
        limit = None

    movie_keys = Movie().query().fetch(keys_only=True, limit=limit, offset=offset)
    movie_list = [movie_key.get().to_dict() for movie_key in movie_keys]
    
    response = {
        'content': movie_list,
        'meta': {
            'count': len(movie_list),
            'total': len(Movie().query().fetch(keys_only=True)),
            'http_code': 200,
            'message': HTTP_STATUS_CODES.get(200),
        },
    }

    return jsonify(response), 200


@app.route('/movie/add', methods=['POST'])
def add_movie():
    """
    curl -X POST http://localhost:8080/movie/add \
    -H 'content-type: application/json' \
    -d '{
      "title": "The Equalizer 2",
      "year": 2018
    }'
    """

    request_body = request.get_json()

    if 'title' in request_body and 'year' in request_body:

        movie = Movie()

        try:
            movie.title = str(request_body['title'])
            movie.year = int(request_body['year'])
        except:
            logging.info('Error Adding Movie: {}'.format(request_body['title']))
            response = {
                'meta': {
                    'http_code': 500,
                    'message': HTTP_STATUS_CODES.get(500),
                },
            }
            return jsonify(response), 500

        movie.put()
        logging.info('Added Movie: {}'.format(movie.title))

        response = {
            'content': movie.to_dict(),
            'meta': {
                'http_code': 200,
                'message': HTTP_STATUS_CODES.get(200),
            },
        }

    return jsonify(response), 200


@app.route('/movie/delete/<id>', methods=['DELETE'])
def delete_movie(id):
    """
    curl -X DELETE http://localhost:8080/movie/delete/123
    """

    try:
        movie = Movie.get_by_id(int(id))
    except:
        movie = None

    if movie == None:
        response = {
            'meta': {
                'http_code': 404,
                'message': HTTP_STATUS_CODES.get(404),
            },
        }
        return jsonify(response), 404

    movie.key.delete()

    return jsonify(), 201

    