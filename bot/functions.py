import logging
from datetime import datetime


class TableClass:
    def __init__(self, connector):
        self.conn = connector
        self.cursor = self.conn.cursor()


class User(TableClass):
    def create_user(self, chat_id, username):
        try:
            current_username = self.check_username(chat_id)
            if current_username:
                if username != current_username[0]:
                    self.cursor.execute("""
                    UPDATE app_user SET username = %s WHERE chat_id = %s;
                    """, (username, chat_id))
                    logging.info(f"User edited with ID: {chat_id}")
            else:
                self.cursor.execute("""
                INSERT INTO app_user (chat_id, username, is_staff)
                VALUES (%s, %s, %s);
                """, (chat_id, username, False))
                logging.info(f"User created with ID: {chat_id}")
                SearchCriteria(self.conn).create(chat_id)
            self.conn.commit()
            return chat_id

        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error occurred: {e}")

    def check_username(self, chat_id):
        self.cursor.execute("""
        SELECT username, is_staff FROM app_user WHERE chat_id = %s;
        """, (chat_id,))
        res = self.cursor.fetchall()
        if res:
            return res[0][0], res[0][1]
        else:
            return False

    def get_all_chat_id(self):
        self.cursor.execute("""
                SELECT chat_id FROM app_user;
                """)
        res = self.cursor.fetchall()
        if res:
            return res[0]
        else:
            return False

    def remove_user(self, chat_id):
        try:
            self.cursor.execute("""
                                DELETE FROM app_user                    
                                WHERE chat_id = %s;
                                """, (chat_id,))
            self.conn.commit()
            logging.info(f"User removed with ID: {chat_id}")

        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error occurred: {e}")



