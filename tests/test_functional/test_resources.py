"""test_resources"""
import unittest
from nose.tools import eq_, assert_raises

from routes import *

class TestResourceGeneration(unittest.TestCase):
    def _assert_restful_routes(self, m, options, path_prefix=''):
        baseroute = '/' + path_prefix + options['controller']
        eq_(baseroute, m.generate(action='index', **options))
        eq_(baseroute + '.xml', m.generate(action='index', format='xml', **options))
        eq_(baseroute + '/new', m.generate(action='new', **options))
        eq_(baseroute + '/1', m.generate(action='show', id='1', **options))
        eq_(baseroute + '/1/edit', m.generate(action='edit',id='1', **options))
        eq_(baseroute + '/1.xml', m.generate(action='show', id='1',format='xml', **options))

        eq_(baseroute, m.generate(action='create', method='post', **options))
        eq_(baseroute + '/1', m.generate(action='update', method='put', id='1', **options))
        eq_(baseroute + '/1', m.generate(action='delete', method='delete', id='1', **options))

    def test_resources(self):
        m = Mapper()
        m.resource('message', 'messages')
        m.resource('massage', 'massages')
        m.resource('passage', 'passages')
        m.create_regs(['messages'])
        options = dict(controller='messages')
        eq_('/messages', url_for('messages'))
        eq_('/messages.xml', url_for('formatted_messages', format='xml'))
        eq_('/messages/1', url_for('message', id=1))
        eq_('/messages/1.xml', url_for('formatted_message', id=1, format='xml'))
        eq_('/messages/new', url_for('new_message'))
        eq_('/messages/1.xml', url_for('formatted_message', id=1, format='xml'))
        eq_('/messages/1/edit', url_for('edit_message', id=1))
        eq_('/messages/1/edit.xml', url_for('formatted_edit_message', id=1, format='xml'))
        self._assert_restful_routes(m, options)

    def test_resources_with_path_prefix(self):
        m = Mapper()
        m.resource('message', 'messages', path_prefix='/thread/:threadid')
        m.create_regs(['messages'])
        options = dict(controller='messages', threadid='5')
        self._assert_restful_routes(m, options, path_prefix='thread/5/')

    def test_resources_with_collection_action(self):
        m = Mapper()
        m.resource('message', 'messages', collection=dict(rss='GET'))
        m.create_regs(['messages'])
        options = dict(controller='messages')
        self._assert_restful_routes(m, options)
        eq_('/messages/rss', m.generate(controller='messages', action='rss'))
        eq_('/messages/rss', url_for('rss_messages'))
        eq_('/messages/rss.xml', m.generate(controller='messages', action='rss', format='xml'))
        eq_('/messages/rss.xml', url_for('formatted_rss_messages', format='xml'))

    def test_resources_with_member_action(self):
        for method in ['put', 'post']:
            m = Mapper()
            m.resource('message', 'messages', member=dict(mark=method))
            m.create_regs(['messages'])
            options = dict(controller='messages')
            self._assert_restful_routes(m, options)
            eq_('/messages/1/mark', m.generate(method=method, action='mark', id='1', **options))
            eq_('/messages/1/mark.xml',
                m.generate(method=method, action='mark', id='1', format='xml', **options))

    def test_resources_with_new_action(self):
        m = Mapper()
        m.resource('message', 'messages/', new=dict(preview='POST'))
        m.create_regs(['messages'])
        options = dict(controller='messages')
        self._assert_restful_routes(m, options)
        eq_('/messages/new/preview', m.generate(controller='messages', action='preview', method='post'))
        eq_('/messages/new/preview', url_for('preview_new_message'))
        eq_('/messages/new/preview.xml',
            m.generate(controller='messages', action='preview', method='post', format='xml'))
        eq_('/messages/new/preview.xml', url_for('formatted_preview_new_message', format='xml'))

    def test_resources_with_name_prefix(self):
        m = Mapper()
        m.resource('message', 'messages', name_prefix='category_', new=dict(preview='POST'))
        m.create_regs(['messages'])
        options = dict(controller='messages')
        self._assert_restful_routes(m, options)
        eq_('/messages/new/preview', url_for('category_preview_new_message'))
        assert_raises(Exception, url_for, 'category_preview_new_message', method='get')

    def test_resources_with_requirements(self):
        m = Mapper()
        m.resource('message', 'messages', path_prefix='/{project_id}/{user_id}/',
                   requirements={'project_id': r'[0-9a-f]{4}', 'user_id': r'\d+'})
        options = dict(controller='messages', project_id='cafe', user_id='123')
        self._assert_restful_routes(m, options, path_prefix='cafe/123/')

        # in addition to the positive tests we need to guarantee we
        # are not matching when the requirements don't match.
        eq_({'action': u'create', 'project_id': u'cafe', 'user_id': u'123', 'controller': u'messages'},
            m.match('/cafe/123/messages'))
        eq_(None, m.match('/extensions/123/messages'))
        eq_(None, m.match('/b0a3/123b/messages'))
        eq_(None, m.match('/foo/bar/messages'))


