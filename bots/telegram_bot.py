"""
Telegram-бот CarSales — inline-меню, навигация через edit_message.
"""
import logging
import os

import requests
from telegram import InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.request import HTTPXRequest

from bots.keyboards import (
    auto_detail_keyboard,
    autos_list_keyboard,
    back_home_row,
    brands_keyboard,
    filter_menu_keyboard,
    inbox_keyboard,
    main_menu_keyboard,
    regions_keyboard,
)

logger = logging.getLogger(__name__)

WELCOME = (
    "🚗 <b>CarSales Bot</b>\n\n"
    "Мобильный канал платформы продажи автомобилей.\n"
    "Выберите действие кнопкой ниже — меню обновляется на месте, "
    "чтобы не засорять переписку."
)


class CarSalesBotClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url.rstrip('/')
        self.headers = {'X-Integration-Key': api_key, 'Content-Type': 'application/json'}

    def _get(self, path, params=None):
        response = requests.get(
            f'{self.base_url}{path}',
            headers=self.headers,
            params=params,
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    def _post(self, path, data):
        response = requests.post(
            f'{self.base_url}{path}',
            headers=self.headers,
            json=data,
            timeout=15,
        )
        if response.status_code >= 400:
            detail = response.json().get('detail', response.text)
            raise ValueError(detail)
        return response.json()

    def link_account(self, token, chat_id, username):
        return self._post('/api/integration/link/', {
            'token': token,
            'telegram_chat_id': chat_id,
            'telegram_username': username,
        })

    def unlink_account(self, chat_id):
        return self._post('/api/integration/unlink/', {'telegram_chat_id': chat_id})

    def link_status(self, chat_id):
        return self._get('/api/integration/status/', {'telegram_chat_id': chat_id})

    def search_autos(self, query, page=1):
        return self._get('/api/integration/autos/search/', {'q': query, 'page': page})

    def filter_autos(self, params, page=1):
        params = dict(params)
        params['page'] = page
        return self._get('/api/integration/autos/filter/', params)

    def get_brands(self):
        return self._get('/api/integration/brands/')

    def get_regions(self):
        return self._get('/api/integration/regions/')

    def get_auto(self, auto_id):
        return self._get(f'/api/integration/autos/{auto_id}/')

    def get_favorites(self, chat_id):
        return self._get('/api/integration/favorites/', {'telegram_chat_id': chat_id})

    def get_inbox(self, chat_id):
        return self._get('/api/integration/messages/inbox/', {'telegram_chat_id': chat_id})

    def send_message(self, chat_id, auto_id, text):
        return self._post('/api/integration/messages/', {
            'telegram_chat_id': chat_id,
            'auto_id': auto_id,
            'message': text,
        })


def _price_fmt(price):
    return f"{price:,} ₽".replace(',', ' ')


def _auto_caption(auto):
    lines = [
        f"<b>{auto['brand']} {auto['model']}</b> ({auto['year']})",
        f"💰 {_price_fmt(auto['price'])}",
        f"📍 {auto['region']} · 🛣 {auto['mileage']:,} км".replace(',', ' '),
        f"📋 {auto['sell_status']}",
        '',
        auto['description'],
        '',
        f'<a href="{auto["web_url"]}">Открыть на сайте</a>',
    ]
    return '\n'.join(lines)


def _filter_summary(flt):
    parts = []
    if flt.get('brand_name'):
        parts.append(f"Марка: {flt['brand_name']}")
    if flt.get('region_name'):
        parts.append(f"Регион: {flt['region_name']}")
    if flt.get('min_price'):
        parts.append(f"Цена от: {_price_fmt(int(flt['min_price']))}")
    if flt.get('max_price'):
        parts.append(f"Цена до: {_price_fmt(int(flt['max_price']))}")
    if flt.get('year'):
        parts.append(f"Год: {flt['year']}")
    return '\n'.join(parts) if parts else 'Фильтр не задан — выберите параметры.'


LINK_HINT = (
    'Личный код смотрите в <b>зелёной полосе вверху сайта AVTO.RU</b> '
    '(появляется после входа в аккаунт).\n'
    'Скопируйте код и отправьте его сюда одним сообщением.'
)


def _init_user_data(context):
    context.user_data.setdefault('ui_id', None)
    context.user_data.setdefault('ui_history', [])
    context.user_data.setdefault('extra_ids', [])
    context.user_data.setdefault('filter', {})
    context.user_data.setdefault('list_ctx', None)
    context.user_data.setdefault('mode', None)


def _is_linked(client, chat_id):
    try:
        return client.link_status(chat_id).get('linked', False)
    except requests.RequestException:
        return False


def _main_menu_kb(client, chat_id):
    return main_menu_keyboard(_is_linked(client, chat_id))


async def _purge_chat(context, bot, chat_id):
    """Удалить все сообщения бота в чате (меню, карточки)."""
    ids = set(context.user_data.get('ui_history', []))
    ui_id = context.user_data.get('ui_id')
    if ui_id:
        ids.add(ui_id)
    ids.update(context.user_data.get('extra_ids', []))
    for mid in ids:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=mid)
        except BadRequest:
            pass
    context.user_data['ui_history'] = []
    context.user_data['extra_ids'] = []
    context.user_data['ui_id'] = None


