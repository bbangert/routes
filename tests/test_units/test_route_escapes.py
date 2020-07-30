import unittest
from routes.route import Route


class TestRouteEscape(unittest.TestCase):
    def test_normal_route(self):
        r = Route('test', '/foo/bar')
        self.assertEqual(r.routelist, ['/foo/bar'])

    def test_route_with_backslash(self):
        r = Route('test', '/foo\\\\bar')
        self.assertEqual(r.routelist, ['/foo\\bar'])

    def test_route_with_random_escapes(self):
        r = Route('test', '\\/f\\oo\\/ba\\r')
        self.assertEqual(r.routelist, ['\\/f\\oo\\/ba\\r'])

    def test_route_with_colon(self):
        r = Route('test', '/foo:bar/baz')
        self.assertEqual(
            r.routelist, ['/foo', {'name': 'bar', 'type': ':'}, '/', 'baz'])

    def test_route_with_escaped_colon(self):
        r = Route('test', '/foo\\:bar/baz')
        self.assertEqual(r.routelist, ['/foo:bar/baz'])

    def test_route_with_both_colons(self):
        r = Route('test', '/prefix/escaped\\:escaped/foo=:notescaped/bar=42')
        self.assertEqual(
            r.routelist, ['/prefix/escaped:escaped/foo=',
                          {'name': 'notescaped', 'type': ':'}, '/', 'bar=42'])

    def test_route_with_all_escapes(self):
        r = Route('test', '/hmm\\:\\*\\{\\}*star/{brackets}/:colon')
        self.assertEqual(
            r.routelist, ['/hmm:*{}', {'name': 'star', 'type': '*'}, '/',
                          {'name': 'brackets', 'type': ':'}, '/',
                          {'name': 'colon', 'type': ':'}])
