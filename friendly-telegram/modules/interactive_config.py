"""
    █ █ ▀ █▄▀ ▄▀█ █▀█ ▀    ▄▀█ ▀█▀ ▄▀█ █▀▄▀█ ▄▀█
    █▀█ █ █ █ █▀█ █▀▄ █ ▄  █▀█  █  █▀█ █ ▀ █ █▀█

    Copyright 2022 t.me/hikariatama
    Licensed under the GNU GPLv3
"""

# <3 title: GeekConfig [geek]
# <3 pic: https://img.icons8.com/external-filled-outline-wichaiwi/64/000000/external-multitasking-generation-z-filled-outline-wichaiwi.png
# <3 desc: Interactive configurator for GeekTG

# scope: inline_content

from .. import loader, utils
from telethon.tl.types import Message
import logging
from typing import Union, List

logger = logging.getLogger(__name__)


def chunks(lst: Union[list, tuple, set], n: int) -> List[list]:
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


blacklist = [
    'Raphielgang Configuration Placeholder',
    'Uniborg configuration placeholder',
    'Logger'
]


@loader.tds
class GeekConfigMod(loader.Module):
    """Interactive configurator for GeekTG"""
    strings = {
        "name": "GeekConfig",
        "configure": "🎚 <b>Here you can configure your modules' configs</b>",
        "configuring_mod": "🎚 <b>Choose config option for mod</b> <code>{}</code>",
        "configuring_option": "🎚 <b>Configuring option </b><code>{}</code><b> of mod </b><code>{}</code>\n<i>ℹ️ {}</i>\n\n<b>Default: </b><code>{}</code>\n\n<b>Current: </b><code>{}</code>",
        "option_saved": "🎚 <b>Configuring option </b><code>{}</code><b> of mod </b><code>{}</code><b> saved!</b>\n<b>Current: </b><code>{}</code>"
    }

    def get(self, *args) -> dict:
        return self.db.get(self.strings['name'], *args)

    def set(self, *args) -> None:
        return self.db.set(self.strings['name'], *args)

    async def client_ready(self, client, db) -> None:
        self.db = db
        self.client = client
        self._bot_id = (await self.inline._bot.get_me()).id
        self._forms = {}

    async def inline__close(self, call: "aiogram.types.CallbackQuery") -> None:
        await call.delete()

    async def inline__set_config(self, call: "aiogram.types.CallbackQuery", query: str, mod: str, option: str, inline_message_id: str) -> None:
        for module in self.allmodules.modules:
            if module.strings('name') == mod:
                module.config[option] = query

        await call.edit(
            self.strings('option_saved')
            .format(
                mod,
                option,
                query
            ),
            reply_markup=[[
                {
                    'text': '👈 Back',
                    'callback': self.inline__configure,
                    'args': (mod,)
                },
                {
                    'text': '🚫 Close',
                    'callback': self.inline__close
                }
            ]],
            inline_message_id=inline_message_id
        )

    async def inline__configure_option(self, call: "aiogram.types.CallbackQuery", mod: str, config_opt: str) -> None:
        for module in self.allmodules.modules:
            if module.strings('name') == mod:
                await call.edit(
                    self.strings('configuring_option')
                    .format(
                        utils.escape_html(config_opt),
                        utils.escape_html(mod),
                        utils.escape_html(module.config.getdoc(config_opt)),
                        utils.escape_html(module.config.getdef(config_opt)),
                        utils.escape_html(module.config[config_opt])
                    ), reply_markup=[[
                        {
                            'text': '✍️ Enter value',
                            'input': '✍️ Enter new configuration value for this option',
                            'handler': self.inline__set_config,
                            'args': (mod, config_opt, call.inline_message_id)
                        }
                    ], [
                        {
                            'text': '👈 Back',
                            'callback': self.inline__configure,
                            'args': (mod,)
                        },
                        {
                            'text': '🚫 Close',
                            'callback': self.inline__close
                        }
                    ]]
                )

    async def inline__configure(self, call: "aiogram.types.CallbackQuery", mod: str) -> None:
        btns = []
        for module in self.allmodules.modules:
            if module.strings('name') == mod:
                for param in module.config:
                    btns += [{
                        'text': param,
                        'callback': self.inline__configure_option,
                        'args': (mod, param)
                    }]

        await call.edit(
            self.strings('configuring_mod')
            .format(
                utils.escape_html(mod)
            ),
            reply_markup=list(chunks(btns, 2)) + [[
                {
                    'text': '👈 Back',
                    'callback': self.inline__global_config
                },
                {
                    'text': '🚫 Close',
                    'callback': self.inline__close
                }
            ]]
        )

    async def inline__global_config(self, call: Union[Message, "aiogram.types.CallbackQuery"]) -> None:
        to_config = [mod.strings('name') for mod in self.allmodules.modules if hasattr(
            mod, 'config') and mod.strings('name') not in blacklist]
        kb = []
        for mod_row in chunks(to_config, 3):
            row = []
            for btn in mod_row:
                row += [{
                    'text': btn,
                    'callback': self.inline__configure,
                    'args': (btn,)
                }]

            kb += [row]

        kb += [[{
            'text': '🚫 Close',
            'callback': self.inline__close
        }]]

        if isinstance(call, Message):
            await self.inline.form(self.strings('configure'), reply_markup=kb, message=call)
        else:
            await call.edit(self.strings('configure'), reply_markup=kb)

    async def configcmd(self, message: Message) -> None:
        """Configure modules"""
        await self.inline__global_config(message)

    async def watcher(self, message: Message) -> None:
        if not getattr(message, 'out', False) or \
                not getattr(message, 'via_bot_id', False) or \
                message.via_bot_id != self._bot_id or \
                'This message is gonna be deleted...' not in getattr(message, 'raw_text', ''):
            return

        await message.delete()
