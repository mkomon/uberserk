# -*- coding: utf-8 -*-
from . import utils

# class model(type):


class Model():
    # __metaclass__ = model
    @classmethod
    def convert(cls, data):
        if isinstance(data, (list, tuple)):
            return [cls.convert_one(v) for v in data]
        return cls.convert_one(data)

    @classmethod
    def convert_one(cls, data):
        for k in set(data) & set(cls.conversions):
            data[k] = cls.conversions[k](data[k])
        return data

    @classmethod
    def convert_values(cls, data):
        for k in data:
            data[k] = cls.convert(data[k])
        return data


class Account(Model):
    createdAt = utils.datetime_from_millis
    seenAt = utils.datetime_from_millis
    conversions = {
        'createdAt': createdAt,
        'seenAt': seenAt,
    }


class User(Model):
    createdAt = utils.datetime_from_millis
    seenAt = utils.datetime_from_millis
    conversions = {
        'createdAt': createdAt,
        'seenAt': seenAt,
    }


class Activity(Model):
    interval = utils.inner(utils.datetime_from_seconds,
                           'start', 'end')
    conversions = {
        'interval': interval,
    }


class Game(Model):
    createdAt = utils.datetime_from_millis
    lastMoveAt = utils.datetime_from_millis
    conversions = {
        'createdAt': createdAt,
        'lastMoveAt': lastMoveAt,
    }


class GameState(Model):
    createdAt = utils.datetime_from_millis
    wtime = utils.datetime_from_millis
    btime = utils.datetime_from_millis
    winc = utils.datetime_from_millis
    binc = utils.datetime_from_millis
    conversions = {
        'createdAt': createdAt,
        'wtime': wtime,
        'btime': btime,
        'winc': winc,
        'binc': binc,
    }
 



class RatingHistory(Model):
    points = utils.listing(utils.rating_history)
