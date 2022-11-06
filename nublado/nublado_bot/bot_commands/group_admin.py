import datetime as dt
import logging

from telegram import (
    Bot, Update, ChatPermissions,
    InlineKeyboardButton, InlineKeyboardMarkup
)

from telegram.ext import (
    CallbackContext, CallbackQueryHandler, MessageHandler, Filters
)
from telegram.constants import CHATMEMBER_CREATOR

from django.conf import settings
from django.utils.translation import gettext as _

from django_telegram.models import GroupMember
from django_telegram.functions.chat_actions import (
    send_typing_action
)
from django_telegram.functions.user import get_username_or_name
from django_telegram.functions.group import (
    restricted_group_member
)
from django_telegram.functions.admin import (
    update_group_members_from_admins,
    get_non_group_members,
    set_bot_language
)
from django_telegram.models import GroupMember
from language_days.functions import set_language_day_locale

logger = logging.getLogger('django')

GROUP_ID = settings.NUBLADO_GROUP_ID

# Callback data
AGREE_BTN_CALLBACK_DATA = "chat_member_welcome_agree"

# Translated strings.
msg_agree = _("I agree.")
msg_welcome = _(
    "Welcome to the group, {name}.\n\n" \
    "Please read the following rules and click the \"I agree\" button to participate.\n\n" \
    "*Rules*\n" \
    "- Communicate in only English and Spanish.\n" \
    "- Be a good example. Help others out with corrections."
)
msg_welcome_agreed = _(
    "Welcome to the group, {name}.\n\n" \
    "We require new members to introduce themselves with a voice message. " \
    "This helps us filter out fake accounts, trolls, etc.\n\n" \
    "We look forward to hearing from you."
)


@send_typing_action
@restricted_group_member(
    group_id=GROUP_ID,
    member_status=CHATMEMBER_CREATOR,
    group_chat=True,
    private_chat=False
)
def set_language(update: Update, context: CallbackContext) -> None:
    if len(context.args) >= 1:
        lang = str(context.args[0])
        if set_bot_language(lang):
            message = _("Bot language has been set.")
        else:
            message = _("Error setting bot language.")

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message
    )


@send_typing_action
@restricted_group_member(
    group_id=GROUP_ID,
    member_status=CHATMEMBER_CREATOR,
    group_chat=False
)
def get_non_members(update: Update, context: CallbackContext) -> None:
    get_non_group_members(context.bot, GROUP_ID)


@send_typing_action
@restricted_group_member(
    group_id=GROUP_ID,
    member_status=CHATMEMBER_CREATOR,
    group_chat=False
)
def update_group_admins(update: Update, context: CallbackContext) -> None:
    members = update_group_members_from_admins(context.bot, GROUP_ID)
    if members:
        message = _("Group members updated from admins.")
    else:
        message = _("Group members not updated from admins.")

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message
    )


def add_member(user_id, group_id):
    member_exists = GroupMember.objects.filter(
        group_id=group_id,
        user_id=user_id
    ).exists()
    if not member_exists:
        GroupMember.objects.create_group_member(
            group_id=group_id,
            user_id=user_id
        )


def remove_member(user_id, group_id):
    GroupMember.objects.filter(
        group_id=group_id,
        user_id=user_id
    ).delete()


def restrict_chat_member(bot: Bot, user_id: int, chat_id: int):
    try:
        permissions = ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_polls=False,
            can_send_other_messages=False  
        )
        bot.restrict_chat_member(
            user_id=user_id,
            chat_id=chat_id,
            permissions=permissions 
        )
        return True
    except:
        logger.error("Error disactivating member " + user_id)
        return False


def unrestrict_chat_member(bot: Bot, user_id: int, chat_id: int, interval_minutes: int = 2):
    """Restore restricted chat member to group's default member permissions."""
    try:
        chat = bot.get_chat(chat_id)
        permissions = chat.permissions
        date_now = dt.datetime.now()
        date_until = date_now + dt.timedelta(minutes=interval_minutes)
        bot.restrict_chat_member(
            user_id=user_id,
            chat_id=chat_id,
            permissions=permissions,
            until_date=date_until
        )
        return True
    except:
        logger.error("Error unrestricting member " + user_id)
        return False


def member_join(update: Update, context: CallbackContext) -> None:
    if update.message.new_chat_members:
        set_language_day_locale()
        for user in update.message.new_chat_members:
            # Add user to db
            add_member(user.id, GROUP_ID)
            # Mute user until he or she presses the "I agree" button.
            restrict_chat_member(context.bot, user.id, GROUP_ID)
            callback_data = AGREE_BTN_CALLBACK_DATA + " " + str(user.id)
            keyboard = [
                [
                    InlineKeyboardButton(
                        _(msg_agree),
                        callback_data=callback_data
                    ),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            message = _(msg_welcome).format(
                name=user.mention_markdown()
            )
            context.bot.send_message(
                text=message,
                chat_id=GROUP_ID,
                reply_markup=reply_markup
            )
        # Delete service message.
        try:
            context.bot.delete_message(
                message_id=update.message.message_id,
                chat_id=update.effective_chat.id
            )
        except:
            pass


def member_exit(update: Update, context: CallbackContext) -> None:
    if update.message.left_chat_member:
        user = update.message.left_chat_member
        # Delete member from db.
        remove_member(user.id, GROUP_ID)
        # Delete service message.
        try:
            context.bot.delete_message(
                message_id=update.message.message_id,
                chat_id=update.effective_chat.id
            )
        except:
            pass


# Listen for when new members join group.
member_join_handler = MessageHandler(
    Filters.status_update.new_chat_members,
    member_join
)


# Listen for when members leave group.
member_exit_handler = MessageHandler(
    Filters.status_update.left_chat_member,
    member_exit
)


def chat_member_welcome_agree(
    bot: Bot, user_id: int, chat_id: int, welcome_message_id: int = None
) -> None:
    unrestrict_chat_member(bot, user_id, chat_id)
    if welcome_message_id:
        try:
            bot.delete_message(
                message_id=welcome_message_id,
                chat_id=chat_id
            )
        except:
            logger.error("Error tring to delete  welcome message " + welcome_message_id)
    try:
        member = bot.get_chat_member(chat_id, user_id)
        message = _(msg_welcome_agreed).format(
            name=member.user.mention_markdown()
        )
        bot.send_message(
            chat_id=chat_id,
            text=message
        )
    except:
        pass


def welcome_button_handler_c(update: Update, context: CallbackContext) -> None:
    """Parse the CallbackQuery and perform corresponding actions."""
    query = update.callback_query
    query.answer()
    data = query.data.split(" ")
    if len(data) >= 2:
        if data[0] == AGREE_BTN_CALLBACK_DATA:
            user_id = int(data[1])
            # Check if effective user is the user that clicked the button.
            if update.effective_user.id == user_id:
                chat_member_welcome_agree(
                    context.bot,
                    user_id,
                    GROUP_ID,
                    query.message.message_id
                )
            else:
                logger.info("Another user clicked the welcome buttton.")
    else:
        query.edit_message_text(text=f"Selected option: {query.data}")


welcome_button_handler = CallbackQueryHandler(
    welcome_button_handler_c,
    pattern='^' + AGREE_BTN_CALLBACK_DATA
)
