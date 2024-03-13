import gradio as gr
from ktem.app import BaseApp
from ktem.pages.admin import AdminPage
from ktem.pages.chat import ChatPage
from ktem.pages.help import HelpPage
from ktem.pages.settings import SettingsPage


class App(BaseApp):
    """The main app of Kotaemon

    The main application contains app-level information:
        - setting state
        - user id

    App life-cycle:
        - Render
        - Declare public events
        - Subscribe public events
        - Register events
    """

    def ui(self):
        """Render the UI"""
        self._tabs = {}

        if self.f_user_management:
            from ktem.pages.login import LoginPage

            with gr.Tab("Login", elem_id="login-tab") as self._tabs["login-tab"]:
                self.login_page = LoginPage(self)

        with gr.Tab(
            "Chat", elem_id="chat-tab", visible=not self.f_user_management
        ) as self._tabs["chat-tab"]:
            self.chat_page = ChatPage(self)

        for index in self.index_manager.indices:
            with gr.Tab(
                f"{index.name} Index",
                elem_id=f"{index.id}-tab",
                elem_classes="indices-tab",
                visible=not self.f_user_management,
            ) as self._tabs[f"{index.id}-tab"]:
                page = index.get_index_page_ui()
                setattr(self, f"_index_{index.id}", page)

        with gr.Tab(
            "Admin", elem_id="admin-tab", visible=not self.f_user_management
        ) as self._tabs["admin-tab"]:
            self.admin_page = AdminPage(self)

        with gr.Tab(
            "Settings", elem_id="settings-tab", visible=not self.f_user_management
        ) as self._tabs["settings-tab"]:
            self.settings_page = SettingsPage(self)

        with gr.Tab(
            "Help", elem_id="help-tab", visible=not self.f_user_management
        ) as self._tabs["help-tab"]:
            self.help_page = HelpPage(self)

    def on_subscribe_public_events(self):
        if self.f_user_management:
            from ktem.db.engine import engine
            from ktem.db.models import User
            from sqlmodel import Session, select

            def signed_in_out(user_id):
                if not user_id:
                    return list(
                        (
                            gr.update(visible=True)
                            if k == "login-tab"
                            else gr.update(visible=False)
                        )
                        for k in self._tabs.keys()
                    )

                with Session(engine) as session:
                    user = session.exec(select(User).where(User.id == user_id)).first()
                    if user is None:
                        return list(
                            (
                                gr.update(visible=True)
                                if k == "login-tab"
                                else gr.update(visible=False)
                            )
                            for k in self._tabs.keys()
                        )

                    is_admin = user.admin

                tabs_update = []
                for k in self._tabs.keys():
                    if k == "login-tab":
                        tabs_update.append(gr.update(visible=False))
                    elif k == "admin-tab":
                        tabs_update.append(gr.update(visible=is_admin))
                    else:
                        tabs_update.append(gr.update(visible=True))

                return tabs_update

            self.subscribe_event(
                name="onSignIn",
                definition={
                    "fn": signed_in_out,
                    "inputs": [self.user_id],
                    "outputs": list(self._tabs.values()),
                    "show_progress": "hidden",
                },
            )

            self.subscribe_event(
                name="onSignOut",
                definition={
                    "fn": signed_in_out,
                    "inputs": [self.user_id],
                    "outputs": list(self._tabs.values()),
                    "show_progress": "hidden",
                },
            )