class TestResourceRecognition(unittest.TestCase):
    def test_resource(self):
        m = Mapper()
        m.resource('person', 'people')
        m.create_regs(['people'])

        con = request_config()
        con.mapper = m
        def test_path(path, method):
            env = dict(HTTP_HOST='example.com', PATH_INFO=path, REQUEST_METHOD=method)
            con.mapper_dict = {}
            con.environ = env

        test_path('/people', 'GET')
        eq_({'controller':'people', 'action':'index'}, con.mapper_dict)
        test_path('/people.xml', 'GET')
        eq_({'controller':'people', 'action':'index', 'format':'xml'}, con.mapper_dict)

        test_path('/people', 'POST')
        eq_({'controller':'people', 'action':'create'}, con.mapper_dict)
        test_path('/people.html', 'POST')
        eq_({'controller':'people', 'action':'create', 'format':'html'}, con.mapper_dict)

        test_path('/people/2.xml', 'GET')
        eq_({'controller':'people', 'action':'show', 'id':'2', 'format':'xml'}, con.mapper_dict)
        test_path('/people/2', 'GET')
        eq_({'controller':'people', 'action':'show', 'id':'2'}, con.mapper_dict)

        test_path('/people/2/edit', 'GET')
        eq_({'controller':'people', 'action':'edit', 'id':'2'}, con.mapper_dict)
        test_path('/people/2/edit.xml', 'GET')
        eq_({'controller':'people', 'action':'edit', 'id':'2', 'format':'xml'}, con.mapper_dict)

        test_path('/people/2', 'DELETE')
        eq_({'controller':'people', 'action':'delete', 'id':'2'}, con.mapper_dict)

        test_path('/people/2', 'PUT')
        eq_({'controller':'people', 'action':'update', 'id':'2'}, con.mapper_dict        )
        test_path('/people/2.json', 'PUT')
        eq_({'controller':'people', 'action':'update', 'id':'2', 'format':'json'}, con.mapper_dict        )

        # Test for dots in urls
        test_path('/people/2\.13', 'PUT')
        eq_({'controller':'people', 'action':'update', 'id':'2\.13'}, con.mapper_dict)
        test_path('/people/2\.13.xml', 'PUT')
        eq_({'controller':'people', 'action':'update', 'id':'2\.13', 'format':'xml'}, con.mapper_dict)
        test_path('/people/user\.name', 'PUT')
        eq_({'controller':'people', 'action':'update', 'id':'user\.name'}, con.mapper_dict)
        test_path('/people/user\.\.\.name', 'PUT')
        eq_({'controller':'people', 'action':'update', 'id':'user\.\.\.name'}, con.mapper_dict)
        test_path('/people/user\.name\.has\.dots', 'PUT')
        eq_({'controller':'people', 'action':'update', 'id':'user\.name\.has\.dots'}, con.mapper_dict)
        test_path('/people/user\.name\.is\.something.xml', 'PUT')
        eq_({'controller':'people', 'action':'update', 'id':'user\.name\.is\.something', 'format':'xml'}, con.mapper_dict)
        test_path('/people/user\.name\.ends\.with\.dot\..xml', 'PUT')
        eq_({'controller':'people', 'action':'update', 'id':'user\.name\.ends\.with\.dot\.', 'format':'xml'}, con.mapper_dict)
        test_path('/people/user\.name\.ends\.with\.dot\.', 'PUT')
        eq_({'controller':'people', 'action':'update', 'id':'user\.name\.ends\.with\.dot\.'}, con.mapper_dict)
        test_path('/people/\.user\.name\.starts\.with\.dot', 'PUT')
        eq_({'controller':'people', 'action':'update', 'id':'\.user\.name\.starts\.with\.dot'}, con.mapper_dict)
        test_path('/people/user\.name.json', 'PUT')
        eq_({'controller':'people', 'action':'update', 'id':'user\.name', 'format':'json'}, con.mapper_dict)

    def test_resource_with_nomin(self):
        m = Mapper()
        m.minimization = False
        m.resource('person', 'people')
        m.create_regs(['people'])

        con = request_config()
        con.mapper = m
        def test_path(path, method):
            env = dict(HTTP_HOST='example.com', PATH_INFO=path, REQUEST_METHOD=method)
            con.mapper_dict = {}
            con.environ = env

        test_path('/people', 'GET')
        eq_({'controller':'people', 'action':'index'}, con.mapper_dict)

        test_path('/people', 'POST')
        eq_({'controller':'people', 'action':'create'}, con.mapper_dict)

        test_path('/people/2', 'GET')
        eq_({'controller':'people', 'action':'show', 'id':'2'}, con.mapper_dict)
        test_path('/people/2/edit', 'GET')
        eq_({'controller':'people', 'action':'edit', 'id':'2'}, con.mapper_dict)

        test_path('/people/2', 'DELETE')
        eq_({'controller':'people', 'action':'delete', 'id':'2'}, con.mapper_dict)

        test_path('/people/2', 'PUT')
        eq_({'controller':'people', 'action':'update', 'id':'2'}, con.mapper_dict)

    def test_resource_created_with_parent_resource(self):
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'))
        m.create_regs(['locations'])

        con = request_config()
        con.mapper = m
        def test_path(path, method):
            env = dict(HTTP_HOST='example.com', PATH_INFO=path,
                       REQUEST_METHOD=method)
            con.mapper_dict = {}
            con.environ = env

        test_path('/regions/13/locations', 'GET')
        eq_(con.mapper_dict, {'region_id': '13', 'controller': 'locations',
                                   'action': 'index'})
        url = url_for('region_locations', region_id=13)
        eq_(url, '/regions/13/locations')

        test_path('/regions/13/locations', 'POST')
        eq_(con.mapper_dict, {'region_id': '13', 'controller': 'locations',
                                   'action': 'create'})
        # new
        url = url_for('region_new_location', region_id=13)
        eq_(url, '/regions/13/locations/new')
        # create
        url = url_for('region_locations', region_id=13)
        eq_(url, '/regions/13/locations')

        test_path('/regions/13/locations/60', 'GET')
        eq_(con.mapper_dict, {'region_id': '13', 'controller': 'locations',
                                   'id': '60', 'action': 'show'})
        url = url_for('region_location', region_id=13, id=60)
        eq_(url, '/regions/13/locations/60')

        test_path('/regions/13/locations/60/edit', 'GET')
        eq_(con.mapper_dict, {'region_id': '13', 'controller': 'locations',
                                   'id': '60', 'action': 'edit'})
        url = url_for('region_edit_location', region_id=13, id=60)
        eq_(url, '/regions/13/locations/60/edit')

        test_path('/regions/13/locations/60', 'DELETE')
        eq_(con.mapper_dict, {'region_id': '13', 'controller': 'locations',
                                   'id': '60', 'action': 'delete'})
        url = url_for('region_location', region_id=13, id=60)
        eq_(url, '/regions/13/locations/60')

        test_path('/regions/13/locations/60', 'PUT')
        eq_(con.mapper_dict, {'region_id': '13', 'controller': 'locations',
                                   'id': '60', 'action': 'update'})
        url = url_for('region_location', region_id=13, id=60)
        eq_(url, '/regions/13/locations/60')

        # Make sure ``path_prefix`` overrides work
        # empty ``path_prefix`` (though I'm not sure why someone would do this)
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   path_prefix='')
        url = url_for('region_locations')
        eq_(url, '/locations')
        # different ``path_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   path_prefix='areas/:area_id')
        url = url_for('region_locations', area_id=51)
        eq_(url, '/areas/51/locations')

        # Make sure ``name_prefix`` overrides work
        # empty ``name_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   name_prefix='')
        url = url_for('locations', region_id=51)
        eq_(url, '/regions/51/locations')
        # different ``name_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   name_prefix='area_')
        url = url_for('area_locations', region_id=51)
        eq_(url, '/regions/51/locations')

        # Make sure ``path_prefix`` and ``name_prefix`` overrides work together
        # empty ``path_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   path_prefix='',
                   name_prefix='place_')
        url = url_for('place_locations')
        eq_(url, '/locations')
        # empty ``name_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   path_prefix='areas/:area_id',
                   name_prefix='')
        url = url_for('locations', area_id=51)
        eq_(url, '/areas/51/locations')
        # different ``path_prefix`` and ``name_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   path_prefix='areas/:area_id',
                   name_prefix='place_')
        url = url_for('place_locations', area_id=51)
        eq_(url, '/areas/51/locations')

    def test_resource_created_with_parent_resource_nomin(self):
        m = Mapper()
        m.minimization = False
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'))
        m.create_regs(['locations'])

        con = request_config()
        con.mapper = m
        def test_path(path, method):
            env = dict(HTTP_HOST='example.com', PATH_INFO=path,
                       REQUEST_METHOD=method)
            con.mapper_dict = {}
            con.environ = env

        test_path('/regions/13/locations', 'GET')
        eq_(con.mapper_dict, {'region_id': '13', 'controller': 'locations',
                                   'action': 'index'})
        url = url_for('region_locations', region_id=13)
        eq_(url, '/regions/13/locations')

        test_path('/regions/13/locations', 'POST')
        eq_(con.mapper_dict, {'region_id': '13', 'controller': 'locations',
                                   'action': 'create'})
        # new
        url = url_for('region_new_location', region_id=13)
        eq_(url, '/regions/13/locations/new')
        # create
        url = url_for('region_locations', region_id=13)
        eq_(url, '/regions/13/locations')

        test_path('/regions/13/locations/60', 'GET')
        eq_(con.mapper_dict, {'region_id': '13', 'controller': 'locations',
                                   'id': '60', 'action': 'show'})
        url = url_for('region_location', region_id=13, id=60)
        eq_(url, '/regions/13/locations/60')

        test_path('/regions/13/locations/60/edit', 'GET')
        eq_(con.mapper_dict, {'region_id': '13', 'controller': 'locations',
                                   'id': '60', 'action': 'edit'})
        url = url_for('region_edit_location', region_id=13, id=60)
        eq_(url, '/regions/13/locations/60/edit')

        test_path('/regions/13/locations/60', 'DELETE')
        eq_(con.mapper_dict, {'region_id': '13', 'controller': 'locations',
                                   'id': '60', 'action': 'delete'})
        url = url_for('region_location', region_id=13, id=60)
        eq_(url, '/regions/13/locations/60')

        test_path('/regions/13/locations/60', 'PUT')
        eq_(con.mapper_dict, {'region_id': '13', 'controller': 'locations',
                                   'id': '60', 'action': 'update'})
        url = url_for('region_location', region_id=13, id=60)
        eq_(url, '/regions/13/locations/60')

        # Make sure ``path_prefix`` overrides work
        # empty ``path_prefix`` (though I'm not sure why someone would do this)
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   path_prefix='/')
        url = url_for('region_locations')
        eq_(url, '/locations')
        # different ``path_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   path_prefix='areas/:area_id')
        url = url_for('region_locations', area_id=51)
        eq_(url, '/areas/51/locations')

        # Make sure ``name_prefix`` overrides work
        # empty ``name_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   name_prefix='')
        url = url_for('locations', region_id=51)
        eq_(url, '/regions/51/locations')
        # different ``name_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   name_prefix='area_')
        url = url_for('area_locations', region_id=51)
        eq_(url, '/regions/51/locations')

        # Make sure ``path_prefix`` and ``name_prefix`` overrides work together
        # empty ``path_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   path_prefix='',
                   name_prefix='place_')
        url = url_for('place_locations')
        eq_(url, '/locations')
        # empty ``name_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   path_prefix='areas/:area_id',
                   name_prefix='')
        url = url_for('locations', area_id=51)
        eq_(url, '/areas/51/locations')
        # different ``path_prefix`` and ``name_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   path_prefix='areas/:area_id',
                   name_prefix='place_')
        url = url_for('place_locations', area_id=51)
        eq_(url, '/areas/51/locations')



if __name__ == '__main__':
    unittest.main()
