import unittest, os, psycopg2
from functions import Ad, User, SearchCriteria, AdComments
from dotenv import load_dotenv


load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('DATABASE_HOST'),
    database=os.getenv('DATABASE_DB'),
    user=os.getenv('DATABASE_USER'),
    password=os.getenv('DATABASE_PASSWORD'),
    port='5432'
)


class TestPostingAd(unittest.TestCase):
    def setUp(self):
        self.conn = conn
        self.user = User(conn).create_user(123456, 'Test_user')
        self.ad = {'name': 'Test name',
                   'start_date': '2024-01-01',
                   'end_date': '2024-02-01',
                   'price': 10.15,
                   'description': 'Test description',
                   'location': 'Test location',
                   'phone': '+7(123)456-78-90',
                   'user': 'Test_user'}

    def tearDown(self):
        SearchCriteria(self.conn).remove(self.user)
        User(self.conn).remove_user(self.user)

    def test_posting_valid_ad(self):
        ad_id = Ad(self.conn).create_ad(self.ad)
        ad = Ad(self.conn).get_ad_by_id(ad_id)
        self.assertEqual(ad['ad_id'], ad_id)
        self.assertEqual(ad['name'], self.ad['name'])
        Ad(self.conn).remove_ad(ad['ad_id'])


class TestEditingAd(unittest.TestCase):
    def setUp(self):
        self.conn = conn
        self.user = User(conn).create_user(123456, 'Test_user')
        self.ad = {'name': 'Test name',
                   'start_date': '2024-01-01',
                   'end_date': '2024-02-01',
                   'price': 10.15,
                   'description': 'Test description',
                   'location': 'Test location',
                   'phone': '+7(123)456-78-90',
                   'user': 'Test_user'}
        self.ad_id = Ad(self.conn).create_ad(self.ad)

    def tearDown(self):
        Ad(self.conn).remove_ad(self.ad_id)
        SearchCriteria(self.conn).remove(self.user)
        User(self.conn).remove_user(self.user)

    def test_editing_ad(self):
        new_data = {'name': 'New name',
                   'start_date': '2024-01-01',
                   'end_date': '2024-02-01',
                   'price': 10.15,
                   'description': 'Test description',
                   'location': 'Test location',
                   'phone': '+7(123)456-78-90',
                   'user': 'Test_user',
                   'ad_id': self.ad_id}
        ad_id = Ad(self.conn).edit_ad(new_data)
        ad = Ad(self.conn).get_ad_by_id(ad_id)
        self.assertEqual(ad['name'], 'New name')


class TestAdCriteria(unittest.TestCase):
    def setUp(self):
        self.conn = conn
        self.user = User(conn).create_user(123456, 'Test_user')

    def tearDown(self):
        SearchCriteria(self.conn).remove(self.user)
        User(self.conn).remove_user(self.user)

    def test_update_criteria(self):
        new_min_price = 5
        new_max_price = 15
        new_keywords = ["keyword_1", "keyword_2"]
        SearchCriteria(self.conn).update(self.user, min_price=new_min_price, max_price=new_max_price, keywords=new_keywords)
        criteria = SearchCriteria(self.conn).get(self.user)
        self.assertEqual(criteria['min_price'], new_min_price)
        self.assertEqual(criteria['max_price'], new_max_price)
        self.assertEqual(criteria['keywords'], new_keywords)


