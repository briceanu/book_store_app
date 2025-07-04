from abc import ABC,abstractmethod



class AbstractUserInterface(ABC):

    @abstractmethod
    def sign_up(self):
        pass


    @abstractmethod
    def sign_in(self):
        pass

    @abstractmethod
    def logout(self):
        pass


    @abstractmethod
    def create_access_token_from_refresh(self):
        pass

    @abstractmethod
    def update_user_author_password(self):
        pass

    @abstractmethod
    def deactivate_account(self):
        pass

    @abstractmethod
    def reactivate_account(self):
        pass

    @abstractmethod
    def update_user_author_email(self):
        pass

    @abstractmethod
    def update_user_author_name(self):
        pass

    @abstractmethod
    def upload_user_author_image(self):
        pass