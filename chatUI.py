import flet as ft

ACCOUNTS = {
    'test': '12345678',
    'user': 'password'
}

class Message():
    def __init__(self, user: str, text: str, message_type: str):
        self.user = user
        self.text = text
        self.message_type = message_type

class ChatMessage(ft.Row):
    def __init__(self, message: Message):
        super().__init__()
        self.vertical_alignment = ft.CrossAxisAlignment.START
        self.controls=[
                ft.CircleAvatar(
                    content=ft.Text(self.get_initials(message.user)),
                    color=ft.colors.WHITE,
                    bgcolor=self.get_avatar_color(message.user),
                ),
                ft.Column(
                    [
                        ft.Text(message.user, weight="bold"),
                        ft.Text(message.text, selectable=True),
                    ],
                    tight=True,
                    spacing=5,
                ),
            ]

    def get_initials(self, user_name: str):
        return user_name[:1].capitalize()

    def get_avatar_color(self, user_name: str):
        colors_lookup = [
            ft.colors.AMBER,
            ft.colors.BLUE,
            ft.colors.BROWN,
            ft.colors.CYAN,
            ft.colors.GREEN,
            ft.colors.INDIGO,
            ft.colors.LIME,
            ft.colors.ORANGE,
            ft.colors.PINK,
            ft.colors.PURPLE,
            ft.colors.RED,
            ft.colors.TEAL,
            ft.colors.YELLOW,
        ]
        return colors_lookup[hash(user_name) % len(colors_lookup)]

def main(page: ft.Page):
    content = None

    def send_message_click(e):
        page.pubsub.send_all(Message(user=page.session.get('username'), text=new_message.value, message_type="chat_message"))
        new_message.value = ""
        page.update()

    def join_click(e):
        if not username.value:
            username.error_text = "Username cannot be blank!"
            username.update()
        elif username.value not in ACCOUNTS.keys():
            username.error_text = 'User does not exist!'
            username.update()
        elif password.value != ACCOUNTS[username.value]:
            password.error_text = 'Incorrect password'
            password.update()
        else:
            page.session.set("username", username.value)
            name_dialog.open = False
            page.pubsub.send_all(Message(user=username.value, text=f"{username.value} has joined the chat.", message_type="login_message"))
            content.visible = True
            page.update()
            
    username = ft.TextField(label="Enter your user name")
    password = ft.TextField(label="Enter your password")

    name_dialog = ft.AlertDialog(
        open=True,
        modal=True,
        title=ft.Text("Welcome!"),
        content=ft.Column([username, password], tight=True),
        actions=[ft.ElevatedButton(text="Join chat", on_click=join_click)],
        actions_alignment="end",
    )

    page.overlay.append(name_dialog)

    # Chat messages
    chat = ft.ListView(
        expand=True,
        spacing=10,
        auto_scroll=True,
    )

    # A new message entry form
    new_message = ft.TextField(
        hint_text="Write a message...",
        autofocus=True,
        shift_enter=True,
        min_lines=1,
        max_lines=5,
        filled=True,
        expand=True,
        on_submit=send_message_click,
    )

    tab = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(icon=ft.icons.PERSON),
            ft.Tab(icon=ft.icons.GROUP),
        ],
        expand=True
    )

    content = ft.Row(
        expand=True,
        visible=False,
        controls=[
            ft.Column(
                controls=[
                    ft.Container(
                        tab,
                    ),
                ],
                expand=1
            ),
            ft.Column(
                expand=3,
                controls=[
                    chat,
                    ft.Row(
                        controls=[
                            new_message,
                            ft.IconButton(
                                icon=ft.icons.SEND_ROUNDED,
                                tooltip="Send message",
                                on_click=send_message_click,
                            ),
                        ]
                    )
                ]
            )
        ]
    )

    page.add(content)

    def on_message(message: Message):
        if message.message_type == "chat_message":
            m = ChatMessage(message)
        elif message.message_type == "login_message":
            m = ft.Text(message.text, italic=True, color=ft.colors.BLACK45, size=12)
        chat.controls.append(m)
        page.update()

    page.pubsub.subscribe(on_message)

ft.app(target=main)