class TestSearchingAd(unittest.TestCase):
    def setUp(self):
        self.conn = conn
        self.user = User(conn).create_user(123456, 'Test_user')
        self.ad_1 = {'name': 'First',
                   'start_date': '2024-01-01',
                   'end_date': '2024-02-01',
                   'price': 10.15,
                   'description': 'Description1',
                   'location': 'Test location',
                   'phone': '+7(123)456-78-90',
                   'user': 'Test_user'}
        self.ad_2 = {'name': 'Second',
                     'start_date': '2024-01-01',
                     'end_date': '2024-02-01',
                     'price': 20.25,
                     'description': 'Description2',
                     'location': 'Test location',
                     'phone': '+7(123)456-78-90',
                     'user': 'Test_user'}
        self.ad_3 = {'name': 'Not approved',
                     'start_date': '2024-01-01',
                     'end_date': '2024-02-01',
                     'price': 20.25,
                     'description': 'Description2',
                     'location': 'Test location',
                     'phone': '+7(123)456-78-90',
                     'user': 'Test_user'}
        self.ad_1_id = Ad(self.conn).create_ad(self.ad_1)
        self.ad_2_id = Ad(self.conn).create_ad(self.ad_2)
        self.ad_3_id = Ad(self.conn).create_ad(self.ad_3)
        Ad(self.conn).change_ad_status(self.ad_1_id, True)
        Ad(self.conn).change_ad_status(self.ad_2_id, True)

    def tearDown(self):
        Ad(self.conn).remove_ad(self.ad_1_id)
        Ad(self.conn).remove_ad(self.ad_2_id)
        Ad(self.conn).remove_ad(self.ad_3_id)
        SearchCriteria(self.conn).remove(self.user)
        User(self.conn).remove_user(self.user)

    def test_searching_approved_ads(self):
        criteria = SearchCriteria(self.conn).get(self.user)
        ads = Ad(self.conn).show_ads(min_price=criteria['min_price'], max_price=criteria['max_price'], keywords=tuple(criteria['keywords']))
        ids = [ad[0] for ad in ads]
        self.assertTrue(self.ad_1_id in ids)
        self.assertTrue(self.ad_2_id in ids)
        self.assertFalse(self.ad_3_id in ids)

    def test_searching_by_price(self):
        new_min_price = 5
        new_max_price = 15
        criteria = SearchCriteria(self.conn).get(self.user)
        SearchCriteria(self.conn).update(self.user, min_price=new_min_price, max_price=new_max_price, keywords=criteria['keywords'])
        criteria = SearchCriteria(self.conn).get(self.user)
        ads = Ad(self.conn).show_ads(min_price=criteria['min_price'], max_price=criteria['max_price'], keywords=tuple(criteria['keywords']))
        ids = [ad[0] for ad in ads]
        self.assertTrue(self.ad_1_id in ids)
        self.assertFalse(self.ad_2_id in ids)
        self.assertFalse(self.ad_3_id in ids)


    def test_searching_by_keywords(self):
        new_min_price = 0
        new_max_price = 99999.99
        new_keywords = ["Description1", "Second"]
        SearchCriteria(self.conn).update(self.user, min_price=new_min_price, max_price=new_max_price, keywords=new_keywords)
        criteria = SearchCriteria(self.conn).get(self.user)
        ads = Ad(self.conn).show_ads(min_price=criteria['min_price'], max_price=criteria['max_price'], keywords=tuple(criteria['keywords']))
        ids = [ad[0] for ad in ads]
        self.assertTrue(self.ad_1_id in ids)
        self.assertTrue(self.ad_2_id in ids)
        self.assertFalse(self.ad_3_id in ids)


class TestAdComment(unittest.TestCase):
    def setUp(self):
        self.conn = conn
        self.user = User(conn).create_user(123456, 'Test_user')
        self.ad = {'name': 'Test name',
                   'start_date': '2024-01-01',
                   'end_date': '2024-02-01',
                   'price': 10.15,
                   'description': 'Test description',
                   'location': 'Test location',
                   'phone': '+7(123)456-78-90',
                   'user': 'Test_user'}
        self.ad_id = Ad(self.conn).create_ad(self.ad)

    def tearDown(self):
        Ad(self.conn).remove_ad(self.ad_id)
        SearchCriteria(self.conn).remove(self.user)
        User(self.conn).remove_user(self.user)
        Ad(self.conn).change_ad_status(self.ad_id, True)

    def test_add_comment(self):
        comment = {'ad_id': self.ad_id,
                   'comment': 'Test comment',
                   'user': 'Test_user'}
        comment_id = AdComments(self.conn).create(comment)
        AdComments(self.conn).approve_comment(comment_id)
        searched_comment = AdComments(self.conn).show_comments(ad_ids=(self.ad_id, ))[0]
        self.assertEqual(searched_comment[1], comment['comment'])
        AdComments(self.conn).remove(comment_id)


if __name__ == '__main__':
    unittest.main()