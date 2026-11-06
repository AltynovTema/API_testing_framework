from custom_requester.custom_requester import CustomRequester
from config.base_urls import AUTH_BASE_URL

USER = "/user"

class UserApi(CustomRequester):
    def __init__(self, session):
        super().__init__(session=session, base_url=AUTH_BASE_URL)

    def get_user_info(self, user_id, expected_status=200, **kwargs):
        return self.send_request(
            method="GET",
            endpoint=f"{USER}/{user_id}",
            expected_status=expected_status,
            **kwargs
        )

    def delete_user(self, user_id, expected_status=200, **kwargs):
        return self.send_request(
            method="DELETE",
            endpoint=f"{USER}/{user_id}",
            expected_status=expected_status,
            **kwargs
        )

    # def delete_set_of_all_users(self, *several_users_ids, expected_status=200, **kwargs):
    #     for user_id in several_users_ids:
    #         self.delete_user(user_id, expected_status, **kwargs)
