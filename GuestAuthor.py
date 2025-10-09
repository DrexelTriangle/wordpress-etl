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
        result += f'\tcreator: {self.data["creator"]}\n'
        result += f'\tlink: {self.data["link"]}\n'
        result += f'\tpub_date: {self.data["pub_date"]}\n'
        result += f'\tguid: {self.data["guid"]}\n'
        result += f'\tdescription: {self.data["description"]}\n'
        result += f'\tcontent_encoded: {self.data["content_encoded"]}\n'
        result += f'\texcerpt_encoded: {self.data["excerpt_encoded"]}\n'
        result += f'\tpost_id: {self.data["post_id"]}\n'
        result += f'\tpost_date: {self.data["post_date"]}\n'
        result += f'\tpost_modified: {self.data["post_modified"]}\n'
        result += f'\tpost_modified_gmt: {self.data["post_modified_gmt"]}\n'
        result += f'\tcomment_status: {self.data["comment_status"]}\n'
        result += f'\tping_status: {self.data["ping_status"]}\n'
        result += f'\tpost_name: {self.data["post_name"]}\n'
        result += f'\tstatus: {self.data["status"]}\n'
        result += f'\tpost_parent: {self.data["post_parent"]}\n'
        result += f'\tmenu_order: {self.data["menu_order"]}\n'
        result += f'\tpost_type: {self.data["post_type"]}\n'
        result += f'\tpost_password: {self.data["post_password"]}\n'
        result += f'\tis_sticky: {self.data["is_sticky"]}\n'
        result += f'\tcategory: {self.data["category"]}\n'
        result += f'\tpostmeta: {self.data["postmeta"]}\n'
        return result
