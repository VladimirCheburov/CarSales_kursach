from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def btn(text, data):
    return InlineKeyboardButton(text, callback_data=data)


def main_menu_keyboard(is_linked=False):
    link_row = [btn('🔓 Отвязать аккаунт', 'm:unlink')] if is_linked else [btn('🔗 Привязать аккаунт', 'm:link')]
    return InlineKeyboardMarkup([
        [btn('🔍 Поиск', 'm:search'), btn('🏷 Каталог по маркам', 'm:brands')],
        [btn('⚙️ Фильтр', 'm:filter'), btn('⭐ Избранное', 'm:favorites')],
        [btn('💬 Сообщения', 'm:inbox')],
        link_row,
    ])


def back_home_row(back_data='m:back'):
    return [btn('◀️ Назад', back_data), btn('🏠 Главное меню', 'm:home')]


def filter_menu_keyboard():
    rows = [
        [btn('Марка', 'm:flt:brand'), btn('Регион', 'm:flt:region')],
        [btn('Цена от', 'm:flt:min'), btn('Цена до', 'm:flt:max')],
        [btn('Год выпуска', 'm:flt:year')],
        [btn('✅ Показать результаты', 'm:flt:run')],
        [btn('🔄 Сбросить фильтр', 'm:flt:reset')],
    ]
    rows.append(back_home_row())
    return InlineKeyboardMarkup(rows)


def pagination_row(has_prev, has_next, prev_data, next_data):
    row = []
    if has_prev:
        row.append(btn('⬅️', prev_data))
    if has_next:
        row.append(btn('➡️', next_data))
    return row


def autos_list_keyboard(autos, nav_prev=None, nav_next=None, back_data='m:back'):
    rows = []
    for auto in autos:
        label = f"{auto['brand']} {auto['model']} · {auto['year']} · {_price_short(auto['price'])}"
        if len(label) > 60:
            label = label[:57] + '…'
        rows.append([btn(label, f"m:auto:{auto['id']}")])
    nav = pagination_row(bool(nav_prev), bool(nav_next), nav_prev or 'x', nav_next or 'x')
    if nav:
        rows.append(nav)
    rows.append(back_home_row(back_data))
    return InlineKeyboardMarkup(rows)


def auto_detail_keyboard(auto_id):
    return InlineKeyboardMarkup([
        [btn('✉️ Написать продавцу', f'm:msg:{auto_id}')],
        back_home_row('m:back'),
    ])


def brands_keyboard(brands, prefix='m:brand'):
    rows = []
    row = []
    for brand in brands:
        row.append(btn(brand['name'], f"{prefix}:{brand['id']}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append(back_home_row())
    return InlineKeyboardMarkup(rows)


def regions_keyboard(regions):
    rows = []
    for region in regions:
        rows.append([btn(region['name'], f"m:flt:set_r:{region['id']}")])
    rows.append([btn('Пропустить', 'm:flt:skip_r')])
    rows.append(back_home_row('m:filter'))
    return InlineKeyboardMarkup(rows)


def inbox_keyboard(messages):
    rows = []
    for msg in messages:
        label = f"{msg['auto_title'][:30]} — {msg['sender']}"
        rows.append([btn(label, f"m:auto:{msg['auto_id']}")])
    rows.append(back_home_row())
    return InlineKeyboardMarkup(rows)


def _price_short(price):
    if price >= 1_000_000:
        return f"{price / 1_000_000:.1f} млн ₽".replace('.0 ', ' ')
    return f"{price:,} ₽".replace(',', ' ')