async def _go_home(update, context, client):
    context.user_data['mode'] = None
    context.user_data['filter'] = {}
    context.user_data['list_ctx'] = None
    chat_id = update.effective_chat.id
    await _purge_chat(context, context.bot, chat_id)
    await _show_ui(update, context, WELCOME, _main_menu_kb(client, chat_id))


def _track_extra(context, message_id):
    if message_id:
        context.user_data['extra_ids'].append(message_id)


async def _delete_extras(context, bot, chat_id):
    for mid in context.user_data.get('extra_ids', []):
        try:
            await bot.delete_message(chat_id=chat_id, message_id=mid)
        except BadRequest:
            pass
    context.user_data['extra_ids'] = []


async def _show_ui(update, context, text, reply_markup, parse_mode=ParseMode.HTML):
    """Показать/обновить главное UI-сообщение (без замусоривания чата)."""
    _init_user_data(context)
    chat_id = update.effective_chat.id
    bot = context.bot
    ui_id = context.user_data.get('ui_id')

    if update.callback_query:
        await update.callback_query.answer()

    if ui_id:
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=ui_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
                disable_web_page_preview=True,
            )
            return
        except BadRequest as exc:
            if 'message is not modified' not in str(exc).lower():
                logger.debug('edit_message failed: %s', exc)

    await _delete_extras(context, bot, chat_id)
    if update.callback_query and update.callback_query.message:
        try:
            msg = await update.callback_query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
                disable_web_page_preview=True,
            )
            context.user_data['ui_id'] = msg.message_id
            return
        except BadRequest:
            pass

    old_id = context.user_data.get('ui_id')
    if old_id:
        context.user_data.setdefault('ui_history', []).append(old_id)
        try:
            await bot.delete_message(chat_id=chat_id, message_id=old_id)
        except BadRequest:
            pass

    msg = await bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup,
        parse_mode=parse_mode,
        disable_web_page_preview=True,
    )
    context.user_data['ui_id'] = msg.message_id


