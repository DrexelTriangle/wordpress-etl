class GuestAuthor:

    def __init__(self, title, creator, link, pub_date, guid, description, content_encoded, excerpt_encoded, post_id, post_date, posted_date_gmt, post_modified, post_modified_gmt, comment_status, ping_status, post_name, status, post_parent, menu_order, post_type, post_password, is_sticky, category, postmeta):
        self.data = {
                "title": title,
                "creator": creator,
                "link": link,
                "pub_date": pub_date,
                "guid": guid,
                "description": description,
                "content_encoded": content_encoded,
                "excerpt_encoded": excerpt_encoded,
                "post_id": post_id,
                "post_date": post_date,
                "post_modified": post_modified,
                "post_modified_gmt": post_modified_gmt,
                "comment_status": comment_status,
                "ping_status": ping_status,
                "post_name": post_name,
                "status": status,
                "post_parent": post_parent,
                "menu_order": menu_order,
                "post_type": post_type,
                "post_password": post_password,
                "is_sticky": is_sticky,
                "category": category,
                "postmeta": postmeta,
        } 

    def __str__(self):
        result = ''
        result += f'Guest Author\n'
        result += f'\ttitle: {self.data["title"]}\n'
        return result