class Ad(TableClass):

    def create_ad(self, ad):
        try:
            self.cursor.execute("""
                INSERT INTO app_ad (name, start_date, end_date, price, description, location, phone, "user", is_approved, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, (ad['name'],
                      ad['start_date'],
                      ad['end_date'],
                      ad['price'],
                      ad['description'],
                      ad['location'],
                      ad['phone'],
                      ad['user'],
                      False,
                      datetime.now()))
            self.conn.commit()
            self.cursor.execute("""
                SELECT id FROM app_ad 
                WHERE name = %s AND "user" = %s
                ORDER BY created_at DESC
                LIMIT 1;
                """, (ad['name'], ad['user']))
            res = self.cursor.fetchall()
            ad_id = res[0][0]
            logging.info(f"Ad created with ID: {ad_id}")
            return ad_id
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error occurred: {e}")

    def show_ads(self, min_price=0, max_price=99999.99, is_approved=(True, ), keywords=(), user='%%'):
        try:
            base_query = """SELECT id, name, description, price, location, start_date, end_date, phone, is_approved, "user"
             FROM app_ad aa WHERE """
            query_for_name =  """ OR """.join([""" aa."name" ILIKE %s""" for _ in keywords]) if keywords else ''
            query_for_description = """ OR """ + """ OR """.join(""" aa.description ILIKE %s""" for _ in keywords) + """ AND """ if keywords else ''
            query_for_price = """aa.price BETWEEN %s AND %s"""
            query_for_approved = """aa.is_approved IN %s"""
            query_for_user = """aa."user" ILIKE %s"""
            params = [f"%{keyword}%" for keyword in keywords]*2
            params += [min_price, max_price, is_approved, user]
            query = base_query + query_for_name + query_for_description + query_for_price + " AND " + query_for_approved + " AND " + query_for_user
            self.cursor.execute(query, params)
            res = self.cursor.fetchall()
            return res

        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error occurred: {e}")

    def change_ad_status(self, ad_id, status):
        try:
            self.cursor.execute("""
                    UPDATE app_ad
                    SET is_approved = %s
                    WHERE id = %s;
                    """, (status, ad_id))
            self.conn.commit()
            logging.info(f"Ad status updated with ID: {ad_id}")
            return ad_id
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error occurred: {e}")

    def remove_ad(self, ad_id):
        try:
            self.cursor.execute("""
                    DELETE FROM app_ad                    
                    WHERE id = %s;
                    """, (ad_id, ))
            self.conn.commit()
            logging.info(f"Ad removed with ID: {ad_id}")
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error occurred: {e}")


    def get_ad_by_id(self, ad_id):
        try:
            self.cursor.execute("""
                            SELECT id, name, description, price, location, start_date, end_date, phone
                            FROM app_ad 
                            WHERE id = %s;
                            """, (ad_id, ))
            res = self.cursor.fetchall()[0]
            ad = {'ad_id': res[0],
                  'name': res[1],
                  'description': res[2],
                  'price': res[3],
                  'location': res[4],
                  'start_date': res[5],
                  'end_date': res[6],
                  'phone': res[7]}
            return ad

        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error occurred: {e}")


    def edit_ad(self, ad):
        try:
            self.cursor.execute("""
                UPDATE app_ad 
                SET name = %s,
                start_date = %s,
                end_date = %s,
                price = %s,
                description = %s,
                location = %s,
                phone = %s,                
                is_approved = %s                
                WHERE id = %s;
                """, (ad['name'],
                      ad['start_date'],
                      ad['end_date'],
                      ad['price'],
                      ad['description'],
                      ad['location'],
                      ad['phone'],
                      False,
                      ad['ad_id']))
            self.conn.commit()
            logging.info(f"Ad updated with ID: {ad['ad_id']}")
            return ad['ad_id']
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error occurred: {e}")


class SearchCriteria(TableClass):
    def create(self, chat_id, min_price=0, max_price=99999.99, keywords="{}"):
        try:
            self.cursor.execute("""INSERT INTO app_searchcriteria (min_price, max_price, keywords, chat_id)
            VALUES (%s, %s, %s, %s);
                    """, (min_price, max_price, keywords, chat_id))
            self.conn.commit()
            logging.info(f"Search criteria created with chat ID: {chat_id}")
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error occurred: {e}")

    def update(self, chat_id, min_price=0, max_price=99999.99, keywords="{}"):
        try:
            self.cursor.execute("""
                    UPDATE app_searchcriteria
                    SET min_price = %s, max_price = %s, keywords = %s
                    WHERE chat_id = %s;
                    """, (min_price, max_price, keywords, chat_id))
            self.conn.commit()
            logging.info(f"Search criteria updated with chat ID: {chat_id}")
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error occurred: {e}")

    def get(self, chat_id):
        try:
            self.cursor.execute("""
                            SELECT min_price, max_price, keywords FROM app_searchcriteria WHERE chat_id = %s;
                            """, (chat_id, ))
            res = self.cursor.fetchall()
            criteria = {'min_price': res[0][0],
                        'max_price': res[0][1],
                        'keywords': res[0][2]
                        }
            return criteria

        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error occurred: {e}")

    def remove(self, chat_id):
        try:
            self.cursor.execute("""
                                DELETE FROM app_searchcriteria                  
                                WHERE chat_id = %s;
                                """, (chat_id,))
            self.conn.commit()
            logging.info(f"SearchCriteria removed with ID: {chat_id}")

        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error occurred: {e}")


class AdComments(TableClass):
    def create(self, comment):
        try:
            self.cursor.execute("""
                INSERT INTO app_adcomments (ad_id, comment, is_approved, "user", created_at)
                VALUES (%s, %s, %s, %s, %s);
                """, (comment['ad_id'],
                      comment['comment'],
                      False,
                      comment['user'],
                      datetime.now()))
            self.conn.commit()
            self.cursor.execute("""
                SELECT max(id) FROM app_adcomments
                WHERE ad_id = %s AND "user" = %s 
                GROUP BY ad_id, "user";
                """, (comment['ad_id'], comment['user']))
            res = self.cursor.fetchall()
            comment_id = res[0][0]
            logging.info(f"Comment created with ID: {comment_id}")
            return comment_id
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error occurred: {e}")

    def show_comments(self, ad_ids='', is_approved=True):
        try:
            if ad_ids == '':
                self.cursor.execute("""
                                    SELECT id, ad_id, comment, "user" FROM app_adcomments WHERE is_approved = %s;
                                    """, (is_approved, ))
                res = self.cursor.fetchall()
            else:
                self.cursor.execute("""
                                SELECT ad_id, comment, "user" FROM app_adcomments WHERE ad_id IN %s AND is_approved = %s;
                                """, (ad_ids, is_approved))
                res = self.cursor.fetchall()
            return res

        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error occurred: {e}")

    def approve_comment(self, comment_id):
        try:
            self.cursor.execute("""
                    UPDATE app_adcomments
                    SET is_approved = True
                    WHERE id = %s;
                    """, (comment_id, ))
            logging.info(f"Comment approved for ad ID: {comment_id}")
            self.conn.commit()
            self.cursor.execute("""
            SELECT au.chat_id, aa."name" 
            FROM app_user au 
            LEFT JOIN app_ad aa ON au.username = aa."user" 
            LEFT JOIN app_adcomments aa2 on aa.id = aa2.ad_id
            WHERE aa2.id = %s;""", (comment_id, ))
            res = self.cursor.fetchall()[0]
            return res
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error occurred: {e}")

    def remove(self, comment_id):
        try:
            self.cursor.execute("""
                                DELETE FROM app_adcomments                 
                                WHERE id = %s;
                                """, (comment_id,))
            self.conn.commit()
            logging.info(f"AdComment removed with ID: {comment_id}")

        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error occurred: {e}")

