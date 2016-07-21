"""test_resources"""
import unittest
from nose.tools import eq_, assert_raises

from routes import *

class TestSubmapper(unittest.TestCase):
    def test_submapper(self):
        m = Mapper()
        c = m.submapper(path_prefix='/entries', requirements=dict(id='\d+'))
        c.connect('entry', '/{id}')

        eq_('/entries/1', url_for('entry', id=1))
        assert_raises(Exception, url_for, 'entry', id='foo')

    def test_submapper_with_no_path(self):
        m = Mapper()
        c = m.submapper(path_prefix='/')
        c.connect('entry')
        eq_('/entry?id=1', url_for('entry', id=1))

    def test_submapper_nesting(self):
        m = Mapper()
        c = m.submapper(path_prefix='/entries', controller='entry',
                        requirements=dict(id='\d+'))
        e = c.submapper(path_prefix='/{id}')

        eq_('entry', c.resource_name)
        eq_('entry', e.resource_name)

        e.connect('entry', '')
        e.connect('edit_entry', '/edit')

        eq_('/entries/1', url_for('entry', id=1))
        eq_('/entries/1/edit', url_for('edit_entry', id=1))
        assert_raises(Exception, url_for, 'entry', id='foo')

    def test_submapper_action(self):
        m = Mapper(explicit=True)
        c = m.submapper(path_prefix='/entries', controller='entry')

        c.action(name='entries', action='list')
        c.action(action='create', method='POST')

        eq_('/entries', url_for('entries', method='GET'))
        eq_('/entries', url_for('create_entry', method='POST'))
        eq_('/entries', url_for(controller='entry', action='list', method='GET'))
        eq_('/entries', url_for(controller='entry', action='create', method='POST'))
        assert_raises(Exception, url_for, 'entries', method='DELETE')

    def test_submapper_link(self):
        m = Mapper(explicit=True)
        c = m.submapper(path_prefix='/entries', controller='entry')

        c.link(rel='new')
        c.link(rel='ping', method='POST')

        eq_('/entries/new', url_for('new_entry', method='GET'))
        eq_('/entries/ping', url_for('ping_entry', method='POST'))
        eq_('/entries/new', url_for(controller='entry', action='new', method='GET'))
        eq_('/entries/ping', url_for(controller='entry', action='ping', method='POST'))
        assert_raises(Exception, url_for, 'new_entry', method='PUT')
        assert_raises(Exception, url_for, 'ping_entry', method='PUT')

    def test_submapper_standard_actions(self):
        m = Mapper()
        c = m.submapper(path_prefix='/entries', collection_name='entries',
                        controller='entry')
        e = c.submapper(path_prefix='/{id}')

        c.index()
        c.create()
        e.show()
        e.update()
        e.delete()

        eq_('/entries', url_for('entries', method='GET'))
        eq_('/entries', url_for('create_entry', method='POST'))
        assert_raises(Exception, url_for, 'entries', method='DELETE')

        eq_('/entries/1', url_for('entry', id=1, method='GET'))
        eq_('/entries/1', url_for('update_entry', id=1, method='PUT'))
        eq_('/entries/1', url_for('delete_entry', id=1, method='DELETE'))
        assert_raises(Exception, url_for, 'entry', id=1, method='POST')

    def test_submapper_standard_links(self):
        m = Mapper()
        c = m.submapper(path_prefix='/entries', controller='entry')
        e = c.submapper(path_prefix='/{id}')

        c.new()
        e.edit()

        eq_('/entries/new', url_for('new_entry', method='GET'))
        assert_raises(Exception, url_for, 'new_entry', method='POST')

        eq_('/entries/1/edit', url_for('edit_entry', id=1, method='GET'))
        assert_raises(Exception, url_for, 'edit_entry', id=1, method='POST')

    def test_submapper_action_and_link_generation(self):
        m = Mapper()
        c = m.submapper(path_prefix='/entries', controller='entry',
                        collection_name='entries',
                        actions=['index', 'new', 'create'])
        e = c.submapper(path_prefix='/{id}',
                       actions=['show', 'edit', 'update', 'delete'])

        eq_('/entries', url_for('entries', method='GET'))
        eq_('/entries', url_for('create_entry', method='POST'))
        assert_raises(Exception, url_for, 'entries', method='DELETE')

        eq_('/entries/1', url_for('entry', id=1, method='GET'))
        eq_('/entries/1', url_for('update_entry', id=1, method='PUT'))
        eq_('/entries/1', url_for('delete_entry', id=1, method='DELETE'))
        assert_raises(Exception, url_for, 'entry', id=1, method='POST')

        eq_('/entries/new', url_for('new_entry', method='GET'))
        assert_raises(Exception, url_for, 'new_entry', method='POST')

        eq_('/entries/1/edit', url_for('edit_entry', id=1, method='GET'))
        assert_raises(Exception, url_for, 'edit_entry', id=1, method='POST')

    def test_collection(self):
        m = Mapper()
        c = m.collection('entries', 'entry')

        eq_('/entries', url_for('entries', method='GET'))
        eq_('/entries', url_for('create_entry', method='POST'))
        assert_raises(Exception, url_for, 'entries', method='DELETE')

        eq_('/entries/1', url_for('entry', id=1, method='GET'))
        eq_('/entries/1', url_for('update_entry', id=1, method='PUT'))
        eq_('/entries/1', url_for('delete_entry', id=1, method='DELETE'))
        assert_raises(Exception, url_for, 'entry', id=1, method='POST')

        eq_('/entries/new', url_for('new_entry', method='GET'))
        assert_raises(Exception, url_for, 'new_entry', method='POST')

        eq_('/entries/1/edit', url_for('edit_entry', id=1, method='GET'))
        assert_raises(Exception, url_for, 'edit_entry', id=1, method='POST')

    def test_collection_options(self):
        m = Mapper()
        requirement=dict(id='\d+')
        c = m.collection('entries', 'entry', conditions=dict(sub_domain=True),
                         requirements=requirement)
        for r in m.matchlist:
            eq_(True, r.conditions['sub_domain'])
            eq_(requirement, r.reqs)

    def test_subsubmapper_with_controller(self):
        m = Mapper()
        col1 = m.collection('parents', 'parent',
                            controller='col1',
                            member_prefix='/{parent_id}')
        # NOTE: If one uses functions as controllers, the error will be here.
        col2 = col1.member.collection('children', 'child',
                                      controller='col2',
                                      member_prefix='/{child_id}')
        match = m.match('/parents/1/children/2')
        eq_('col2', match.get('controller'))

    def test_submapper_argument_overriding(self):
        m = Mapper()
        first = m.submapper(path_prefix='/first_level',
                            controller='first', action='test',
                            name_prefix='first_')
        first.connect('test', r'/test')
        second = first.submapper(path_prefix='/second_level',
                                 controller='second',
                                 name_prefix='second_')
        second.connect('test', r'/test')
        third = second.submapper(path_prefix='/third_level',
                                 controller="third", action='third_action',
                                 name_prefix='third_')
        third.connect('test', r'/test')

        # test first level
        match = m.match('/first_level/test')
        eq_('first', match.get('controller'))
        eq_('test', match.get('action'))
        # test name_prefix worked
        eq_('/first_level/test', url_for('first_test'))

        # test second level controller override
        match = m.match('/first_level/second_level/test')
        eq_('second', match.get('controller'))
        eq_('test', match.get('action'))
        # test name_prefix worked
        eq_('/first_level/second_level/test', url_for('first_second_test'))

        # test third level controller and action override
        match = m.match('/first_level/second_level/third_level/test')
        eq_('third', match.get('controller'))
        eq_('third_action', match.get('action'))
        # test name_prefix worked
        eq_('/first_level/second_level/third_level/test',
             url_for('first_second_third_test'))


if __name__ == '__main__':
    unittest.main()