async def _show_auto_detail(update, context, client, auto_id):
    """Карточка с фото (отдельное сообщение удаляется при «Назад»)."""
    chat_id = update.effective_chat.id
    bot = context.bot
    await _delete_extras(context, bot, chat_id)

    try:
        auto = client.get_auto(auto_id)
    except requests.HTTPError:
        await _show_ui(update, context, '❌ Объявление не найдено.', _main_menu_kb(client, chat_id))
        return
    except requests.RequestException:
        await _show_ui(update, context, '⚠️ Сервис временно недоступен.', _main_menu_kb(client, chat_id))
        return

    caption = _auto_caption(auto)
    keyboard = auto_detail_keyboard(auto_id)
    context.user_data['list_ctx'] = context.user_data.get('list_ctx') or {'back': 'm:home'}

    if auto.get('photo_url'):
        msg = await bot.send_photo(
            chat_id=chat_id,
            photo=auto['photo_url'],
            caption=caption,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )
    else:
        msg = await bot.send_message(
            chat_id=chat_id,
            text=caption,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
    _track_extra(context, msg.message_id)

    if update.callback_query:
        await update.callback_query.answer()


def _list_nav_callbacks(list_ctx, page, data):
    prefix = list_ctx['type']
    if prefix == 'search':
        prev_cb = f"m:srch_p:{page - 1}" if page > 1 else None
        next_cb = f"m:srch_p:{page + 1}" if data.get('has_next') else None
    elif prefix == 'brand':
        prev_cb = f"m:brand_p:{page - 1}" if page > 1 else None
        next_cb = f"m:brand_p:{page + 1}" if data.get('has_next') else None
    elif prefix == 'filter':
        prev_cb = f"m:flt_p:{page - 1}" if page > 1 else None
        next_cb = f"m:flt_p:{page + 1}" if data.get('has_next') else None
    else:
        prev_cb = next_cb = None
    return prev_cb, next_cb


async def _show_autos_page(update, context, client, data, list_ctx):
    chat_id = update.effective_chat.id
    autos = data['results']
    if not autos:
        await _show_ui(
            update, context,
            '🔍 По вашему запросу ничего не найдено.\n\nПопробуйте другие параметры.',
            _main_menu_kb(client, chat_id),
        )
        return

    list_ctx['page'] = data['page']
    list_ctx['has_next'] = data['has_next']
    context.user_data['list_ctx'] = list_ctx

    title = list_ctx.get('title', 'Результаты')
    text = f"<b>{title}</b>\n\nНайдено: {data['total']}. Страница {data['page']}.\nВыберите объявление:"
    prev_cb, next_cb = _list_nav_callbacks(list_ctx, data['page'], data)
    kb = autos_list_keyboard(autos, prev_cb, next_cb, list_ctx.get('back', 'm:back'))
    await _show_ui(update, context, text, kb)


def build_bot_application(token, base_url, api_key, proxy_url=None):
    client = CarSalesBotClient(base_url, api_key)

    async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        _init_user_data(context)
        context.user_data['mode'] = None
        try:
            await context.bot.set_my_commands([])
        except Exception:
            pass
        await _go_home(update, context, client)

    async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        data = query.data or ''
        _init_user_data(context)
        chat_id = update.effective_chat.id

        if data == 'm:home':
            await _go_home(update, context, client)
            return

        if data == 'm:back':
            await _delete_extras(context, context.bot, chat_id)
            ctx = context.user_data.get('list_ctx')
            if ctx and ctx.get('type') in ('search', 'brand', 'filter'):
                await _restore_list(update, context, client, ctx)
                return
            await _go_home(update, context, client)
            return

        if data == 'm:search':
            context.user_data['mode'] = 'await_search'
            await _show_ui(
                update, context,
                '🔍 <b>Поиск</b>\n\nВведите марку или модель (например: <code>BMW</code> или <code>Camry</code>):',
                InlineKeyboardMarkup([back_home_row()]),
            )
            return

        if data == 'm:brands':
            try:
                brands = client.get_brands()
            except requests.RequestException:
                await query.answer('Сервис недоступен', show_alert=True)
                return
            if not brands:
                await _show_ui(update, context, 'Каталог пуст.', _main_menu_kb(client, chat_id))
                return
            await _show_ui(
                update, context,
                '🏷 <b>Каталог по маркам</b>\n\nВыберите марку:',
                brands_keyboard(brands),
            )
            return

        if data.startswith('m:brand:'):
            brand_id = data.split(':')[-1]
            try:
                brands = {str(b['id']): b['name'] for b in client.get_brands()}
                brand_name = brands.get(brand_id, '')
                payload = client.filter_autos({'brand_id': brand_id}, page=1)
            except requests.RequestException:
                await query.answer('Сервис недоступен', show_alert=True)
                return
            list_ctx = {
                'type': 'brand',
                'brand_id': brand_id,
                'title': f'Марка: {brand_name}',
                'back': 'm:brands',
            }
            await _show_autos_page(update, context, client, payload, list_ctx)
            return

        if data.startswith('m:brand_p:'):
            page = int(data.split(':')[-1])
            list_ctx = context.user_data.get('list_ctx')
            if not list_ctx or list_ctx.get('type') != 'brand':
                await query.answer('Сессия устарела', show_alert=True)
                return
            try:
                payload = client.filter_autos(
                    {'brand_id': list_ctx['brand_id']},
                    page=page,
                )
            except requests.RequestException:
                await query.answer('Ошибка загрузки', show_alert=True)
                return
            await _show_autos_page(update, context, client, payload, list_ctx)
            return

        if data.startswith('m:srch_p:'):
            page = int(data.split(':')[-1])
            list_ctx = context.user_data.get('list_ctx')
            if not list_ctx or list_ctx.get('type') != 'search':
                await query.answer('Сессия устарела', show_alert=True)
                return
            try:
                payload = client.search_autos(list_ctx['q'], page=page)
            except requests.RequestException:
                await query.answer('Ошибка загрузки', show_alert=True)
                return
            await _show_autos_page(update, context, client, payload, list_ctx)
            return

        if data == 'm:filter':
            flt = context.user_data.setdefault('filter', {})
            text = '⚙️ <b>Фильтр</b>\n\n' + _filter_summary(flt)
            await _show_ui(update, context, text, filter_menu_keyboard())
            return

        if data == 'm:flt:reset':
            context.user_data['filter'] = {}
            await _show_ui(
                update, context,
                '⚙️ <b>Фильтр</b>\n\nФильтр сброшен.',
                filter_menu_keyboard(),
            )
            return

        if data == 'm:flt:brand':
            try:
                brands = client.get_brands()
            except requests.RequestException:
                await query.answer('Сервис недоступен', show_alert=True)
                return
            await _show_ui(
                update, context,
                'Выберите марку для фильтра:',
                brands_keyboard(brands, prefix='m:flt:set_b'),
            )
            return

        if data.startswith('m:flt:set_b:'):
            brand_id = data.split(':')[-1]
            brands = {str(b['id']): b['name'] for b in client.get_brands()}
            flt = context.user_data.setdefault('filter', {})
            flt['brand_id'] = brand_id
            flt['brand_name'] = brands.get(brand_id, '')
            await _show_ui(
                update, context,
                '⚙️ <b>Фильтр</b>\n\n' + _filter_summary(flt),
                filter_menu_keyboard(),
            )
            return

        if data == 'm:flt:region':
            try:
                regions = client.get_regions()
            except requests.RequestException:
                await query.answer('Сервис недоступен', show_alert=True)
                return
            await _show_ui(update, context, 'Выберите регион:', regions_keyboard(regions))
            return

        if data.startswith('m:flt:set_r:'):
            region_id = data.split(':')[-1]
            regions = {str(r['id']): r['name'] for r in client.get_regions()}
            flt = context.user_data.setdefault('filter', {})
            flt['region_id'] = region_id
            flt['region_name'] = regions.get(region_id, '')
            await _show_ui(
                update, context,
                '⚙️ <b>Фильтр</b>\n\n' + _filter_summary(flt),
                filter_menu_keyboard(),
            )
            return

        if data == 'm:flt:skip_r':
            flt = context.user_data.setdefault('filter', {})
            flt.pop('region_id', None)
            flt.pop('region_name', None)
            await _show_ui(
                update, context,
                '⚙️ <b>Фильтр</b>\n\n' + _filter_summary(flt),
                filter_menu_keyboard(),
            )
            return

        if data in ('m:flt:min', 'm:flt:max', 'm:flt:year'):
            prompts = {
                'm:flt:min': ('await_flt_min', 'Введите минимальную цену (только цифры):'),
                'm:flt:max': ('await_flt_max', 'Введите максимальную цену (только цифры):'),
                'm:flt:year': ('await_flt_year', 'Введите год выпуска (например 2018):'),
            }
            mode, prompt = prompts[data]
            context.user_data['mode'] = mode
            await _show_ui(
                update, context,
                f'⚙️ {prompt}',
                InlineKeyboardMarkup([back_home_row('m:filter')]),
            )
            return

        if data == 'm:flt:run':
            await _run_filter(update, context, client)
            return

        if data.startswith('m:flt_p:'):
            page = int(data.split(':')[-1])
            await _run_filter(update, context, client, page=page)
            return

        if data.startswith('m:auto:'):
            auto_id = int(data.split(':')[-1])
            await _show_auto_detail(update, context, client, auto_id)
            return

        if data.startswith('m:msg:'):
            auto_id = int(data.split(':')[-1])
            context.user_data['mode'] = f'await_msg:{auto_id}'
            await _show_ui(
                update, context,
                f'✉️ Напишите сообщение продавцу по объявлению #{auto_id}.\n'
                'Отправьте одним сообщением в чат:',
                InlineKeyboardMarkup([back_home_row('m:back')]),
            )
            return

        if data == 'm:favorites':
            try:
                autos = client.get_favorites(chat_id)
            except ValueError as exc:
                await _show_ui(
                    update, context,
                    f'⭐ {exc}\n\nСначала привяжите аккаунт.',
                    _main_menu_kb(client, chat_id),
                )
                return
            except requests.RequestException:
                await query.answer('Сервис недоступен', show_alert=True)
                return
            if not autos:
                await _show_ui(update, context, '⭐ Избранное пусто.', _main_menu_kb(client, chat_id))
                return
            list_ctx = {'type': 'fav', 'title': 'Избранное', 'back': 'm:home', 'has_next': False}
            data_page = {'results': autos, 'page': 1, 'total': len(autos), 'has_next': False, 'has_prev': False}
            await _show_autos_page(update, context, client, data_page, list_ctx)
            return

        if data == 'm:inbox':
            try:
                inbox = client.get_inbox(chat_id)
            except ValueError as exc:
                await _show_ui(update, context, f'💬 {exc}', _main_menu_kb(client, chat_id))
                return
            except requests.RequestException:
                await query.answer('Сервис недоступен', show_alert=True)
                return
            messages = inbox.get('messages', [])
            if not messages:
                await _show_ui(update, context, '💬 Нет непрочитанных сообщений.', _main_menu_kb(client, chat_id))
                return
            text = f"💬 <b>Сообщения</b>\n\nНепрочитанных: {inbox['unread_count']}"
            await _show_ui(update, context, text, inbox_keyboard(messages))
            return

        if data == 'm:link':
            context.user_data['mode'] = 'await_link'
            await _show_ui(
                update, context,
                '🔗 <b>Привязка аккаунта</b>\n\n' + LINK_HINT,
                InlineKeyboardMarkup([back_home_row()]),
            )
            return

        if data == 'm:unlink':
            try:
                client.unlink_account(chat_id)
                context.user_data['mode'] = None
                await query.answer('Аккаунт отвязан')
                await _go_home(update, context, client)
            except ValueError as exc:
                await query.answer(str(exc), show_alert=True)
            except requests.RequestException:
                await query.answer('Сервис недоступен', show_alert=True)
            return

        await query.answer()

    async def _run_filter(update, context, client, page=1):
        flt = context.user_data.get('filter', {})
        params = {}
        if flt.get('brand_id'):
            params['brand_id'] = flt['brand_id']
        if flt.get('region_id'):
            params['region_id'] = flt['region_id']
        if flt.get('min_price'):
            params['min_price'] = flt['min_price']
        if flt.get('max_price'):
            params['max_price'] = flt['max_price']
        if flt.get('year'):
            params['year'] = flt['year']
        try:
            payload = client.filter_autos(params, page=page)
        except requests.RequestException:
            await _show_ui(update, context, '⚠️ Сервис недоступен.', _main_menu_kb(client, chat_id))
            return
        list_ctx = {
            'type': 'filter',
            'title': 'Результаты фильтра',
            'back': 'm:filter',
            'params': params,
        }
        await _show_autos_page(update, context, client, payload, list_ctx)

    async def _restore_list(update, context, client, list_ctx):
        try:
            if list_ctx['type'] == 'search':
                payload = client.search_autos(list_ctx['q'], page=list_ctx.get('page', 1))
            elif list_ctx['type'] == 'brand':
                payload = client.filter_autos(
                    {'brand_id': list_ctx['brand_id']},
                    page=list_ctx.get('page', 1),
                )
            elif list_ctx['type'] == 'filter':
                payload = client.filter_autos(
                    list_ctx.get('params', {}),
                    page=list_ctx.get('page', 1),
                )
            else:
                await _go_home(update, context, client)
                return
            await _show_autos_page(update, context, client, payload, list_ctx)
        except requests.RequestException:
            await _show_ui(update, context, '⚠️ Сервис недоступен.', _main_menu_kb(client, chat_id))

    async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
        _init_user_data(context)
        mode = context.user_data.get('mode')
        text = (update.message.text or '').strip()
        chat_id = update.effective_chat.id

        if not mode:
            await update.message.delete()
            return

        try:
            await update.message.delete()
        except BadRequest:
            pass

        if mode == 'await_search':
            if not text:
                await _show_ui(update, context, 'Введите текст для поиска.', _main_menu_kb(client, chat_id))
                return
            try:
                payload = client.search_autos(text, page=1)
            except requests.RequestException:
                await _show_ui(update, context, '⚠️ Сервис недоступен.', _main_menu_kb(client, chat_id))
                return
            context.user_data['mode'] = None
            list_ctx = {'type': 'search', 'q': text, 'title': f'Поиск: {text}', 'back': 'm:home'}
            await _show_autos_page(update, context, client, payload, list_ctx)
            return

        if mode == 'await_link':
            try:
                result = client.link_account(
                    text,
                    chat_id,
                    update.effective_user.username or '',
                )
                context.user_data['mode'] = None
                await _show_ui(
                    update, context,
                    f"✅ Аккаунт <b>{result['username']}</b> привязан!",
                    _main_menu_kb(client, chat_id),
                )
            except ValueError as exc:
                await _show_ui(update, context, f'❌ {exc}', _main_menu_kb(client, chat_id))
            except requests.RequestException:
                await _show_ui(update, context, '⚠️ Сервис недоступен.', _main_menu_kb(client, chat_id))
            return

        if mode == 'await_flt_min':
            if not text.isdigit():
                await _show_ui(update, context, 'Введите число.', filter_menu_keyboard())
                return
            context.user_data['filter']['min_price'] = text
            context.user_data['mode'] = None
            flt = context.user_data['filter']
            await _show_ui(update, context, '⚙️ <b>Фильтр</b>\n\n' + _filter_summary(flt), filter_menu_keyboard())
            return

        if mode == 'await_flt_max':
            if not text.isdigit():
                await _show_ui(update, context, 'Введите число.', filter_menu_keyboard())
                return
            context.user_data['filter']['max_price'] = text
            context.user_data['mode'] = None
            flt = context.user_data['filter']
            await _show_ui(update, context, '⚙️ <b>Фильтр</b>\n\n' + _filter_summary(flt), filter_menu_keyboard())
            return

        if mode == 'await_flt_year':
            if not text.isdigit() or len(text) != 4:
                await _show_ui(update, context, 'Введите год из 4 цифр.', filter_menu_keyboard())
                return
            context.user_data['filter']['year'] = text
            context.user_data['mode'] = None
            flt = context.user_data['filter']
            await _show_ui(update, context, '⚙️ <b>Фильтр</b>\n\n' + _filter_summary(flt), filter_menu_keyboard())
            return

        if mode and mode.startswith('await_msg:'):
            auto_id = int(mode.split(':')[1])
            try:
                result = client.send_message(chat_id, auto_id, text)
                context.user_data['mode'] = None
                await _delete_extras(context, context.bot, chat_id)
                await _show_ui(
                    update, context,
                    f"✅ {result['message']}",
                    _main_menu_kb(client, chat_id),
                )
            except ValueError as exc:
                await _show_ui(update, context, f'❌ {exc}', _main_menu_kb(client, chat_id))
            except requests.RequestException:
                await _show_ui(update, context, '⚠️ Сервис недоступен.', _main_menu_kb(client, chat_id))
            return

    request_kwargs = {
        'connect_timeout': 30.0,
        'read_timeout': 30.0,
        'write_timeout': 30.0,
    }
    if proxy_url:
        request_kwargs['proxy_url'] = proxy_url

    app = Application.builder().token(token).request(HTTPXRequest(**request_kwargs)).build()
    app.bot_data['client'] = client

    app.add_handler(CommandHandler('start', cmd_start))
    app.add_handler(CallbackQueryHandler(on_callback, pattern=r'^m:'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    return app


def run_bot():
    token = os.getenv('TELEGRAM_BOT_TOKEN', '')
    base_url = os.getenv('SITE_BASE_URL', 'http://127.0.0.1:8000')
    api_key = os.getenv('INTEGRATION_API_KEY', 'dev-integration-key-change-me')
    proxy_url = os.getenv('TELEGRAM_PROXY_URL', '').strip() or None

    if not token:
        raise RuntimeError('Задайте переменную окружения TELEGRAM_BOT_TOKEN')

    logging.basicConfig(level=logging.INFO)
    app = build_bot_application(token, base_url, api_key, proxy_url=proxy_url)
    logger.info('Telegram bot started, API: %s', base_url)
    if proxy_url:
        logger.info('Используется прокси для Telegram API')
    app.run_polling(allowed_updates=Update.ALL_TYPES)
