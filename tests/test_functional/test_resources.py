"""test_resources"""
import unittest
import pytest

from routes import *

class TestResourceGeneration(unittest.TestCase):
    def _assert_restful_routes(self, m, options, path_prefix=''):
        baseroute = '/' + path_prefix + options['controller']
        assert m.generate(action='index', **options) == baseroute
        assert m.generate(action='index', format='xml', **options) == baseroute + '.xml'
        assert m.generate(action='new', **options) == baseroute + '/new'
        assert m.generate(action='show', id='1', **options) == baseroute + '/1'
        assert m.generate(action='edit', id='1', **options) == baseroute + '/1/edit'
        assert m.generate(action='show', id='1', format='xml', **options) == baseroute + '/1.xml'

        assert m.generate(action='create', method='post', **options) == baseroute
        assert m.generate(action='update', method='put', id='1', **options) == baseroute + '/1'
        assert m.generate(action='delete', method='delete', id='1', **options) == baseroute + '/1'

    def test_resources(self):
        m = Mapper()
        m.resource('message', 'messages')
        m.resource('massage', 'massages')
        m.resource('passage', 'passages')
        m.create_regs(['messages'])
        options = dict(controller='messages')
        assert url_for('messages') == '/messages'
        assert url_for('formatted_messages', format='xml') == '/messages.xml'
        assert url_for('message', id=1) == '/messages/1'
        assert url_for('formatted_message', id=1, format='xml') == '/messages/1.xml'
        assert url_for('new_message') == '/messages/new'
        assert url_for('formatted_message', id=1, format='xml') == '/messages/1.xml'
        assert url_for('edit_message', id=1) == '/messages/1/edit'
        assert url_for('formatted_edit_message', id=1, format='xml') == '/messages/1/edit.xml'
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
        assert m.generate(controller='messages', action='rss') == '/messages/rss'
        assert url_for('rss_messages') == '/messages/rss'
        assert m.generate(controller='messages', action='rss', format='xml') == '/messages/rss.xml'
        assert url_for('formatted_rss_messages', format='xml') == '/messages/rss.xml'

    def test_resources_with_member_action(self):
        for method in ['put', 'post']:
            m = Mapper()
            m.resource('message', 'messages', member=dict(mark=method))
            m.create_regs(['messages'])
            options = dict(controller='messages')
            self._assert_restful_routes(m, options)
            assert m.generate(method=method, action='mark', id='1', **options) == '/messages/1/mark'
            assert m.generate(method=method, action='mark', id='1', format='xml', **options) == '/messages/1/mark.xml'

    def test_resources_with_new_action(self):
        m = Mapper()
        m.resource('message', 'messages/', new=dict(preview='POST'))
        m.create_regs(['messages'])
        options = dict(controller='messages')
        self._assert_restful_routes(m, options)
        assert m.generate(controller='messages', action='preview', method='post') == '/messages/new/preview'
        assert url_for('preview_new_message') == '/messages/new/preview'
        assert m.generate(controller='messages', action='preview', method='post', format='xml') == '/messages/new/preview.xml'
        assert url_for('formatted_preview_new_message', format='xml') == '/messages/new/preview.xml'

    def test_resources_with_name_prefix(self):
        m = Mapper()
        m.resource('message', 'messages', name_prefix='category_', new=dict(preview='POST'))
        m.create_regs(['messages'])
        options = dict(controller='messages')
        self._assert_restful_routes(m, options)
        assert url_for('category_preview_new_message') == '/messages/new/preview'
        with pytest.raises(Exception):
            url_for('category_preview_new_message', method='get')

    def test_resources_with_requirements(self):
        m = Mapper()
        m.resource('message', 'messages', path_prefix='/{project_id}/{user_id}/',
                   requirements={'project_id': r'[0-9a-f]{4}', 'user_id': r'\d+'})
        options = dict(controller='messages', project_id='cafe', user_id='123')
        self._assert_restful_routes(m, options, path_prefix='cafe/123/')

        # in addition to the positive tests we need to guarantee we
        # are not matching when the requirements don't match.
        assert m.match('/cafe/123/messages') == {'action': u'create', 'project_id': u'cafe', 'user_id': u'123', 'controller': u'messages'}
        assert m.match('/extensions/123/messages') is None
        assert m.match('/b0a3/123b/messages') is None
        assert m.match('/foo/bar/messages') is None


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
        assert con.mapper_dict == {'controller':'people', 'action':'index'}
        test_path('/people.xml', 'GET')
        assert con.mapper_dict == {'controller':'people', 'action':'index', 'format':'xml'}

        test_path('/people', 'POST')
        assert con.mapper_dict == {'controller':'people', 'action':'create'}
        test_path('/people.html', 'POST')
        assert con.mapper_dict == {'controller':'people', 'action':'create', 'format':'html'}

        test_path('/people/2.xml', 'GET')
        assert con.mapper_dict == {'controller':'people', 'action':'show', 'id':'2', 'format':'xml'}
        test_path('/people/2', 'GET')
        assert con.mapper_dict == {'controller':'people', 'action':'show', 'id':'2'}

        test_path('/people/2/edit', 'GET')
        assert con.mapper_dict == {'controller':'people', 'action':'edit', 'id':'2'}
        test_path('/people/2/edit.xml', 'GET')
        assert con.mapper_dict == {'controller':'people', 'action':'edit', 'id':'2', 'format':'xml'}

        test_path('/people/2', 'DELETE')
        assert con.mapper_dict == {'controller':'people', 'action':'delete', 'id':'2'}

        test_path('/people/2', 'PUT')
        assert con.mapper_dict == {'controller':'people', 'action':'update', 'id':'2'}
        test_path('/people/2.json', 'PUT')
        assert con.mapper_dict == {'controller':'people', 'action':'update', 'id':'2', 'format':'json'}

        # Test for dots in urls
        test_path('/people/2\.13', 'PUT')
        assert con.mapper_dict == {'controller':'people', 'action':'update', 'id':'2\.13'}
        test_path('/people/2\.13.xml', 'PUT')
        assert con.mapper_dict == {'controller':'people', 'action':'update', 'id':'2\.13', 'format':'xml'}
        test_path('/people/user\.name', 'PUT')
        assert con.mapper_dict == {'controller':'people', 'action':'update', 'id':'user\.name'}
        test_path('/people/user\.\.\.name', 'PUT')
        assert con.mapper_dict == {'controller':'people', 'action':'update', 'id':'user\.\.\.name'}
        test_path('/people/user\.name\.has\.dots', 'PUT')
        assert con.mapper_dict == {'controller':'people', 'action':'update', 'id':'user\.name\.has\.dots'}
        test_path('/people/user\.name\.is\.something.xml', 'PUT')
        assert con.mapper_dict == {'controller':'people', 'action':'update', 'id':'user\.name\.is\.something', 'format':'xml'}
        test_path('/people/user\.name\.ends\.with\.dot\..xml', 'PUT')
        assert con.mapper_dict == {'controller':'people', 'action':'update', 'id':'user\.name\.ends\.with\.dot\.', 'format':'xml'}
        test_path('/people/user\.name\.ends\.with\.dot\.', 'PUT')
        assert con.mapper_dict == {'controller':'people', 'action':'update', 'id':'user\.name\.ends\.with\.dot\.'}
        test_path('/people/\.user\.name\.starts\.with\.dot', 'PUT')
        assert con.mapper_dict == {'controller':'people', 'action':'update', 'id':'\.user\.name\.starts\.with\.dot'}
        test_path('/people/user\.name.json', 'PUT')
        assert con.mapper_dict == {'controller':'people', 'action':'update', 'id':'user\.name', 'format':'json'}

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
        assert con.mapper_dict == {'controller':'people', 'action':'index'}

        test_path('/people', 'POST')
        assert con.mapper_dict == {'controller':'people', 'action':'create'}

        test_path('/people/2', 'GET')
        assert con.mapper_dict == {'controller':'people', 'action':'show', 'id':'2'}
        test_path('/people/2/edit', 'GET')
        assert con.mapper_dict == {'controller':'people', 'action':'edit', 'id':'2'}

        test_path('/people/2', 'DELETE')
        assert con.mapper_dict == {'controller':'people', 'action':'delete', 'id':'2'}

        test_path('/people/2', 'PUT')
        assert con.mapper_dict == {'controller':'people', 'action':'update', 'id':'2'}

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
        assert con.mapper_dict == {'region_id': '13', 'controller': 'locations', 'action': 'index'}
        url = url_for('region_locations', region_id=13)
        assert url == '/regions/13/locations'

        test_path('/regions/13/locations', 'POST')
        assert con.mapper_dict == {'region_id': '13', 'controller': 'locations', 'action': 'create'}
        # new
        url = url_for('region_new_location', region_id=13)
        assert url == '/regions/13/locations/new'
        # create
        url = url_for('region_locations', region_id=13)
        assert url == '/regions/13/locations'

        test_path('/regions/13/locations/60', 'GET')
        assert con.mapper_dict == {'region_id': '13', 'controller': 'locations', 'id': '60', 'action': 'show'}
        url = url_for('region_location', region_id=13, id=60)
        assert url == '/regions/13/locations/60'

        test_path('/regions/13/locations/60/edit', 'GET')
        assert con.mapper_dict == {'region_id': '13', 'controller': 'locations', 'id': '60', 'action': 'edit'}
        url = url_for('region_edit_location', region_id=13, id=60)
        assert url == '/regions/13/locations/60/edit'

        test_path('/regions/13/locations/60', 'DELETE')
        assert con.mapper_dict == {'region_id': '13', 'controller': 'locations', 'id': '60', 'action': 'delete'}
        url = url_for('region_location', region_id=13, id=60)
        assert url == '/regions/13/locations/60'

        test_path('/regions/13/locations/60', 'PUT')
        assert con.mapper_dict == {'region_id': '13', 'controller': 'locations', 'id': '60', 'action': 'update'}
        url = url_for('region_location', region_id=13, id=60)
        assert url == '/regions/13/locations/60'

        # Make sure ``path_prefix`` overrides work
        # empty ``path_prefix`` (though I'm not sure why someone would do this)
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   path_prefix='')
        url = url_for('region_locations')
        assert url == '/locations'
        # different ``path_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   path_prefix='areas/:area_id')
        url = url_for('region_locations', area_id=51)
        assert url == '/areas/51/locations'

        # Make sure ``name_prefix`` overrides work
        # empty ``name_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   name_prefix='')
        url = url_for('locations', region_id=51)
        assert url == '/regions/51/locations'
        # different ``name_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   name_prefix='area_')
        url = url_for('area_locations', region_id=51)
        assert url == '/regions/51/locations'

        # Make sure ``path_prefix`` and ``name_prefix`` overrides work together
        # empty ``path_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   path_prefix='',
                   name_prefix='place_')
        url = url_for('place_locations')
        assert url == '/locations'
        # empty ``name_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   path_prefix='areas/:area_id',
                   name_prefix='')
        url = url_for('locations', area_id=51)
        assert url == '/areas/51/locations'
        # different ``path_prefix`` and ``name_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   path_prefix='areas/:area_id',
                   name_prefix='place_')
        url = url_for('place_locations', area_id=51)
        assert url == '/areas/51/locations'

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
        assert con.mapper_dict == {'region_id': '13', 'controller': 'locations', 'action': 'index'}
        url = url_for('region_locations', region_id=13)
        assert url == '/regions/13/locations'

        test_path('/regions/13/locations', 'POST')
        assert con.mapper_dict == {'region_id': '13', 'controller': 'locations', 'action': 'create'}
        # new
        url = url_for('region_new_location', region_id=13)
        assert url == '/regions/13/locations/new'
        # create
        url = url_for('region_locations', region_id=13)
        assert url == '/regions/13/locations'

        test_path('/regions/13/locations/60', 'GET')
        assert con.mapper_dict == {'region_id': '13', 'controller': 'locations', 'id': '60', 'action': 'show'}
        url = url_for('region_location', region_id=13, id=60)
        assert url == '/regions/13/locations/60'

        test_path('/regions/13/locations/60/edit', 'GET')
        assert con.mapper_dict == {'region_id': '13', 'controller': 'locations', 'id': '60', 'action': 'edit'}
        url = url_for('region_edit_location', region_id=13, id=60)
        assert url == '/regions/13/locations/60/edit'

        test_path('/regions/13/locations/60', 'DELETE')
        assert con.mapper_dict == {'region_id': '13', 'controller': 'locations', 'id': '60', 'action': 'delete'}
        url = url_for('region_location', region_id=13, id=60)
        assert url == '/regions/13/locations/60'

        test_path('/regions/13/locations/60', 'PUT')
        assert con.mapper_dict == {'region_id': '13', 'controller': 'locations', 'id': '60', 'action': 'update'}
        url = url_for('region_location', region_id=13, id=60)
        assert url == '/regions/13/locations/60'

        # Make sure ``path_prefix`` overrides work
        # empty ``path_prefix`` (though I'm not sure why someone would do this)
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   path_prefix='/')
        url = url_for('region_locations')
        assert url == '/locations'
        # different ``path_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   path_prefix='areas/:area_id')
        url = url_for('region_locations', area_id=51)
        assert url == '/areas/51/locations'

        # Make sure ``name_prefix`` overrides work
        # empty ``name_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   name_prefix='')
        url = url_for('locations', region_id=51)
        assert url == '/regions/51/locations'
        # different ``name_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   name_prefix='area_')
        url = url_for('area_locations', region_id=51)
        assert url == '/regions/51/locations'

        # Make sure ``path_prefix`` and ``name_prefix`` overrides work together
        # empty ``path_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   path_prefix='',
                   name_prefix='place_')
        url = url_for('place_locations')
        assert url == '/locations'
        # empty ``name_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   path_prefix='areas/:area_id',
                   name_prefix='')
        url = url_for('locations', area_id=51)
        assert url == '/areas/51/locations'
        # different ``path_prefix`` and ``name_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   path_prefix='areas/:area_id',
                   name_prefix='place_')
        url = url_for('place_locations', area_id=51)
        assert url == '/areas/51/locations'



if __name__ == '__main__':
    unittest.main()
