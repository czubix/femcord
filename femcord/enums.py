"""
Copyright 2022-2025 czubix

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from enum import Enum

class FemcordEnum(Enum):
    def __str__(self) -> str:
        return self.name
    def __repr__(self) -> str:
        return self.name

class Intents(FemcordEnum):
    GUILDS = 1 << 0
    GUILD_MEMBERS = 1 << 1
    GUILD_BANS = 1 << 2
    GUILD_EMOJIS = 1 << 3
    GUILD_INTEGRATIONS = 1 << 4
    GUILD_WEBHOOKS = 1 << 5
    GUILD_INVITES = 1 << 6
    GUILD_VOICE_STATES = 1 << 7
    GUILD_PRESENCES = 1 << 8
    GUILD_MESSAGES = 1 << 9
    GUILD_MESSAGE_REACTIONS = 1 << 10
    GUILD_MESSAGE_TYPING = 1 << 11
    DIRECT_MESSAGES = 1 << 12
    DIRECT_MESSAGE_REACTIONS = 1 << 13
    DIRECT_MESSAGE_TYPING = 1 << 14

class Permissions(FemcordEnum):
    CREATE_INSTANT_INVITE = 1 << 0
    KICK_MEMBERS = 1 << 1
    BAN_MEMBERS = 1 << 2
    ADMINISTRATOR = 1 << 3
    MANAGE_CHANNELS = 1 << 4
    MANAGE_GUILD = 1 << 5
    ADD_REACTIONS = 1 << 6
    VIEW_AUDIT_LOG = 1 << 7
    PRIORITY_SPEAKER = 1 << 8
    STREAM = 1 << 9
    VIEW_CHANNEL = 1 << 10
    SEND_MESSAGES = 1 << 11
    SEND_TTS_MESSAGES = 1 << 12
    MANAGE_MESSAGES = 1 << 13
    EMBED_LINKS = 1 << 14
    ATTACH_FILES = 1 << 15
    READ_MESSAGE_HISTORY = 1 << 16
    MENTION_EVERYONE = 1 << 17
    USE_EXTERNAL_EMOJIS = 1 << 18
    VIEW_GUILD_INSIGHTS = 1 << 19
    CONNECT = 1 << 20
    SPEAK = 1 << 21
    MUTE_MEMBERS = 1 << 22
    DEAFEN_MEMBERS = 1 << 23
    MOVE_MEMBERS = 1 << 24
    USE_VAD = 1 << 25
    CHANGE_NICKNAME = 1 << 26
    MANAGE_NICKNAMES = 1 << 27
    MANAGE_ROLES = 1 << 28
    MANAGE_WEBHOOKS = 1 << 29
    MANAGE_GUILD_EXPRESSIONS = 1 << 30
    USE_APPLICATION_COMMANDS = 1 << 31
    REQUEST_TO_SPEAK = 1 << 32
    MANAGE_EVENTS = 1 << 33
    MANAGE_THREADS = 1 << 34
    CREATE_PUBLIC_THREADS = 1 << 35
    CREATE_PRIVATE_THREADS = 1 << 36
    USE_EXTERNAL_STICKERS = 1 << 37
    SEND_MESSAGES_IN_THREADS = 1 << 38
    USE_EMBEDDED_ACTIVITIES = 1 << 39
    MODERATE_MEMBERS = 1 << 40
    VIEW_CREATOR_MONETIZATION_ANALYTICS = 1 << 41
    USE_SOUNDBOARD = 1 << 42
    CREATE_GUILD_EXPRESSIONS = 1 << 43
    CREATE_EVENTS = 1 << 44
    USE_EXTERNAL_SOUNDS = 1 << 45
    SEND_VOICE_MESSAGES = 1 << 46
    SEND_POLLS = 1 << 49
    USE_EXTERNAL_APPS = 1 << 50

class UserFlags(FemcordEnum):
    STAFF = 1 << 0
    PARTNER = 1 << 1
    HYPESQUAD = 1 << 2
    BUG_HUNTER_LEVEL_1 = 1 << 3
    HYPESQUAD_ONLINE_HOUSE_1 = 1 << 6
    HYPESQUAD_ONLINE_HOUSE_2 = 1 << 7
    HYPESQUAD_ONLINE_HOUSE_3 = 1 << 8
    PREMIUM_EARLY_SUPPORTER = 1 << 9
    TEAM_PSEUDO_USER = 1 << 10
    BUG_HUNTER_LEVEL_2 = 1 << 14
    VERIFIED_BOT = 1 << 16
    VERIFIED_DEVELOPER = 1 << 17
    CERTIFIED_MODERATOR = 1 << 18
    BOT_HTTP_INTERACTIONS = 1 << 19

class PublicFlags(FemcordEnum):
    DISCORD_EMPLOYEE = 1 << 0
    PARTNERED_SERVER_OWNER = 1 << 1
    HYPESQUAD_EVENTS = 1 << 2
    BUG_HUNTER_LEVEL_1 = 1 << 3
    BRAVERY = 1 << 6
    BRILLIANCE = 1 << 7
    BALANCE = 1 << 8
    EARLY_SUPPORTER = 1 << 9
    BUG_HUNTER_LEVEL_2 = 1 << 14
    VERIFIED_BOT_DEVELOPER = 1 << 17
    CERTIFIED_MODERATOR = 1 << 18
    BOT_HTTP_INTERACTIONS = 1 << 19
    ACTIVE_DEVELOPER = 1 << 22

class ChannelFlags(FemcordEnum):
    PINNED = 1 << 1
    REQUIRE_TAG = 1 << 4

class SortOrderTypes(FemcordEnum):
    LATEST_ACTIVITY = 0
    CREATION_DATE = 1

class ChannelTypes(FemcordEnum):
    NONE = None
    GUILD_TEXT = 0
    DM = 1
    GUILD_VOICE = 2
    GROUP_DM = 3
    GUILD_CATEGORY = 4
    GUILD_NEWS = 5
    GUILD_STORE = 6
    GUILD_NEWS_THREAD = 10
    GUILD_PUBLIC_THREAD = 11
    GUILD_PRIVATE_THREAD = 12
    GUILD_STAGE_VOICE = 13
    GUILD_DIRECTORY = 14
    GUILD_FORUM = 15
    GUILD_MEDIA = 16

class MessageTypes(FemcordEnum):
    NONE = None
    DEFAULT = 0
    RECIPIENT_ADD = 1
    RECIPIENT_REMOVE = 2
    CALL = 3
    CHANNEL_NAME_CHANGE = 4
    CHANNEL_ICON_CHANGE = 5
    CHANNEL_PINNED_MESSAGE = 6
    USER_JOIN = 7
    PREMIUM_GUILD_SUBSCRIPTION = 8
    PREMIUM_GUILD_SUBSCRIPTION_TIER_1 = 9
    PREMIUM_GUILD_SUBSCRIPTION_TIER_2 = 10
    PREMIUM_GUILD_SUBSCRIPTION_TIER_3 = 11
    CHANNEL_FOLLOW_ADD = 12
    GUILD_STREAM = 13
    GUILD_DISCOVERY_DISQUALIFIED = 14
    GUILD_DISCOVERY_REQUALIFIED = 15
    GUILD_DISCOVERY_GRACE_PERIOD_INITIAL_WARNING = 16
    GUILD_DISCOVERY_GRACE_PERIOD_FINAL_WARNING = 17
    THREAD_CREATED = 18
    REPLY = 19
    CHAT_INPUT_COMMAND = 20
    THREAD_STARTER_MESSAGE = 21
    GUILD_INVITE_REMINDER = 22
    CONTEXT_MENU_COMMAND = 23
    AUTO_MODERATION_ACTION = 24
    ROLE_SUBSCRIPTION_PURCHASE = 25
    INTERACTION_PREMIUM_UPSELL = 26
    STAGE_START = 27
    STAGE_END = 28
    STAGE_SPEAKER = 29
    STAGE_RAISE_HAND = 30
    STAGE_TOPIC = 31
    GUILD_APPLICATION_PREMIUM_SUBSCRIPTION = 32
    PRIVATE_CHANNEL_INTEGRATION_ADDED = 33
    PRIVATE_CHANNEL_INTEGRATION_REMOVED = 34
    PREMIUM_REFERRAL = 35
    GUILD_INCIDENT_ALERT_MODE_ENABLED = 36
    GUILD_INCIDENT_ALERT_MODE_DISABLED = 37
    GUILD_INCIDENT_REPORT_RAID = 38
    GUILD_INCIDENT_REPORT_FALSE_ALARM = 39
    GUILD_DEADCHAT_REVIVE_PROMPT = 40
    CUSTOM_GIFT = 41
    GUILD_GAMING_STATS_PROMPT = 42
    POLL = 43
    PURCHASE_NOTIFICATION = 44
    VOICE_HANGOUT_INVITE = 45
    POLL_RESULT = 46
    CHANGELOG = 47
    NITRO_NOTIFICATION = 48

class MessageReferences(FemcordEnum):
    DEFAULT = 0
    FORWARD = 1

class ComponentTypes(FemcordEnum):
    ACTION_ROW = 1
    BUTTON = 2
    SELECT_MENU = 3
    TEXT_INPUT = 4
    USER_SELECT = 5
    ROLE_SELECT = 6
    MENTIONABLE_SELECT = 7
    CHANNEL_SELECT = 8
    SECTION = 9
    TEXT_DISPLAY = 10
    THUMBNAIL = 11
    MEDIA_GALLERY = 12
    FILE = 13
    SEPARATOR = 14
    CONTAINER = 17
    LABEL = 18

class ButtonStyles(FemcordEnum):
    PRIMARY = 1
    SECONDARY = 2
    SUCCESS = 3
    DANGER = 4
    LINK = 5
    PREMIUM = 6

class TextInputStyles(FemcordEnum):
    SHORT = 1
    PARAGRAPH = 2

class InteractionTypes(FemcordEnum):
    PING = 1
    APPLICATION_COMMAND = 2
    MESSAGE_COMPONENT = 3
    APPLICATION_COMMAND_AUTOCOMPLETE = 4
    MODAL_SUBMIT = 5

class InteractionCallbackTypes(FemcordEnum):
    PONG = 1
    CHANNEL_MESSAGE_WITH_SOURCE = 4
    DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE = 5
    DEFERRED_UPDATE_MESSAGE = 6
    UPDATE_MESSAGE = 7
    APPLICATION_COMMAND_AUTOCOMPLETE_RESULT = 8
    MODAL = 9
    PREMIUM_REQUIRED = 11
    LAUNCH_ACTIVITY = 12

class InteractionContextTypes(FemcordEnum):
    GUILD = 0
    BOT_DM = 1
    PRIVATE_CHANNEL = 2

class ApplicationCommandTypes(FemcordEnum):
    CHAT_INPUT = 1
    USER = 2
    MESSAGE = 3
    PRIMARY_ENTRY_POINT = 4

class ApplicationIntegrationTypes(FemcordEnum):
    GUILD_INSTALL = 0
    USER_INSTALL = 1

class CommandOptionTypes(FemcordEnum):
    SUB_COMMAND = 1
    SUB_COMMAND_GROUP = 2
    STRING = 3
    INTEGER = 4
    BOOLEAN = 5
    USER = 6
    CHANNEL = 7
    ROLE = 8
    MENTIONABLE = 9
    NUMBER = 10
    ATTACHMENT = 11

class StickerFormatTypes(FemcordEnum):
    PNG = 1
    APNG = 2
    LOTTIE = 3
    GIF = 4

class StickerTypes(FemcordEnum):
    STANDARD = 1
    GUILD = 2

class OverwriteTypes(FemcordEnum):
    ROLE = 0
    MEMBER = 1

class MessageFlags(FemcordEnum):
    CROSSPOSTED = 1 << 0
    IS_CROSSPOST = 1 << 1
    SUPPRESS_EMBEDS = 1 << 2
    SOURCE_MESSAGE_DELETED = 1 << 3
    URGENT = 1 << 4
    HAS_THREAD = 1 << 5
    EPHEMERAL = 1 << 6
    LOADING = 1 << 7
    FAILED_TO_MENTION_SOME_ROLES_IN_THREAD = 1 << 8
    SUPPRESS_NOTIFICATIONS = 1 << 12
    IS_VOICE_MESSAGE = 1 << 13
    HAS_SNAPSHOT = 1 << 14
    IS_COMPONENTS_V2 = 1 << 15

class VerificationLevel(FemcordEnum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    VERY_HIGH = 4

class DefaultMessageNotification(FemcordEnum):
    ALL_MESSAGES = 0
    ONLY_MENTIONS = 1

class ExplicitContentFilter(FemcordEnum):
    DISABLED = 0
    MEMBERS_WITHOUT_ROLES = 1
    ALL_MEMBERS = 2

class MfaLevel(FemcordEnum):
    NONE = 0
    ELEVATED = 1

class NSFWLevel(FemcordEnum):
    DEFAULT = 0
    EXPLICIT = 1
    SAFE = 2
    AGE_RESTRICTED = 3

class PrivacyLevel(FemcordEnum):
    PUBLIC = 1
    GUILD_ONLY = 2

class Opcodes(FemcordEnum):
    DISPATCH = 0
    HEARTBEAT = 1
    IDENTIFY = 2
    PRESENCE_UPDATE = 3
    VOICE_STATE_UPDATE = 4
    RESUME = 6
    RECONNECT = 7
    REQUEST_GUILD_MEMBERS = 8
    INVALID_SESSION = 9
    HELLO = 10
    HEARTBEAT_ACK = 11
    SEARCH_RECENT_MEMBERS = 35

class PremiumTypes(FemcordEnum):
    NONE = 0
    NITRO_CLASSIC = 1
    NITRO = 2
    NITRO_BASIC = 3

class PremiumTier(FemcordEnum):
    NONE = 0
    TIER_1 = 1
    TIER_2 = 2
    TIER_3 = 3

class StatusTypes(FemcordEnum):
    ONLINE = "online"
    DND = "dnd"
    IDLE = "idle"
    INVISIBLE = "invisible"
    OFFLINE = "offline"

class ActivityTypes(FemcordEnum):
    PLAYING = 0
    STREAMING = 1
    LISTENING = 2
    WATCHING = 3
    CUSTOM = 4
    COMPETING = 5
    HANGSTATUS = 6

class ActivityFlags(FemcordEnum):
    INSTANCE = 1 << 0
    JOIN = 1 << 1
    SPECTATE = 1 << 2
    JOIN_REQUEST = 1 << 3
    SYNC = 1 << 4
    PLAY = 1 << 5
    PARTY_PRIVACY_FRIENDS =1 << 6
    PARTY_PRIVACY_VOICE_CHANNEL = 1 << 7
    EMBEDDED = 1 << 8

class InviteTypes(FemcordEnum):
    GUILD = 0
    GROUP_DM = 1
    FRIEND = 2

class SelectDefaultValueTypes(FemcordEnum):
    USER = "user"
    ROLE = "role"
    CHANNEL = "channel"

class PaddingSizes(FemcordEnum):
    SMALL = 1
    LARGE = 2

class AuditLogEvents(FemcordEnum):
    GUILD_UPDATE = 1
    CHANNEL_CREATE = 10
    CHANNEL_UPDATE = 11
    CHANNEL_DELETE = 12
    CHANNEL_OVERWRITE_CREATE = 13
    CHANNEL_OVERWRITE_UPDATE = 14
    CHANNEL_OVERWRITE_DELETE = 15
    MEMBER_KICK = 20
    MEMBER_PRUNE = 21
    MEMBER_BAN_ADD = 22
    MEMBER_BAN_REMOVE = 23
    MEMBER_UPDATE = 24
    MEMBER_ROLE_UPDATE = 25
    MEMBER_MOVE = 26
    MEMBER_DISCONNECT = 27
    BOT_ADD = 28
    ROLE_CREATE = 30
    ROLE_UPDATE = 31
    ROLE_DELETE = 32
    INVITE_CREATE = 40
    INVITE_UPDATE = 41
    INVITE_DELETE = 42
    WEBHOOK_CREATE = 50
    WEBHOOK_UPDATE = 51
    WEBHOOK_DELETE = 52
    EMOJI_CREATE = 60
    EMOJI_UPDATE = 61
    EMOJI_DELETE = 62
    MESSAGE_DELETE = 72
    MESSAGE_BULK_DELETE = 73
    MESSAGE_PIN = 74
    MESSAGE_UNPIN = 75
    INTEGRATION_CREATE = 80
    INTEGRATION_UPDATE = 81
    INTEGRATION_DELETE = 82
    STAGE_INSTANCE_CREATE = 83
    STAGE_INSTANCE_UPDATE = 84
    STAGE_INSTANCE_DELETE = 85
    STICKER_CREATE = 90
    STICKER_UPDATE = 91
    STICKER_DELETE = 92
    GUILD_SCHEDULED_EVENT_CREATE = 100
    GUILD_SCHEDULED_EVENT_UPDATE = 101
    GUILD_SCHEDULED_EVENT_DELETE = 102
    THREAD_CREATE = 110
    THREAD_UPDATE = 111
    THREAD_DELETE = 112
    APPLICATION_COMMAND_PERMISSION_UPDATE = 121
    SOUNDBOARD_SOUND_CREATE = 130
    SOUNDBOARD_SOUND_UPDATE = 131
    SOUNDBOARD_SOUND_DELETE = 132
    AUTO_MODERATION_RULE_CREATE = 140
    AUTO_MODERATION_RULE_UPDATE = 141
    AUTO_MODERATION_RULE_DELETE = 142
    AUTO_MODERATION_BLOCK_MESSAGE = 143
    AUTO_MODERATION_FLAG_TO_CHANNEL = 144
    AUTO_MODERATION_USER_COMMUNICATION_DISABLED = 145
    CREATOR_MONETIZATION_REQUEST_CREATED = 150
    CREATOR_MONETIZATION_TERMS_ACCEPTED = 151
    ONBOARDING_PROMPT_CREATE = 163
    ONBOARDING_PROMPT_UPDATE = 164
    ONBOARDING_PROMPT_DELETE = 165
    ONBOARDING_CREATE = 166
    ONBOARDING_UPDATE = 167
    HOME_SETTINGS_CREATE = 190
    HOME_SETTINGS_UPDATE = 191
    VOICE_CHANNEL_STATUS_UPDATE = 192
    VOICE_CHANNEL_STATUS_REMOVE = 193
    UNKNOWN = -1

    @classmethod
    def _missing_(cls, value):
        return cls.UNKNOWN